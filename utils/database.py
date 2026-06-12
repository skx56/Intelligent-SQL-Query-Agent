"""
Database utilities for SQLite operations with Spider dataset
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


class DatabaseManager:
    """
    Manages SQLite database connections and operations for Spider dataset.
    """
    
    def __init__(self, db_path: str | Path):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            fetch_all: Whether to fetch all results
            
        Returns:
            List of dictionaries containing query results
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                row = cursor.fetchone()
                return [dict(row)] if row else []
                
        except sqlite3.Error as e:
            raise RuntimeError(f"SQL execution error: {e}\nQuery: {query}")
        finally:
            cursor.close()
    
    def get_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract complete database schema.
        
        Returns:
            Dictionary with table names as keys and column info as values
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            schema[table] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default": col[4],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        
        cursor.close()
        return schema
    
    def get_schema_text(self) -> str:
        """
        Get schema as formatted text for LLM context.
        
        Returns:
            Formatted schema string
        """
        schema = self.get_schema()
        lines = []
        
        for table_name, columns in schema.items():
            col_defs = []
            for col in columns:
                pk = " PRIMARY KEY" if col["primary_key"] else ""
                nn = " NOT NULL" if col["not_null"] else ""
                col_defs.append(f"  {col['name']} {col['type']}{pk}{nn}")
            
            lines.append(f"CREATE TABLE {table_name} (")
            lines.append(",\n".join(col_defs))
            lines.append(");")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_foreign_keys(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract foreign key relationships.
        
        Returns:
            Dictionary mapping tables to their foreign key relationships
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        foreign_keys = {}
        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = cursor.fetchall()
            
            if fks:
                foreign_keys[table] = [
                    {
                        "from_column": fk[3],
                        "to_table": fk[2],
                        "to_column": fk[4]
                    }
                    for fk in fks
                ]
        
        cursor.close()
        return foreign_keys
    
    def get_sample_data(self, table: str, limit: int = 3) -> pd.DataFrame:
        """
        Get sample data from a table.
        
        Args:
            table: Table name
            limit: Number of rows to fetch
            
        Returns:
            DataFrame with sample data
        """
        query = f"SELECT * FROM {table} LIMIT {limit}"
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def display_results(self, results: List[Dict[str, Any]], title: str = "Query Results"):
        """
        Display query results in a formatted table.
        
        Args:
            results: Query results
            title: Table title
        """
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Add columns
        for key in results[0].keys():
            table.add_column(str(key))
        
        # Add rows (limit to 20 for display)
        for row in results[:20]:
            table.add_row(*[str(v) for v in row.values()])
        
        if len(results) > 20:
            console.print(f"[dim]Showing 20 of {len(results)} results[/dim]")
        
        console.print(table)


def get_spider_databases(spider_dir: Path) -> List[Path]:
    """
    Get all database paths from Spider dataset directory.
    
    Args:
        spider_dir: Path to Spider dataset directory
        
    Returns:
        List of database file paths
    """
    db_dir = spider_dir / "database"
    if not db_dir.exists():
        return []
    
    databases = []
    for db_folder in db_dir.iterdir():
        if db_folder.is_dir():
            db_file = db_folder / f"{db_folder.name}.sqlite"
            if db_file.exists():
                databases.append(db_file)
    
    return databases

