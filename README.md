# Intelligent SQL Query Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/LangGraph-Multi_Agent-green.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/FAISS-Vector_Store-orange.svg" alt="FAISS">
  <img src="https://img.shields.io/badge/Ollama-LLM-purple.svg" alt="Ollama">
  <img src="https://img.shields.io/badge/SQLglot-SQL_Processing-red.svg" alt="SQLglot">
</p>

## 🎯 Project Overview

**Intelligent SQL Query Agent** is an advanced AI-driven platform designed to translate natural language into highly accurate SQL queries. By leveraging a multi-agent architecture and specialized Retrieval-Augmented Generation (RAG) capabilities, the system accurately queries databases. We implement and evaluate three distinct execution pipelines:

| Pipeline Architecture | Description | Optimal Use Case |
|----------|-------------|----------|
| **Standalone Agent** | A simple, single-prompt approach for SQL translation. | Baseline metric comparisons |
| **Agent Swarm (No RAG)** | Orchestration of 5 distinct agents with direct schema visibility. | Complex reasoning without huge schemas |
| **Agent Swarm (with RAG)** | 5 distinct agents paired with semantic schema search. | Large-scale production databases |

### Core Capabilities

- 🤖 **5-Agent Swarm**: Including Planner, Schema, SQL generation, Executor, and Evaluator agents.
- 🔍 **Tri-fold RAG Mechanism**: Support for Dense (FAISS), Sparse (BM25), and Hybrid retrieval.
- 📊 **Robust Validation**: Granular performance and syntax evaluations, with interactive charts.
- 🌐 **Interactive Dashboard**: A sleek Streamlit GUI to explore the models.
- 📈 **Benchmark Ready**: Compatible with the Spider dataset and evaluating 5 default databases.

---

## 📊 Architectural Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
│         "How many countries have a republic government?"     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PLANNER AGENT                              │
│  • Interprets user intent                                    │
│  • Identifies the operational needs (SELECT, COUNT, etc.)   │
│  • Forecasts necessary tables                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   SCHEMA AGENT                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Dense     │  │    Sparse    │  │    Hybrid    │       │
│  │   (FAISS)    │  │    (BM25)    │  │   (Dense+    │       │
│  │              │  │              │  │    Sparse)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  Extracts context-aware schema definitions                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQL AGENT                                 │
│  • Ingests schema + plan + query                             │
│  • Constructs robust SQL via few-shot learning               │
│  • Post-processes output with SQLglot                        │
│  • Auto-recovers from syntax errors                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXECUTOR AGENT                              │
│  • Safely executes queries on the backend SQLite DB          │
│  • Guardrails against destructive ops (DROP, DELETE)         │
│  • Returns parsed data                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  EVALUATOR AGENT                             │
│  • Validates final outputs                                   │
│  • Measures syntax and semantic accuracy                     │
│  • Generates optimization feedback                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Schema Retrieval Approaches

### 1. Semantic (Dense) Retrieval
- Relies on sentence embeddings to grasp the context of schemas.
- Excellent for deep natural language understanding.
- Powered by `all-MiniLM-L6-v2`.

### 2. Lexical (Sparse) Retrieval
- Fast, BM25-based keyword matching.
- Ideal for exact column or table name lookups.

### 3. Hybrid Retrieval (Optimal)
- Merges the strengths of both semantic and lexical searches.
- Operates at a default 60/40 ratio (Dense/Sparse).
- Provides the highest accuracy in retrieving complex schema parts.

---

## 🛠️ Setup & Installation

### Requirements

```bash
# Verify Python version (3.9+)
python --version

# Set up Ollama (Local AI Runtime)
# Windows: Fetch from https://ollama.ai/download
# macOS/Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Fetch the core model
ollama pull llama3.2:3b
```

### Installation Steps

```bash
# 1. Fetch the repository
git clone https://github.com/sakshamojha56/Intelligent-SQL-Agent.git
cd Intelligent-SQL-Agent

# 2. Setup a virtual environment
python -m venv venv

# 3. Activate the environment
# On Windows (PowerShell):
.\venv\Scripts\Activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install required libraries
pip install -r requirements.txt
```

### Dataset Information
We use the Spider benchmark dataset located in `data/spider_data/`. 

---

## 🚀 Getting Started

### 1. Graphical Interface (Recommended)

```bash
streamlit run app.py
```

Access the interface at `http://localhost:8501`. Here you can:
- Swap between various sample databases (World, Concerts, Transcripts, Dogs, Cars).
- Experiment with different AI architectures (Standalone, Swarm, RAG Swarm).
- Run and visualize data outcomes.

### 2. CLI Execution

```bash
# Query the database using the RAG pipeline
python main.py --mode rag --question "How many countries are there?" --db "data/spider_data/spider_data/database/world_1/world_1.sqlite"

# Run a comparative test across all agent architectures
python main.py --compare --question "What countries became independent after 1950?" --db "data/spider_data/spider_data/database/world_1/world_1.sqlite"

# Start the interactive prompt
python main.py --interactive
```

### 3. Rigorous Evaluation

```bash
# Run a quick diagnostic test (25 samples)
python full_evaluation.py --limit 5

# Run the comprehensive benchmark suite (~3-4 hours)
python full_evaluation.py

# Evaluate a specific database only
python full_evaluation.py --db world_1
```

---

## 🔧 System Configuration

Modify settings in `config/config.py`:

```python
# Model selection
OLLAMA_MODEL = "llama3.2:3b"

# Retrieval specifications
RAG_TOP_K = 5 
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Weight distributions
DENSE_WEIGHT = 0.6
SPARSE_WEIGHT = 0.4

# Query generation bounds
SQL_MAX_RETRIES = 3
SQL_TEMPERATURE = 0.1
```

---

## 📈 System Metrics & Performance

Evaluations are captured across metrics like Execution Accuracy, Exact Set Matches, and execution valid rates. The Evaluator Agent additionally verifies structural compliance (SELECT, FROM, WHERE, GROUP BY, ORDER BY).

**Benchmark Insights (across 284 varied questions):**
- **Standalone:** ~48.6% accuracy (Often hallucinates JOINs)
- **Agent Swarm (No RAG):** ~53.2% accuracy (Strong structural syntax)
- **RAG Swarm:** ~60.6% accuracy (Peak performance)

---

## 🛡️ Core Technologies

- **LangGraph**: Used for crafting intelligent state machines and agent workflows.
- **FAISS & BM25**: Engine for dual-mode text retrieval.
- **Ollama**: Provider of local, robust LLM processing.
- **Sentence Transformers**: Vectorization of database schemas.
- **SQLglot**: Strict SQL syntax parsing and validation.
- **Streamlit**: Driving the frontend web experience.

---

## 📄 Licensing

This project is licensed under the MIT License. Refer to the [LICENSE](LICENSE) file.

---

## 🙏 Credits

- [Spider Dataset](https://yale-lily.github.io/spider) 
- [Ollama](https://ollama.ai/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FAISS](https://github.com/facebookresearch/faiss)
- [SQLglot](https://github.com/tobymao/sqlglot)
