"""
Configuration settings for the Intelligent SQL Query Agent
"""

import os
from pathlib import Path

# ============================================================
# Path Configurations
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SPIDER_DIR = DATA_DIR / "spider_data" / "spider_data"  # Adjusted for actual structure
VECTOR_STORE_DIR = DATA_DIR / "vector_stores"

# ============================================================
# LLM Configuration (Ollama)
# ============================================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")  # or codellama, mistral, etc.

# ============================================================
# Embedding Configuration
# ============================================================
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight and effective
EMBEDDING_DIMENSION = 384

# ============================================================
# RAG Configuration
# ============================================================
RAG_TOP_K = 5  # Number of schema chunks to retrieve
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50

# ============================================================
# Schema Retrieval Approaches
# ============================================================
SCHEMA_RETRIEVAL_APPROACHES = {
    "dense": {
        "name": "Dense Retrieval (FAISS)",
        "description": "Semantic similarity using sentence embeddings"
    },
    "sparse": {
        "name": "Sparse Retrieval (BM25)",
        "description": "Keyword-based retrieval using BM25 algorithm"
    },
    "hybrid": {
        "name": "Hybrid Retrieval",
        "description": "Combination of dense and sparse retrieval with weighted fusion"
    }
}

# ============================================================
# SQL Generation Settings
# ============================================================
SQL_MAX_RETRIES = 3
SQL_TEMPERATURE = 0.1  # Low temperature for deterministic SQL

# ============================================================
# Evaluation Settings
# ============================================================
EVALUATION_SAMPLE_SIZE = 100  # Number of samples for evaluation
EXACT_MATCH_WEIGHT = 0.4
EXECUTION_MATCH_WEIGHT = 0.6

# ============================================================
# Logging
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"

