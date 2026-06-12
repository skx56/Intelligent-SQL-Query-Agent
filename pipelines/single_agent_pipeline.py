"""
Single Agent Pipeline - Simple Text-to-SQL using one LLM call

This is the baseline approach where a single LLM call handles:
- Schema understanding
- SQL generation
- No explicit planning or evaluation
"""

from typing import Any, Dict, List, Optional
import time

from rich.console import Console
from rich.panel import Panel

from utils.llm_client import OllamaClient
from utils.database import DatabaseManager

console = Console()


class SingleAgentPipeline:
    """
    Single agent pipeline for Text-to-SQL.
    
    Simplest approach: one LLM call to generate SQL from question + schema.
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize single agent pipeline.
        
        Args:
            llm_client: Ollama client instance
        """
        self.llm = llm_client or OllamaClient()
        self.verbose = False
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output."""
        self.verbose = verbose
    
    def _create_prompt(self, question: str, schema: str) -> str:
        """Create the SQL generation prompt."""
        return f"""You are a SQL expert. Generate a SQLite query to answer the question.

Database Schema:
{schema}

Question: {question}

Requirements:
1. Output ONLY the SQL query, nothing else
2. Use valid SQLite syntax
3. End with semicolon
4. Use appropriate JOINs if needed

SQL:"""

    def run(
        self, 
        question: str, 
        db_path: str,
        execute: bool = True
    ) -> Dict[str, Any]:
        """
        Run the single agent pipeline.
        
        Args:
            question: Natural language question
            db_path: Path to SQLite database
            execute: Whether to execute the generated SQL
            
        Returns:
            Pipeline result dictionary
        """
        start_time = time.time()
        result = {
            "question": question,
            "db_path": db_path,
            "pipeline": "single_agent",
            "success": False,
            "sql": "",
            "result": None,
            "error": None,
            "execution_time": 0
        }
        
        try:
            # Step 1: Get schema
            if self.verbose:
                console.print("[dim]Extracting schema...[/dim]")
            
            with DatabaseManager(db_path) as db:
                schema = db.get_schema_text()
            
            # Step 2: Generate SQL
            if self.verbose:
                console.print("[dim]Generating SQL...[/dim]")
            
            prompt = self._create_prompt(question, schema)
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a SQL expert. Generate only the SQL query.",
                temperature=0.1
            )
            
            sql = self.llm.extract_sql(response)
            result["sql"] = sql
            
            # Step 3: Execute (optional)
            if execute and sql:
                if self.verbose:
                    console.print("[dim]Executing SQL...[/dim]")
                
                with DatabaseManager(db_path) as db:
                    query_result = db.execute_query(sql)
                    result["result"] = query_result
                    result["success"] = True
            else:
                result["success"] = bool(sql)
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        
        result["execution_time"] = time.time() - start_time
        
        if self.verbose:
            self._display_result(result)
        
        return result
    
    def _display_result(self, result: Dict[str, Any]):
        """Display pipeline result."""
        status = "[green]✓ Success[/green]" if result["success"] else "[red]✗ Failed[/red]"
        
        console.print(Panel(
            f"""[bold]Single Agent Pipeline Result[/bold]

{status}

[cyan]Question:[/cyan] {result['question']}

[cyan]Generated SQL:[/cyan]
{result['sql']}

[cyan]Execution Time:[/cyan] {result['execution_time']:.2f}s

[cyan]Result:[/cyan] {len(result['result']) if result['result'] else 0} rows""",
            title="Pipeline Output"
        ))
    
    def batch_run(
        self, 
        examples: List[Dict[str, str]],
        execute: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run pipeline on multiple examples.
        
        Args:
            examples: List of dicts with 'question' and 'db_path' keys
            execute: Whether to execute SQL
            
        Returns:
            List of results
        """
        results = []
        
        for i, example in enumerate(examples):
            if self.verbose:
                console.print(f"\n[bold]Example {i+1}/{len(examples)}[/bold]")
            
            result = self.run(
                question=example["question"],
                db_path=example["db_path"],
                execute=execute
            )
            results.append(result)
        
        return results
    
    def evaluate(
        self, 
        examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evaluate pipeline on examples with ground truth.
        
        Args:
            examples: List with 'question', 'db_path', and 'gold_sql' keys
            
        Returns:
            Evaluation metrics
        """
        correct = 0
        total = len(examples)
        execution_matches = 0
        
        for example in examples:
            result = self.run(
                question=example["question"],
                db_path=example["db_path"],
                execute=True
            )
            
            if result["success"] and "gold_sql" in example:
                # Execute gold SQL
                try:
                    with DatabaseManager(example["db_path"]) as db:
                        gold_result = db.execute_query(example["gold_sql"])
                    
                    # Compare results
                    if self._results_match(result["result"], gold_result):
                        execution_matches += 1
                        correct += 1
                except Exception:
                    pass
        
        return {
            "accuracy": correct / total if total > 0 else 0,
            "execution_match": execution_matches / total if total > 0 else 0,
            "total": total,
            "correct": correct
        }
    
    def _results_match(
        self, 
        result1: List[Dict], 
        result2: List[Dict]
    ) -> bool:
        """Check if two query results match."""
        if not result1 and not result2:
            return True
        if not result1 or not result2:
            return False
        if len(result1) != len(result2):
            return False
        
        # Sort and compare
        def normalize(results):
            return sorted([tuple(sorted(r.items())) for r in results])
        
        return normalize(result1) == normalize(result2)

