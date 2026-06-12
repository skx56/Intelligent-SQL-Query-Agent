"""
Spider Dataset Loader

Loads and processes Spider dataset for evaluation.
Spider: https://yale-lily.github.io/spider
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.progress import track

from config.config import SPIDER_DIR

console = Console()


@dataclass
class SpiderExample:
    """Single Spider dataset example."""
    question: str
    query: str  # Gold SQL
    db_id: str
    db_path: str
    query_type: str = ""
    hardness: str = ""  # easy, medium, hard, extra


class SpiderLoader:
    """
    Loads Spider dataset for evaluation.
    
    Spider dataset structure:
    - train_spider.json: Training examples
    - dev.json: Development/test examples
    - database/: SQLite databases
    - tables.json: Schema information
    """
    
    def __init__(self, spider_dir: Path = None):
        """
        Initialize Spider loader.
        
        Args:
            spider_dir: Path to Spider dataset directory
        """
        self.spider_dir = Path(spider_dir) if spider_dir else SPIDER_DIR
        self.databases_dir = self.spider_dir / "database"
        
        self._validate_structure()
    
    def _validate_structure(self):
        """Validate Spider directory structure."""
        if not self.spider_dir.exists():
            console.print(f"[yellow]Warning: Spider directory not found: {self.spider_dir}[/yellow]")
            console.print("[dim]Download from: https://yale-lily.github.io/spider[/dim]")
            return False
        
        required_files = ["train_spider.json", "dev.json", "tables.json"]
        missing = [f for f in required_files if not (self.spider_dir / f).exists()]
        
        if missing:
            console.print(f"[yellow]Warning: Missing files: {missing}[/yellow]")
            return False
        
        if not self.databases_dir.exists():
            console.print("[yellow]Warning: database/ directory not found[/yellow]")
            return False
        
        return True
    
    def load_train(self, limit: Optional[int] = None) -> List[SpiderExample]:
        """
        Load training examples.
        
        Args:
            limit: Maximum number of examples to load
            
        Returns:
            List of SpiderExample objects
        """
        return self._load_split("train_spider.json", limit)
    
    def load_dev(self, limit: Optional[int] = None) -> List[SpiderExample]:
        """
        Load development/test examples.
        
        Args:
            limit: Maximum number of examples to load
            
        Returns:
            List of SpiderExample objects
        """
        return self._load_split("dev.json", limit)
    
    def _load_split(self, filename: str, limit: Optional[int] = None) -> List[SpiderExample]:
        """Load a specific split of the dataset."""
        filepath = self.spider_dir / filename
        
        if not filepath.exists():
            console.print(f"[red]File not found: {filepath}[/red]")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        
        for item in data[:limit] if limit else data:
            db_id = item.get("db_id", "")
            db_path = self.databases_dir / db_id / f"{db_id}.sqlite"
            
            if not db_path.exists():
                continue
            
            example = SpiderExample(
                question=item.get("question", ""),
                query=item.get("query", ""),
                db_id=db_id,
                db_path=str(db_path),
                hardness=item.get("hardness", "unknown")
            )
            examples.append(example)
        
        console.print(f"[green]Loaded {len(examples)} examples from {filename}[/green]")
        return examples
    
    def load_tables(self) -> Dict[str, Dict]:
        """
        Load table schema information.
        
        Returns:
            Dictionary mapping db_id to schema info
        """
        filepath = self.spider_dir / "tables.json"
        
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            tables_data = json.load(f)
        
        return {db["db_id"]: db for db in tables_data}
    
    def get_database_path(self, db_id: str) -> Optional[Path]:
        """Get path to a specific database."""
        db_path = self.databases_dir / db_id / f"{db_id}.sqlite"
        return db_path if db_path.exists() else None
    
    def list_databases(self) -> List[str]:
        """List all available databases."""
        if not self.databases_dir.exists():
            return []
        
        databases = []
        for db_folder in self.databases_dir.iterdir():
            if db_folder.is_dir():
                db_file = db_folder / f"{db_folder.name}.sqlite"
                if db_file.exists():
                    databases.append(db_folder.name)
        
        return sorted(databases)
    
    def get_relevant_tables(self, query: str, db_id: str) -> List[str]:
        """
        Extract table names used in a SQL query.
        
        Args:
            query: SQL query string
            db_id: Database ID
            
        Returns:
            List of table names
        """
        import re
        
        tables_info = self.load_tables()
        db_info = tables_info.get(db_id, {})
        db_tables = [t.lower() for t in db_info.get("table_names_original", [])]
        
        # Find tables mentioned in query
        query_lower = query.lower()
        found_tables = []
        
        for table in db_tables:
            # Check for table name in FROM, JOIN clauses
            patterns = [
                rf'\bfrom\s+{table}\b',
                rf'\bjoin\s+{table}\b',
                rf'\b{table}\s+as\b',
                rf'\b{table}\.',
            ]
            
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    found_tables.append(table)
                    break
        
        return list(set(found_tables))
    
    def to_test_cases(
        self, 
        examples: List[SpiderExample],
        include_relevant_tables: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Convert Spider examples to test case format.
        
        Args:
            examples: List of SpiderExample objects
            include_relevant_tables: Whether to extract relevant tables
            
        Returns:
            List of test case dictionaries
        """
        test_cases = []
        
        for ex in examples:
            case = {
                "question": ex.question,
                "db_path": ex.db_path,
                "gold_sql": ex.query,
                "db_id": ex.db_id,
                "hardness": ex.hardness
            }
            
            if include_relevant_tables:
                case["relevant_tables"] = self.get_relevant_tables(
                    ex.query, ex.db_id
                )
            
            test_cases.append(case)
        
        return test_cases
    
    def sample_by_hardness(
        self, 
        examples: List[SpiderExample],
        easy: int = 10,
        medium: int = 10,
        hard: int = 10,
        extra: int = 5
    ) -> List[SpiderExample]:
        """
        Sample examples by difficulty level.
        
        Args:
            examples: Full list of examples
            easy/medium/hard/extra: Number of samples per difficulty
            
        Returns:
            Sampled examples
        """
        import random
        
        by_hardness = {
            "easy": [],
            "medium": [],
            "hard": [],
            "extra": []
        }
        
        for ex in examples:
            h = ex.hardness.lower()
            if h in by_hardness:
                by_hardness[h].append(ex)
        
        sampled = []
        limits = {"easy": easy, "medium": medium, "hard": hard, "extra": extra}
        
        for hardness, limit in limits.items():
            pool = by_hardness.get(hardness, [])
            sampled.extend(random.sample(pool, min(limit, len(pool))))
        
        return sampled


def create_evaluation_dataset(
    spider_dir: Path = None,
    split: str = "dev",
    sample_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Create evaluation dataset from Spider.
    
    Args:
        spider_dir: Spider directory path
        split: "train" or "dev"
        sample_size: Number of examples to sample
        
    Returns:
        List of test case dictionaries
    """
    loader = SpiderLoader(spider_dir)
    
    if split == "train":
        examples = loader.load_train()
    else:
        examples = loader.load_dev()
    
    if not examples:
        console.print("[red]No examples loaded. Check Spider dataset path.[/red]")
        return []
    
    # Sample balanced by difficulty
    sampled = loader.sample_by_hardness(
        examples,
        easy=sample_size // 4,
        medium=sample_size // 4,
        hard=sample_size // 4,
        extra=sample_size // 4
    )
    
    return loader.to_test_cases(sampled)


# Quick usage example
if __name__ == "__main__":
    loader = SpiderLoader()
    
    print("Available databases:")
    for db in loader.list_databases()[:10]:
        print(f"  - {db}")
    
    print("\nLoading dev set...")
    dev_examples = loader.load_dev(limit=5)
    
    for ex in dev_examples:
        print(f"\nQ: {ex.question}")
        print(f"SQL: {ex.query}")
        print(f"DB: {ex.db_id}")

