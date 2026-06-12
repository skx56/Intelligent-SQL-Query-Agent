"""
Schema Agent - Extracts and retrieves relevant database schema information
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_agent import BaseAgent
from utils.database import DatabaseManager


class SchemaAgent(BaseAgent):
    """
    Extracts database schema information.
    
    Two modes:
    - Direct: Reads schema directly from database (for No-RAG pipeline)
    - RAG: Uses vector store for semantic schema retrieval
    """
    
    def __init__(self, use_rag: bool = False, vector_store=None):
        """
        Initialize Schema Agent.
        
        Args:
            use_rag: Whether to use RAG for schema retrieval
            vector_store: Vector store instance for RAG mode
        """
        super().__init__(
            name="Schema Agent",
            description="Extracts and retrieves database schema"
        )
        self.use_rag = use_rag
        self.vector_store = vector_store
        self._schema_cache: Dict[str, str] = {}
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract schema information for the current database.
        
        Args:
            state: Current pipeline state with 'db_path' key
            
        Returns:
            Updated state with 'schema', 'relevant_tables', 'foreign_keys'
        """
        db_path = state.get("db_path", "")
        question = state.get("question", "")
        plan = state.get("plan", {})
        
        if not db_path:
            state["errors"] = state.get("errors", []) + ["No database path provided"]
            return state
        
        self.log(f"Extracting schema from: {db_path}")
        
        try:
            if self.use_rag and self.vector_store:
                # RAG-based schema retrieval
                schema_info = self._rag_schema_retrieval(question, plan, db_path)
            else:
                # Direct schema extraction
                schema_info = self._direct_schema_extraction(db_path)
            
            state["schema"] = schema_info["schema_text"]
            state["relevant_tables"] = schema_info["tables"]
            state["foreign_keys"] = schema_info.get("foreign_keys", {})
            
            self.log(f"Found {len(schema_info['tables'])} relevant tables")
            
        except Exception as e:
            state["errors"] = state.get("errors", []) + [f"Schema extraction error: {str(e)}"]
            state["schema"] = ""
            state["relevant_tables"] = []
        
        return state
    
    def _direct_schema_extraction(self, db_path: str) -> Dict[str, Any]:
        """
        Extract complete schema directly from database.
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            Dictionary with schema information
        """
        # Check cache first
        if db_path in self._schema_cache:
            return {
                "schema_text": self._schema_cache[db_path]["schema_text"],
                "tables": self._schema_cache[db_path]["tables"],
                "foreign_keys": self._schema_cache[db_path]["foreign_keys"]
            }
        
        with DatabaseManager(db_path) as db:
            schema_text = db.get_schema_text()
            schema_dict = db.get_schema()
            foreign_keys = db.get_foreign_keys()
        
        result = {
            "schema_text": schema_text,
            "tables": list(schema_dict.keys()),
            "foreign_keys": foreign_keys
        }
        
        # Cache the result
        self._schema_cache[db_path] = result
        
        return result
    
    def _rag_schema_retrieval(
        self, 
        question: str, 
        plan: Dict[str, Any],
        db_path: str
    ) -> Dict[str, Any]:
        """
        Retrieve relevant schema using RAG.
        
        Args:
            question: User question
            plan: Query plan from planner
            db_path: Path to database
            
        Returns:
            Dictionary with relevant schema information
        """
        if not self.vector_store:
            self.log("No vector store available, falling back to direct extraction")
            return self._direct_schema_extraction(db_path)
        
        # Build search query from question and plan
        search_query = self._build_schema_search_query(question, plan)
        
        # Retrieve relevant schema chunks
        retrieved_docs = self.vector_store.similarity_search(search_query, k=5)
        
        # Extract schema text from retrieved documents
        schema_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Extract table names from retrieved content
        tables = self._extract_table_names(schema_text)
        
        # Get foreign keys for retrieved tables
        with DatabaseManager(db_path) as db:
            all_fks = db.get_foreign_keys()
            relevant_fks = {t: all_fks.get(t, []) for t in tables if t in all_fks}
        
        return {
            "schema_text": schema_text,
            "tables": tables,
            "foreign_keys": relevant_fks
        }
    
    def _build_schema_search_query(
        self, 
        question: str, 
        plan: Dict[str, Any]
    ) -> str:
        """
        Build optimized search query for schema retrieval.
        
        Args:
            question: User question
            plan: Query plan
            
        Returns:
            Search query string
        """
        # Start with the question
        query_parts = [question]
        
        # Add table hints from plan
        if "required_tables" in plan:
            query_parts.extend(plan["required_tables"])
        
        # Add column hints from plan
        if "required_columns" in plan:
            query_parts.extend(plan["required_columns"])
        
        return " ".join(query_parts)
    
    def _extract_table_names(self, schema_text: str) -> List[str]:
        """
        Extract table names from schema text.
        
        Args:
            schema_text: Schema text
            
        Returns:
            List of table names
        """
        import re
        
        # Match CREATE TABLE statements
        pattern = r"CREATE TABLE\s+(\w+)"
        matches = re.findall(pattern, schema_text, re.IGNORECASE)
        
        return list(set(matches))
    
    def get_table_sample(
        self, 
        db_path: str, 
        table: str, 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get sample data from a table.
        
        Args:
            db_path: Database path
            table: Table name
            limit: Number of rows
            
        Returns:
            List of sample rows
        """
        with DatabaseManager(db_path) as db:
            query = f"SELECT * FROM {table} LIMIT {limit}"
            return db.execute_query(query)
    
    def format_schema_for_llm(
        self, 
        schema_text: str, 
        foreign_keys: Dict[str, List[Dict]],
        include_samples: bool = False,
        db_path: Optional[str] = None
    ) -> str:
        """
        Format schema information for LLM context.
        
        Args:
            schema_text: Raw schema text
            foreign_keys: Foreign key relationships
            include_samples: Whether to include sample data
            db_path: Database path (needed for samples)
            
        Returns:
            Formatted schema string
        """
        lines = ["=== DATABASE SCHEMA ===", "", schema_text]
        
        if foreign_keys:
            lines.extend(["", "=== FOREIGN KEY RELATIONSHIPS ===", ""])
            for table, fks in foreign_keys.items():
                for fk in fks:
                    lines.append(
                        f"{table}.{fk['from_column']} -> "
                        f"{fk['to_table']}.{fk['to_column']}"
                    )
        
        if include_samples and db_path:
            lines.extend(["", "=== SAMPLE DATA ===", ""])
            tables = self._extract_table_names(schema_text)
            for table in tables[:3]:  # Limit to 3 tables
                try:
                    samples = self.get_table_sample(db_path, table, limit=2)
                    if samples:
                        lines.append(f"\n-- {table} --")
                        for row in samples:
                            lines.append(str(row))
                except Exception:
                    pass
        
        return "\n".join(lines)

