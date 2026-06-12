"""
Executor Agent - Executes SQL queries on the database
"""

from typing import Any, Dict, List, Optional
import sqlite3

from .base_agent import BaseAgent
from utils.database import DatabaseManager


class ExecutorAgent(BaseAgent):
    """
    Executes SQL queries on SQLite database.
    
    Features:
    - Safe query execution
    - Result formatting
    - Error handling
    - Query type validation (for No-RAG: SELECT only)
    """
    
    def __init__(self, allow_modifications: bool = False):
        """
        Initialize Executor Agent.
        
        Args:
            allow_modifications: Whether to allow INSERT/UPDATE/DELETE
        """
        super().__init__(
            name="Executor Agent",
            description="Executes SQL queries on the database"
        )
        self.allow_modifications = allow_modifications
        
        # Allowed SQL commands
        self.read_only_commands = ['SELECT']
        self.modification_commands = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the generated SQL query.
        
        Args:
            state: Current pipeline state with 'generated_sql' and 'db_path'
            
        Returns:
            Updated state with 'execution_result', 'execution_success', 'execution_error'
        """
        sql = state.get("generated_sql", "")
        db_path = state.get("db_path", "")
        
        if not sql:
            state["execution_success"] = False
            state["execution_error"] = "No SQL query to execute"
            state["execution_result"] = None
            return state
        
        if not db_path:
            state["execution_success"] = False
            state["execution_error"] = "No database path provided"
            state["execution_result"] = None
            return state
        
        self.log(f"Executing SQL: {sql[:50]}...")
        
        # Validate query type
        validation = self._validate_query_type(sql)
        if not validation["allowed"]:
            state["execution_success"] = False
            state["execution_error"] = validation["error"]
            state["execution_result"] = None
            return state
        
        # Execute query
        try:
            result = self._execute_query(sql, db_path)
            state["execution_success"] = True
            state["execution_result"] = result
            state["execution_error"] = None
            self.log(f"Query executed successfully, {len(result)} rows returned")
            
        except sqlite3.Error as e:
            state["execution_success"] = False
            state["execution_error"] = f"SQLite error: {str(e)}"
            state["execution_result"] = None
            self.log(f"Execution failed: {e}")
            
        except Exception as e:
            state["execution_success"] = False
            state["execution_error"] = f"Execution error: {str(e)}"
            state["execution_result"] = None
            self.log(f"Unexpected error: {e}")
        
        return state
    
    def _validate_query_type(self, sql: str) -> Dict[str, Any]:
        """
        Validate if query type is allowed.
        
        Args:
            sql: SQL query
            
        Returns:
            Validation result
        """
        sql_upper = sql.strip().upper()
        
        # Check for read-only queries
        is_read_only = any(sql_upper.startswith(cmd) for cmd in self.read_only_commands)
        is_modification = any(sql_upper.startswith(cmd) for cmd in self.modification_commands)
        
        if is_read_only:
            return {"allowed": True, "error": None}
        
        if is_modification:
            if self.allow_modifications:
                return {"allowed": True, "error": None}
            else:
                return {
                    "allowed": False,
                    "error": "Modification queries (INSERT/UPDATE/DELETE) are not allowed in read-only mode"
                }
        
        return {"allowed": False, "error": f"Unknown query type: {sql[:20]}..."}
    
    def _execute_query(
        self, 
        sql: str, 
        db_path: str,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query
            db_path: Database path
            timeout: Query timeout in seconds
            
        Returns:
            List of result dictionaries
        """
        with DatabaseManager(db_path) as db:
            # Set timeout
            db.connection.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            
            # Execute query
            results = db.execute_query(sql)
            
            return results
    
    def execute_direct(
        self, 
        sql: str, 
        db_path: str
    ) -> Dict[str, Any]:
        """
        Direct query execution without state management.
        
        Args:
            sql: SQL query
            db_path: Database path
            
        Returns:
            Execution result
        """
        state = {
            "generated_sql": sql,
            "db_path": db_path
        }
        
        result = self.process(state)
        
        return {
            "success": result["execution_success"],
            "result": result["execution_result"],
            "error": result.get("execution_error")
        }
    
    def format_results(
        self, 
        results: List[Dict[str, Any]], 
        max_rows: int = 20,
        max_col_width: int = 50
    ) -> str:
        """
        Format query results for display.
        
        Args:
            results: Query results
            max_rows: Maximum rows to display
            max_col_width: Maximum column width
            
        Returns:
            Formatted string
        """
        if not results:
            return "No results returned."
        
        # Get columns
        columns = list(results[0].keys())
        
        # Calculate column widths
        widths = {}
        for col in columns:
            col_values = [str(row.get(col, ''))[:max_col_width] for row in results[:max_rows]]
            widths[col] = max(len(col), max(len(v) for v in col_values))
        
        # Build table
        lines = []
        
        # Header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for row in results[:max_rows]:
            row_str = " | ".join(
                str(row.get(col, ''))[:max_col_width].ljust(widths[col]) 
                for col in columns
            )
            lines.append(row_str)
        
        if len(results) > max_rows:
            lines.append(f"\n... and {len(results) - max_rows} more rows")
        
        lines.append(f"\nTotal: {len(results)} rows")
        
        return "\n".join(lines)
    
    def compare_results(
        self, 
        result1: List[Dict[str, Any]], 
        result2: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare two query results for evaluation.
        
        Args:
            result1: First result set
            result2: Second result set
            
        Returns:
            Comparison result
        """
        # Convert to comparable format
        def normalize(results):
            if not results:
                return set()
            return {tuple(sorted(row.items())) for row in results}
        
        set1 = normalize(result1)
        set2 = normalize(result2)
        
        exact_match = set1 == set2
        
        # Calculate overlap
        if set1 and set2:
            intersection = set1 & set2
            union = set1 | set2
            jaccard = len(intersection) / len(union) if union else 0
        else:
            jaccard = 1.0 if set1 == set2 else 0.0
        
        return {
            "exact_match": exact_match,
            "jaccard_similarity": jaccard,
            "result1_count": len(result1) if result1 else 0,
            "result2_count": len(result2) if result2 else 0
        }

