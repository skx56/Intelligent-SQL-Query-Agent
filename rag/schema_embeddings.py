"""
Schema Embeddings - Creates vector embeddings for database schemas

Enhanced with:
- Example SQL patterns for few-shot retrieval
- Column value sampling for better matching
- Semantic descriptions for improved retrieval
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
from pathlib import Path

from rich.console import Console
from config.config import EMBEDDING_MODEL, EMBEDDING_DIMENSION

console = Console()


# Example SQL patterns for common query types - will be embedded for RAG
EXAMPLE_SQL_PATTERNS = {
    "count_all": {
        "description": "Count all records in a table",
        "pattern": "SELECT COUNT(*) FROM {table};",
        "keywords": ["how many", "count", "total number", "number of"]
    },
    "count_where": {
        "description": "Count records with a condition",
        "pattern": "SELECT COUNT(*) FROM {table} WHERE {condition};",
        "keywords": ["how many", "count", "with", "that have", "where"]
    },
    "sum_column": {
        "description": "Sum a numeric column",
        "pattern": "SELECT SUM({column}) FROM {table};",
        "keywords": ["total", "sum", "combined", "altogether"]
    },
    "average": {
        "description": "Calculate average of a column",
        "pattern": "SELECT AVG({column}) FROM {table};",
        "keywords": ["average", "mean", "avg"]
    },
    "max_min": {
        "description": "Find maximum or minimum value",
        "pattern": "SELECT MAX({column}) FROM {table}; / SELECT MIN({column}) FROM {table};",
        "keywords": ["maximum", "minimum", "highest", "lowest", "most", "least", "largest", "smallest"]
    },
    "select_where": {
        "description": "Select with condition",
        "pattern": "SELECT {columns} FROM {table} WHERE {condition};",
        "keywords": ["find", "get", "show", "list", "what are", "which"]
    },
    "join_tables": {
        "description": "Join two tables",
        "pattern": "SELECT {columns} FROM {table1} JOIN {table2} ON {table1}.{key} = {table2}.{key};",
        "keywords": ["from both", "related", "associated", "linked", "connected"]
    },
    "group_by": {
        "description": "Group and aggregate",
        "pattern": "SELECT {column}, COUNT(*) FROM {table} GROUP BY {column};",
        "keywords": ["for each", "per", "by", "grouped", "breakdown"]
    },
    "order_limit": {
        "description": "Order and limit results",
        "pattern": "SELECT {columns} FROM {table} ORDER BY {column} DESC LIMIT {n};",
        "keywords": ["top", "first", "highest", "best", "most"]
    }
}


class SchemaEmbedder:
    """
    Creates embeddings for database schema elements using sentence transformers.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the schema embedder.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            console.print(f"[green]Loaded embedding model: {self.model_name}[/green]")
        except ImportError:
            raise ImportError(
                "Please install sentence-transformers: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Create embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Create embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            
        Returns:
            Matrix of embeddings (n_texts x dimension)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        return embeddings
    
    def embed_schema(
        self, 
        schema_dict: Dict[str, List[Dict]],
        include_samples: bool = False,
        sample_data: Optional[Dict[str, List[Dict]]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Create embeddings for all schema elements.
        
        Args:
            schema_dict: Schema dictionary with tables and columns
            include_samples: Whether to include sample data in embeddings
            sample_data: Sample data for each table
            
        Returns:
            Dictionary mapping identifiers to embeddings
        """
        embeddings = {}
        texts = []
        identifiers = []
        
        for table_name, columns in schema_dict.items():
            # Table-level text
            col_names = ", ".join(c["name"] for c in columns)
            table_text = f"Table {table_name} contains columns: {col_names}"
            
            if include_samples and sample_data and table_name in sample_data:
                samples = sample_data[table_name]
                if samples:
                    sample_str = str(samples[0])
                    table_text += f". Example data: {sample_str[:200]}"
            
            texts.append(table_text)
            identifiers.append(f"table:{table_name}")
            
            # Column-level texts
            for col in columns:
                col_text = (
                    f"Column {col['name']} in table {table_name} "
                    f"has type {col['type']}"
                )
                if col.get("primary_key"):
                    col_text += " and is the primary key"
                
                texts.append(col_text)
                identifiers.append(f"column:{table_name}.{col['name']}")
        
        # Generate embeddings
        if texts:
            all_embeddings = self.embed_texts(texts)
            for identifier, embedding in zip(identifiers, all_embeddings):
                embeddings[identifier] = embedding
        
        return embeddings
    
    def embed_schema_for_store(
        self,
        schema_dict: Dict[str, List[Dict]],
        db_name: str,
        column_values: Optional[Dict[str, Dict[str, List]]] = None
    ) -> tuple:
        """
        Prepare schema embeddings for vector store with enhanced information.
        
        Args:
            schema_dict: Schema dictionary
            db_name: Database name
            column_values: Optional dict of {table: {column: [sample_values]}}
            
        Returns:
            Tuple of (documents, embeddings)
        """
        documents = []
        texts = []
        
        for table_name, columns in schema_dict.items():
            # Full table schema
            col_defs = []
            for col in columns:
                pk = " PRIMARY KEY" if col.get("primary_key") else ""
                not_null = " NOT NULL" if col.get("not_null") else ""
                col_defs.append(f"{col['name']} {col['type']}{pk}{not_null}")
            
            schema_text = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
            
            doc = {
                "id": f"{db_name}:{table_name}",
                "content": schema_text,
                "table": table_name,
                "db_name": db_name,
                "columns": [c["name"] for c in columns],
                "type": "table_schema"
            }
            
            documents.append(doc)
            texts.append(schema_text)
            
            # Semantic description for better retrieval
            col_desc = ", ".join(c["name"] for c in columns)
            desc_text = f"Table {table_name} with columns: {col_desc}"
            
            desc_doc = {
                "id": f"{db_name}:{table_name}:desc",
                "content": desc_text,
                "table": table_name,
                "db_name": db_name,
                "type": "table_description"
            }
            
            documents.append(desc_doc)
            texts.append(desc_text)
            
            # Add column value information if provided (helps with case sensitivity)
            if column_values and table_name in column_values:
                for col_name, values in column_values[table_name].items():
                    if values:
                        # Sample unique values (first 10)
                        unique_vals = list(set(str(v) for v in values if v is not None))[:10]
                        if unique_vals:
                            value_text = f"Column {table_name}.{col_name} has values like: {', '.join(unique_vals)}"
                            value_doc = {
                                "id": f"{db_name}:{table_name}:{col_name}:values",
                                "content": value_text,
                                "table": table_name,
                                "column": col_name,
                                "db_name": db_name,
                                "type": "column_values"
                            }
                            documents.append(value_doc)
                            texts.append(value_text)
        
        # Add SQL pattern examples for the database
        for pattern_name, pattern_info in EXAMPLE_SQL_PATTERNS.items():
            pattern_text = f"SQL Pattern: {pattern_info['description']}. Keywords: {', '.join(pattern_info['keywords'])}. Example: {pattern_info['pattern']}"
            pattern_doc = {
                "id": f"{db_name}:pattern:{pattern_name}",
                "content": pattern_text,
                "db_name": db_name,
                "type": "sql_pattern",
                "pattern_name": pattern_name
            }
            documents.append(pattern_doc)
            texts.append(pattern_text)
        
        # Generate embeddings
        embeddings = self.embed_texts(texts) if texts else np.array([])
        
        return documents, embeddings
    
    def get_column_sample_values(
        self,
        db_path: str,
        schema_dict: Dict[str, List[Dict]],
        sample_size: int = 20
    ) -> Dict[str, Dict[str, List]]:
        """
        Get sample values from columns for better RAG matching.
        
        Args:
            db_path: Path to SQLite database
            schema_dict: Schema dictionary
            sample_size: Number of sample values per column
            
        Returns:
            Dictionary of {table: {column: [values]}}
        """
        import sqlite3
        
        column_values = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for table_name, columns in schema_dict.items():
                column_values[table_name] = {}
                
                for col in columns:
                    col_name = col["name"]
                    col_type = col.get("type", "").upper()
                    
                    # Only sample text/varchar columns (useful for case sensitivity)
                    if any(t in col_type for t in ["TEXT", "VARCHAR", "CHAR"]):
                        try:
                            query = f'SELECT DISTINCT "{col_name}" FROM "{table_name}" LIMIT {sample_size}'
                            cursor.execute(query)
                            values = [row[0] for row in cursor.fetchall()]
                            column_values[table_name][col_name] = values
                        except Exception as e:
                            console.print(f"[dim]Could not sample {table_name}.{col_name}: {e}[/dim]")
            
            conn.close()
        except Exception as e:
            console.print(f"[yellow]Could not sample column values: {e}[/yellow]")
        
        return column_values
    
    def compute_similarity(
        self, 
        query_embedding: np.ndarray, 
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.
        
        Args:
            query_embedding: Query embedding
            doc_embeddings: Document embeddings matrix
            
        Returns:
            Similarity scores
        """
        # Normalize
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        doc_norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        docs_norm = doc_embeddings / (doc_norms + 1e-10)
        
        # Compute cosine similarity
        similarities = np.dot(docs_norm, query_norm)
        
        return similarities
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return EMBEDDING_DIMENSION


class SchemaChunker:
    """
    Chunks database schemas for optimal retrieval.
    """
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_schema(
        self, 
        schema_text: str, 
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split schema into chunks.
        
        Args:
            schema_text: Full schema text
            metadata: Additional metadata
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Split by table definitions
        tables = schema_text.split("CREATE TABLE")
        
        for i, table_def in enumerate(tables):
            if not table_def.strip():
                continue
            
            table_text = "CREATE TABLE" + table_def
            
            # If table definition is small enough, keep as single chunk
            if len(table_text) <= self.chunk_size:
                chunks.append({
                    "content": table_text.strip(),
                    "chunk_index": len(chunks),
                    "metadata": metadata or {}
                })
            else:
                # Split large table definitions
                sub_chunks = self._split_text(table_text)
                for sub_chunk in sub_chunks:
                    chunks.append({
                        "content": sub_chunk,
                        "chunk_index": len(chunks),
                        "metadata": metadata or {}
                    })
        
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at line boundary
            if end < len(text):
                newline_pos = text.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap
        
        return chunks

