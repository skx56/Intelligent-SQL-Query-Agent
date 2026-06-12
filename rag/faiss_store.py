"""
FAISS Vector Store for schema embeddings
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from rich.console import Console
from config.config import VECTOR_STORE_DIR, RAG_TOP_K

console = Console()


class FAISSVectorStore:
    """
    FAISS-based vector store for schema embeddings.
    
    Supports:
    - Adding documents with embeddings
    - Similarity search
    - Persistence to disk
    """
    
    def __init__(self, dimension: int = 384, store_name: str = "schema_store"):
        """
        Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension
            store_name: Name for persistence
        """
        self.dimension = dimension
        self.store_name = store_name
        self.store_path = VECTOR_STORE_DIR / store_name
        
        # Lazy import faiss
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("Please install faiss-cpu: pip install faiss-cpu")
        
        # Initialize index
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Document storage
        self.documents: List[Dict[str, Any]] = []
        self.id_to_idx: Dict[str, int] = {}
        
        # Ensure store directory exists
        self.store_path.mkdir(parents=True, exist_ok=True)
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: np.ndarray
    ):
        """
        Add documents with their embeddings.
        
        Args:
            documents: List of document dictionaries
            embeddings: Numpy array of embeddings (n_docs x dimension)
        """
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-10)
        
        # Add to index
        start_idx = len(self.documents)
        self.index.add(normalized.astype('float32'))
        
        # Store documents
        for i, doc in enumerate(documents):
            doc_id = doc.get('id', f"doc_{start_idx + i}")
            self.id_to_idx[doc_id] = start_idx + i
            self.documents.append(doc)
        
        console.print(f"[green]Added {len(documents)} documents to vector store[/green]")
    
    def similarity_search(
        self,
        query_embedding: np.ndarray,
        k: int = RAG_TOP_K,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching documents with scores
        """
        if self.index.ntotal == 0:
            return []
        
        # Normalize query
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        query_norm = query_norm.reshape(1, -1).astype('float32')
        
        # Search
        scores, indices = self.index.search(query_norm, min(k, self.index.ntotal))
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score >= threshold:
                doc = self.documents[idx].copy()
                doc['score'] = float(score)
                results.append(doc)
        
        return results
    
    def search_by_text(
        self,
        query: str,
        embedder,
        k: int = RAG_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Search using text query.
        
        Args:
            query: Text query
            embedder: Embedder instance
            k: Number of results
            
        Returns:
            List of matching documents
        """
        query_embedding = embedder.embed_text(query)
        return self.similarity_search(query_embedding, k)
    
    def save(self):
        """Save vector store to disk."""
        # Save FAISS index
        index_path = self.store_path / "index.faiss"
        self.faiss.write_index(self.index, str(index_path))
        
        # Save documents
        docs_path = self.store_path / "documents.pkl"
        with open(docs_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'id_to_idx': self.id_to_idx
            }, f)
        
        # Save metadata
        meta_path = self.store_path / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump({
                'dimension': self.dimension,
                'num_documents': len(self.documents),
                'store_name': self.store_name
            }, f)
        
        console.print(f"[green]Vector store saved to {self.store_path}[/green]")
    
    def load(self) -> bool:
        """
        Load vector store from disk.
        
        Returns:
            True if loaded successfully
        """
        index_path = self.store_path / "index.faiss"
        docs_path = self.store_path / "documents.pkl"
        
        if not index_path.exists() or not docs_path.exists():
            return False
        
        try:
            # Load FAISS index
            self.index = self.faiss.read_index(str(index_path))
            
            # Load documents
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.id_to_idx = data['id_to_idx']
            
            console.print(f"[green]Loaded {len(self.documents)} documents from {self.store_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error loading vector store: {e}[/red]")
            return False
    
    def clear(self):
        """Clear all documents from the store."""
        self.index = self.faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.id_to_idx = {}
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        idx = self.id_to_idx.get(doc_id)
        if idx is not None:
            return self.documents[idx]
        return None
    
    def __len__(self) -> int:
        return len(self.documents)


class Document:
    """Simple document class for compatibility with LangChain-style interfaces."""
    
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Document(content='{self.page_content[:50]}...', metadata={self.metadata})"


def create_documents_from_schema(
    schema_dict: Dict[str, List[Dict]],
    db_name: str
) -> List[Document]:
    """
    Create document chunks from database schema.
    
    Args:
        schema_dict: Schema dictionary with tables and columns
        db_name: Database name
        
    Returns:
        List of Document objects
    """
    documents = []
    
    for table_name, columns in schema_dict.items():
        # Create table-level document
        col_defs = []
        for col in columns:
            pk = " PRIMARY KEY" if col.get("primary_key") else ""
            col_defs.append(f"  {col['name']} {col['type']}{pk}")
        
        table_schema = f"CREATE TABLE {table_name} (\n" + ",\n".join(col_defs) + "\n);"
        
        doc = Document(
            page_content=table_schema,
            metadata={
                "table": table_name,
                "db_name": db_name,
                "type": "table_schema",
                "columns": [c["name"] for c in columns]
            }
        )
        documents.append(doc)
        
        # Create column-level documents for better granularity
        for col in columns:
            col_doc = Document(
                page_content=f"Table: {table_name}, Column: {col['name']}, Type: {col['type']}",
                metadata={
                    "table": table_name,
                    "column": col["name"],
                    "db_name": db_name,
                    "type": "column_info"
                }
            )
            documents.append(col_doc)
    
    return documents

