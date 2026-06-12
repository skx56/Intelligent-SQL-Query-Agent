"""
Different Schema Retrieval Methods for Comparison

Three approaches:
1. Dense Retrieval (FAISS + Sentence Embeddings)
2. Sparse Retrieval (BM25)
3. Hybrid Retrieval (Dense + Sparse with weighted fusion)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import re
from collections import Counter
import math

from rich.console import Console
from config.config import RAG_TOP_K

console = Console()


class BaseRetriever(ABC):
    """Abstract base class for retrievers."""
    
    def __init__(self, name: str):
        self.name = name
        self.documents: List[Dict[str, Any]] = []
    
    @abstractmethod
    def index(self, documents: List[Dict[str, Any]]):
        """Index documents for retrieval."""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, k: int = RAG_TOP_K) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for query."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "name": self.name,
            "num_documents": len(self.documents)
        }


class DenseRetriever(BaseRetriever):
    """
    Dense retrieval using FAISS and sentence embeddings.
    
    Uses semantic similarity between query and document embeddings.
    """
    
    def __init__(self, embedder=None):
        """
        Initialize dense retriever.
        
        Args:
            embedder: SchemaEmbedder instance
        """
        super().__init__("Dense Retrieval (FAISS)")
        self.embedder = embedder
        self.faiss_index = None
        self.embeddings = None
        
        # Lazy import faiss
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("Please install faiss-cpu: pip install faiss-cpu")
    
    def set_embedder(self, embedder):
        """Set the embedder after initialization."""
        self.embedder = embedder
    
    def index(self, documents: List[Dict[str, Any]]):
        """
        Index documents using FAISS.
        
        Args:
            documents: List of document dicts with 'content' key
        """
        if not self.embedder:
            raise ValueError("Embedder not set. Call set_embedder() first.")
        
        self.documents = documents
        texts = [doc.get("content", "") for doc in documents]
        
        # Generate embeddings
        console.print(f"[dim]Generating embeddings for {len(texts)} documents...[/dim]")
        self.embeddings = self.embedder.embed_texts(texts)
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normalized = self.embeddings / (norms + 1e-10)
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.faiss_index = self.faiss.IndexFlatIP(dimension)
        self.faiss_index.add(normalized.astype('float32'))
        
        console.print(f"[green]Indexed {len(documents)} documents for dense retrieval[/green]")
    
    def retrieve(self, query: str, k: int = RAG_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve documents using semantic similarity.
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with scores
        """
        if not self.faiss_index or not self.embedder:
            return []
        
        # Embed query
        query_embedding = self.embedder.embed_text(query)
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        query_norm = query_norm.reshape(1, -1).astype('float32')
        
        # Search
        scores, indices = self.faiss_index.search(query_norm, min(k, len(self.documents)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                doc = self.documents[idx].copy()
                doc['score'] = float(score)
                doc['retrieval_method'] = 'dense'
                results.append(doc)
        
        return results


class SparseRetriever(BaseRetriever):
    """
    Sparse retrieval using BM25 algorithm.
    
    Keyword-based retrieval that works well for exact matches.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.
        
        Args:
            k1: Term frequency saturation parameter
            b: Document length normalization parameter
        """
        super().__init__("Sparse Retrieval (BM25)")
        self.k1 = k1
        self.b = b
        
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self.term_freqs: List[Dict[str, int]] = []
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def index(self, documents: List[Dict[str, Any]]):
        """
        Index documents for BM25 retrieval.
        
        Args:
            documents: List of document dicts with 'content' key
        """
        self.documents = documents
        self.doc_freqs = {}
        self.doc_lengths = []
        self.term_freqs = []
        
        # Build index
        for doc in documents:
            text = doc.get("content", "")
            tokens = self._tokenize(text)
            
            self.doc_lengths.append(len(tokens))
            
            # Term frequency for this document
            tf = Counter(tokens)
            self.term_freqs.append(tf)
            
            # Document frequency
            for term in set(tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        console.print(f"[green]Indexed {len(documents)} documents for sparse retrieval[/green]")
    
    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Calculate BM25 score for a document."""
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freq = self.term_freqs[doc_idx]
        n_docs = len(self.documents)
        
        for term in query_tokens:
            if term not in term_freq:
                continue
            
            tf = term_freq[term]
            df = self.doc_freqs.get(term, 0)
            
            # IDF component
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
            
            # TF component with length normalization
            tf_norm = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            )
            
            score += idf * tf_norm
        
        return score
    
    def retrieve(self, query: str, k: int = RAG_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve documents using BM25 scoring.
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with scores
        """
        if not self.documents:
            return []
        
        query_tokens = self._tokenize(query)
        
        # Calculate scores for all documents
        scores = []
        for i in range(len(self.documents)):
            score = self._bm25_score(query_tokens, i)
            scores.append((i, score))
        
        # Sort by score and get top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:k]:
            if score > 0:
                doc = self.documents[idx].copy()
                doc['score'] = score
                doc['retrieval_method'] = 'sparse'
                results.append(doc)
        
        return results


class HybridRetriever(BaseRetriever):
    """
    Hybrid retrieval combining dense and sparse methods.
    
    Uses weighted fusion of dense (semantic) and sparse (keyword) scores.
    """
    
    def __init__(
        self, 
        embedder=None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            embedder: SchemaEmbedder instance
            dense_weight: Weight for dense retrieval scores
            sparse_weight: Weight for sparse retrieval scores
        """
        super().__init__("Hybrid Retrieval (Dense + Sparse)")
        self.dense_retriever = DenseRetriever(embedder)
        self.sparse_retriever = SparseRetriever()
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
    
    def set_embedder(self, embedder):
        """Set the embedder."""
        self.dense_retriever.set_embedder(embedder)
    
    def index(self, documents: List[Dict[str, Any]]):
        """
        Index documents for both retrieval methods.
        
        Args:
            documents: List of document dicts
        """
        self.documents = documents
        self.dense_retriever.index(documents)
        self.sparse_retriever.index(documents)
        
        console.print(f"[green]Indexed {len(documents)} documents for hybrid retrieval[/green]")
    
    def retrieve(self, query: str, k: int = RAG_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve documents using hybrid scoring.
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with combined scores
        """
        # Get results from both retrievers (get more than k for fusion)
        dense_results = self.dense_retriever.retrieve(query, k * 2)
        sparse_results = self.sparse_retriever.retrieve(query, k * 2)
        
        # Normalize scores
        dense_scores = self._normalize_scores(
            {self._doc_id(d): d['score'] for d in dense_results}
        )
        sparse_scores = self._normalize_scores(
            {self._doc_id(d): d['score'] for d in sparse_results}
        )
        
        # Combine scores
        all_doc_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        combined_scores = {}
        
        for doc_id in all_doc_ids:
            dense_score = dense_scores.get(doc_id, 0) * self.dense_weight
            sparse_score = sparse_scores.get(doc_id, 0) * self.sparse_weight
            combined_scores[doc_id] = dense_score + sparse_score
        
        # Sort and get top-k
        sorted_docs = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:k]
        
        # Build result documents
        doc_map = {self._doc_id(d): d for d in dense_results + sparse_results}
        
        results = []
        for doc_id, score in sorted_docs:
            if doc_id in doc_map:
                doc = doc_map[doc_id].copy()
                doc['score'] = score
                doc['dense_score'] = dense_scores.get(doc_id, 0)
                doc['sparse_score'] = sparse_scores.get(doc_id, 0)
                doc['retrieval_method'] = 'hybrid'
                results.append(doc)
        
        return results
    
    def _doc_id(self, doc: Dict[str, Any]) -> str:
        """Get unique identifier for document."""
        return doc.get('id', doc.get('content', '')[:50])
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0, 1] range using min-max normalization."""
        if not scores:
            return {}
        
        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return {k: 1.0 for k in scores}
        
        return {
            k: (v - min_val) / (max_val - min_val)
            for k, v in scores.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "name": self.name,
            "num_documents": len(self.documents),
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight
        }


def compare_retrievers(
    documents: List[Dict[str, Any]],
    queries: List[str],
    embedder,
    k: int = 5
) -> Dict[str, Any]:
    """
    Compare all three retrieval methods on given queries.
    
    Args:
        documents: Documents to index
        queries: Test queries
        embedder: SchemaEmbedder instance
        k: Number of results per query
        
    Returns:
        Comparison results
    """
    # Initialize retrievers
    dense = DenseRetriever(embedder)
    sparse = SparseRetriever()
    hybrid = HybridRetriever(embedder)
    
    # Index documents
    for retriever in [dense, sparse, hybrid]:
        retriever.index(documents)
    
    # Run queries and collect results
    results = {
        "dense": [],
        "sparse": [],
        "hybrid": []
    }
    
    for query in queries:
        results["dense"].append(dense.retrieve(query, k))
        results["sparse"].append(sparse.retrieve(query, k))
        results["hybrid"].append(hybrid.retrieve(query, k))
    
    # Calculate metrics
    metrics = {}
    for method, method_results in results.items():
        avg_score = np.mean([
            np.mean([d['score'] for d in r]) if r else 0
            for r in method_results
        ])
        avg_results = np.mean([len(r) for r in method_results])
        
        metrics[method] = {
            "avg_score": float(avg_score),
            "avg_results": float(avg_results)
        }
    
    return {
        "results": results,
        "metrics": metrics
    }

