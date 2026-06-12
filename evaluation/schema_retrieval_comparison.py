"""
Schema Retrieval Comparison Analysis

Compares three different schema retrieval approaches:
1. Dense Retrieval (FAISS + Sentence Embeddings)
2. Sparse Retrieval (BM25)
3. Hybrid Retrieval (Dense + Sparse weighted fusion)

Metrics:
- Retrieval Accuracy (relevant tables retrieved)
- Retrieval Time
- SQL Generation Success Rate
- End-to-end Execution Accuracy
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

from rag.schema_embeddings import SchemaEmbedder
from rag.retrieval_methods import DenseRetriever, SparseRetriever, HybridRetriever
from utils.database import DatabaseManager
from utils.llm_client import OllamaClient
from config.config import RAG_TOP_K

console = Console()


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval evaluation."""
    method: str
    precision: float
    recall: float
    f1_score: float
    retrieval_time: float
    num_retrieved: int
    relevant_retrieved: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EndToEndMetrics:
    """End-to-end pipeline metrics."""
    method: str
    execution_accuracy: float
    sql_validity: float
    avg_retrieval_time: float
    avg_total_time: float
    success_count: int
    total_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SchemaRetrievalComparison:
    """
    Compares different schema retrieval methods.
    
    Evaluates on:
    - Table relevance (precision/recall)
    - SQL generation quality
    - End-to-end execution accuracy
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize comparison framework.
        
        Args:
            llm_client: Ollama client for SQL generation
        """
        self.llm = llm_client or OllamaClient()
        self.embedder = SchemaEmbedder()
        
        # Initialize all retrievers
        self.retrievers = {
            "dense": DenseRetriever(self.embedder),
            "sparse": SparseRetriever(),
            "hybrid": HybridRetriever(self.embedder)
        }
        
        self.results: Dict[str, List[Dict]] = {
            "dense": [],
            "sparse": [],
            "hybrid": []
        }
    
    def prepare_test_data(
        self, 
        db_path: str,
        test_questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prepare test data with ground truth tables.
        
        Args:
            db_path: Path to database
            test_questions: List of questions with expected tables
            
        Returns:
            Prepared test data
        """
        # Extract schema
        with DatabaseManager(db_path) as db:
            schema_dict = db.get_schema()
            db_name = Path(db_path).stem
        
        # Create documents for indexing
        documents, _ = self.embedder.embed_schema_for_store(schema_dict, db_name)
        doc_dicts = [
            {"content": d["content"], "id": d["id"], "table": d["table"]}
            for d in documents
        ]
        
        # Index in all retrievers
        for retriever in self.retrievers.values():
            retriever.index(doc_dicts)
        
        return test_questions
    
    def evaluate_retrieval(
        self,
        question: str,
        relevant_tables: List[str],
        k: int = RAG_TOP_K
    ) -> Dict[str, RetrievalMetrics]:
        """
        Evaluate retrieval for a single question.
        
        Args:
            question: Test question
            relevant_tables: Ground truth relevant tables
            k: Number of documents to retrieve
            
        Returns:
            Metrics for each retrieval method
        """
        results = {}
        relevant_set = set(t.lower() for t in relevant_tables)
        
        for method, retriever in self.retrievers.items():
            start_time = time.time()
            retrieved = retriever.retrieve(question, k)
            retrieval_time = time.time() - start_time
            
            # Extract retrieved tables
            retrieved_tables = set(
                d.get("table", "").lower() 
                for d in retrieved 
                if d.get("table")
            )
            
            # Calculate metrics
            if relevant_set:
                relevant_retrieved = len(retrieved_tables & relevant_set)
                precision = relevant_retrieved / len(retrieved_tables) if retrieved_tables else 0
                recall = relevant_retrieved / len(relevant_set)
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            else:
                precision = recall = f1 = 0
                relevant_retrieved = 0
            
            results[method] = RetrievalMetrics(
                method=method,
                precision=precision,
                recall=recall,
                f1_score=f1,
                retrieval_time=retrieval_time,
                num_retrieved=len(retrieved),
                relevant_retrieved=relevant_retrieved
            )
        
        return results
    
    def run_comparison(
        self,
        db_path: str,
        test_cases: List[Dict[str, Any]],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run full comparison across all retrieval methods.
        
        Args:
            db_path: Path to database
            test_cases: Test cases with 'question' and 'relevant_tables'
            verbose: Whether to show progress
            
        Returns:
            Comparison results
        """
        # Prepare data
        self.prepare_test_data(db_path, test_cases)
        
        all_results = {
            "dense": {"metrics": [], "times": []},
            "sparse": {"metrics": [], "times": []},
            "hybrid": {"metrics": [], "times": []}
        }
        
        # Run evaluations
        iterator = track(test_cases, description="Evaluating...") if verbose else test_cases
        
        for case in iterator:
            question = case["question"]
            relevant_tables = case.get("relevant_tables", [])
            
            metrics = self.evaluate_retrieval(question, relevant_tables)
            
            for method, metric in metrics.items():
                all_results[method]["metrics"].append(metric)
                all_results[method]["times"].append(metric.retrieval_time)
        
        # Aggregate results
        summary = {}
        for method in ["dense", "sparse", "hybrid"]:
            metrics = all_results[method]["metrics"]
            
            summary[method] = {
                "avg_precision": np.mean([m.precision for m in metrics]),
                "avg_recall": np.mean([m.recall for m in metrics]),
                "avg_f1": np.mean([m.f1_score for m in metrics]),
                "avg_time": np.mean(all_results[method]["times"]),
                "std_time": np.std(all_results[method]["times"]),
                "total_cases": len(metrics)
            }
        
        if verbose:
            self._display_comparison(summary)
        
        return {
            "summary": summary,
            "detailed_results": all_results
        }
    
    def _display_comparison(self, summary: Dict[str, Dict]):
        """Display comparison results in a table."""
        table = Table(
            title="Schema Retrieval Method Comparison",
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Method", style="cyan")
        table.add_column("Precision", justify="right")
        table.add_column("Recall", justify="right")
        table.add_column("F1 Score", justify="right")
        table.add_column("Avg Time (ms)", justify="right")
        
        method_names = {
            "dense": "Dense (FAISS)",
            "sparse": "Sparse (BM25)",
            "hybrid": "Hybrid"
        }
        
        for method, metrics in summary.items():
            table.add_row(
                method_names.get(method, method),
                f"{metrics['avg_precision']:.3f}",
                f"{metrics['avg_recall']:.3f}",
                f"{metrics['avg_f1']:.3f}",
                f"{metrics['avg_time']*1000:.2f}"
            )
        
        console.print(table)
        
        # Find best method
        best_method = max(summary.items(), key=lambda x: x[1]['avg_f1'])
        console.print(Panel(
            f"[green]Best Method: {method_names.get(best_method[0], best_method[0])} "
            f"(F1 Score: {best_method[1]['avg_f1']:.3f})[/green]",
            title="Recommendation"
        ))
    
    def analyze_by_query_type(
        self,
        db_path: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Dict]:
        """
        Analyze retrieval performance by query type.
        
        Args:
            db_path: Database path
            test_cases: Test cases with 'query_type' field
            
        Returns:
            Results grouped by query type
        """
        # Group by query type
        by_type = {}
        for case in test_cases:
            qtype = case.get("query_type", "unknown")
            if qtype not in by_type:
                by_type[qtype] = []
            by_type[qtype].append(case)
        
        results = {}
        for qtype, cases in by_type.items():
            console.print(f"\n[bold]Query Type: {qtype}[/bold]")
            comparison = self.run_comparison(db_path, cases, verbose=False)
            results[qtype] = comparison["summary"]
        
        return results
    
    def generate_report(
        self,
        comparison_results: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a detailed comparison report.
        
        Args:
            comparison_results: Results from run_comparison
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        summary = comparison_results.get("summary", {})
        
        report_lines = [
            "=" * 60,
            "SCHEMA RETRIEVAL COMPARISON REPORT",
            "=" * 60,
            "",
            "METHODOLOGY",
            "-" * 40,
            "Three retrieval approaches were compared:",
            "",
            "1. DENSE RETRIEVAL (FAISS + Sentence Embeddings)",
            "   - Uses semantic similarity between query and schema",
            "   - Captures meaning beyond keyword matching",
            "   - Best for: Natural language understanding",
            "",
            "2. SPARSE RETRIEVAL (BM25)",
            "   - Keyword-based retrieval algorithm",
            "   - Efficient for exact term matching",
            "   - Best for: Technical queries with specific terms",
            "",
            "3. HYBRID RETRIEVAL",
            "   - Combines dense and sparse with weighted fusion",
            "   - Balances semantic understanding and keyword matching",
            "   - Best for: General purpose use",
            "",
            "RESULTS",
            "-" * 40,
            ""
        ]
        
        for method, metrics in summary.items():
            report_lines.extend([
                f"{method.upper()} RETRIEVAL:",
                f"  Precision: {metrics['avg_precision']:.4f}",
                f"  Recall:    {metrics['avg_recall']:.4f}",
                f"  F1 Score:  {metrics['avg_f1']:.4f}",
                f"  Avg Time:  {metrics['avg_time']*1000:.2f}ms",
                ""
            ])
        
        # Recommendations
        best_f1 = max(summary.items(), key=lambda x: x[1]['avg_f1'])
        fastest = min(summary.items(), key=lambda x: x[1]['avg_time'])
        
        report_lines.extend([
            "RECOMMENDATIONS",
            "-" * 40,
            f"Best Accuracy: {best_f1[0].upper()} (F1: {best_f1[1]['avg_f1']:.4f})",
            f"Fastest:       {fastest[0].upper()} ({fastest[1]['avg_time']*1000:.2f}ms)",
            "",
            "CONCLUSION",
            "-" * 40,
        ])
        
        if best_f1[0] == "hybrid":
            report_lines.append(
                "Hybrid retrieval provides the best balance of accuracy and coverage."
            )
        elif best_f1[0] == "dense":
            report_lines.append(
                "Dense retrieval excels at semantic understanding of questions."
            )
        else:
            report_lines.append(
                "Sparse retrieval is effective for keyword-heavy technical queries."
            )
        
        report = "\n".join(report_lines)
        
        if output_path:
            Path(output_path).write_text(report)
            console.print(f"[green]Report saved to {output_path}[/green]")
        
        return report
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save results to JSON file."""
        # Convert numpy types to Python types
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            if isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            if isinstance(obj, RetrievalMetrics):
                return obj.to_dict()
            return obj
        
        # Deep convert
        def deep_convert(d):
            if isinstance(d, dict):
                return {k: deep_convert(v) for k, v in d.items()}
            if isinstance(d, list):
                return [deep_convert(i) for i in d]
            return convert(d)
        
        converted = deep_convert(results)
        
        with open(output_path, 'w') as f:
            json.dump(converted, f, indent=2)
        
        console.print(f"[green]Results saved to {output_path}[/green]")


def create_sample_test_cases() -> List[Dict[str, Any]]:
    """Create sample test cases for evaluation."""
    return [
        {
            "question": "How many students are enrolled in each course?",
            "relevant_tables": ["students", "enrollments", "courses"],
            "query_type": "AGGREGATE"
        },
        {
            "question": "List all professors and their departments",
            "relevant_tables": ["professors", "departments"],
            "query_type": "JOIN"
        },
        {
            "question": "What is the average grade for each student?",
            "relevant_tables": ["students", "grades"],
            "query_type": "AGGREGATE"
        },
        {
            "question": "Find courses with more than 50 students",
            "relevant_tables": ["courses", "enrollments"],
            "query_type": "FILTER"
        },
        {
            "question": "Show the top 5 highest-paid employees",
            "relevant_tables": ["employees"],
            "query_type": "ORDERBY"
        },
        {
            "question": "Count the number of orders per customer",
            "relevant_tables": ["orders", "customers"],
            "query_type": "COUNT"
        },
        {
            "question": "List products and their categories",
            "relevant_tables": ["products", "categories"],
            "query_type": "SELECT"
        },
        {
            "question": "Find employees who work in the IT department",
            "relevant_tables": ["employees", "departments"],
            "query_type": "FILTER"
        }
    ]

