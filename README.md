# Intelligent SQL Query Agent

<p align="center">
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge" />
  <img alt="LangChain" src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge" />
  <img alt="FAISS" src="https://img.shields.io/badge/FAISS-2B6CB0?style=for-the-badge" />
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge" />
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-374151?style=for-the-badge" />
  <img alt="Machine Learning" src="https://img.shields.io/badge/Machine%20Learning-102230?style=for-the-badge" />
</p>

<p align="center">
  <strong>A multi-agent natural-language-to-SQL system with schema retrieval, execution checks, and evaluation pipelines.</strong>
</p>

The Intelligent SQL Query Agent translates natural language into database queries through a structured planning, schema retrieval, SQL generation, execution, and evaluation workflow. It is built for accuracy, traceability, and side-by-side comparison of single-agent, multi-agent, and retrieval-enhanced pipelines.

## Core Capabilities

- Retrieves relevant schema context using vector search.
- Separates planning, schema understanding, SQL generation, execution, and evaluation into distinct modules.
- Benchmarks multiple query-generation pipeline strategies.
- Includes Streamlit and analysis scripts for result inspection.

## Technical Architecture

The repository is organized around agent modules, RAG utilities, pipeline variants, evaluation scripts, and example entry points. FAISS-backed schema embeddings provide retrieval context while SQLAlchemy and sqlglot support database and SQL handling.

## Architecture Diagram

```mermaid
flowchart TD
  Question["Natural Language Question"] --> Planner["Planner Agent"]
  Planner --> Schema["Schema Agent"]
  Schema --> RAG["FAISS Schema Retrieval"]
  RAG --> SQLAgent["SQL Generation Agent"]
  SQLAgent --> Executor["Execution Agent"]
  Executor --> Database["SQL Database"]
  Executor --> Evaluator["Evaluator Agent"]
  Evaluator --> Answer["Validated Query and Result"]

  classDef inputs fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D,stroke-width:2px;
  classDef process fill:#ECFCCB,stroke:#65A30D,color:#365314,stroke-width:2px;
  classDef data fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A,stroke-width:2px;
  classDef agent fill:#FAE8FF,stroke:#C026D3,color:#701A75,stroke-width:2px;
  classDef output fill:#DCFCE7,stroke:#16A34A,color:#14532D,stroke-width:2px;
  class Question,Planner,Database inputs;
  class Schema,RAG,Executor,Evaluator process;
  class SQLAgent agent;
  class Answer output;
  linkStyle default stroke:#52525B,stroke-width:2px;
```

## Technology Stack

- LangChain and LangGraph for orchestration patterns.
- FAISS and sentence-transformers for schema retrieval.
- SQLAlchemy and sqlglot for database and query workflows.
- Streamlit and Plotly for interactive analysis.
- Rich, tqdm, and evaluation scripts for developer-facing diagnostics.

## Repository Structure

- `agents` - Planner, schema, SQL, executor, and evaluator modules.
- `rag` - Schema embeddings and retrieval methods.
- `pipelines` - Single-agent, multi-agent, and RAG-enhanced pipelines.
- `evaluation` - Evaluation workflows.
- `app.py` - Interactive application entry point.
- `full_evaluation.py` - Full benchmark runner.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
python main.py
streamlit run app.py
```

## Professional Context

This project demonstrates applied retrieval, structured reasoning, SQL execution safety, and evaluation-driven system design.
