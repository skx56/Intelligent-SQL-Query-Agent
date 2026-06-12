"""
Pipeline Evaluation - Compares Single Agent, Multi-Agent No-RAG, and Multi-Agent RAG

Comprehensive evaluation across all three pipeline approaches.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

from pipelines import (
    SingleAgentPipeline,
    MultiAgentNoRAGPipeline,
    MultiAgentRAGPipeline
)
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager

console = Console()


@dataclass
class PipelineMetrics:
    """Metrics for a pipeline evaluation."""
    pipeline_name: str
    execution_accuracy: float
    sql_validity_rate: float
    avg_score: float
    avg_execution_time: float
    success_count: int
    total_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PipelineEvaluator:
    """
    Evaluates and compares all three pipeline approaches.
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize pipeline evaluator.
        
        Args:
            llm_client: Shared Ollama client
        """
        self.llm = llm_client or OllamaClient()
        
        # Initialize all pipelines
        self.pipelines = {
            "single_agent": SingleAgentPipeline(self.llm),
            "multi_agent_no_rag": MultiAgentNoRAGPipeline(self.llm),
            "multi_agent_rag_dense": MultiAgentRAGPipeline(self.llm, retrieval_method="dense"),
            "multi_agent_rag_sparse": MultiAgentRAGPipeline(self.llm, retrieval_method="sparse"),
            "multi_agent_rag_hybrid": MultiAgentRAGPipeline(self.llm, retrieval_method="hybrid"),
        }
        
        self.results: Dict[str, List[Dict]] = {}
    
    def evaluate_pipeline(
        self,
        pipeline_name: str,
        test_cases: List[Dict[str, Any]],
        verbose: bool = False
    ) -> PipelineMetrics:
        """
        Evaluate a single pipeline on test cases.
        
        Args:
            pipeline_name: Name of pipeline to evaluate
            test_cases: Test cases with 'question', 'db_path', optional 'gold_sql'
            verbose: Whether to show detailed output
            
        Returns:
            Pipeline metrics
        """
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")
        
        pipeline = self.pipelines[pipeline_name]
        pipeline.set_verbose(verbose)
        
        results = []
        
        for case in test_cases:
            question = case["question"]
            db_path = case["db_path"]
            gold_sql = case.get("gold_sql")
            
            start_time = time.time()
            
            # Run pipeline
            result = pipeline.run(question, db_path)
            
            execution_time = time.time() - start_time
            
            # Evaluate result
            sql_valid = bool(result.get("sql"))
            execution_success = result.get("success", False)
            
            # Compare with gold SQL if available
            execution_match = False
            if gold_sql and result.get("result") is not None:
                try:
                    with DatabaseManager(db_path) as db:
                        gold_result = db.execute_query(gold_sql)
                    execution_match = self._results_match(
                        result.get("result", []), 
                        gold_result
                    )
                except Exception:
                    pass
            
            results.append({
                "question": question,
                "generated_sql": result.get("sql", ""),
                "gold_sql": gold_sql,
                "sql_valid": sql_valid,
                "execution_success": execution_success,
                "execution_match": execution_match,
                "score": result.get("score", 0),
                "execution_time": execution_time
            })
        
        # Calculate metrics
        success_count = sum(1 for r in results if r["execution_success"])
        valid_count = sum(1 for r in results if r["sql_valid"])
        match_count = sum(1 for r in results if r["execution_match"])
        
        metrics = PipelineMetrics(
            pipeline_name=pipeline_name,
            execution_accuracy=match_count / len(results) if results else 0,
            sql_validity_rate=valid_count / len(results) if results else 0,
            avg_score=np.mean([r["score"] for r in results]) if results else 0,
            avg_execution_time=np.mean([r["execution_time"] for r in results]) if results else 0,
            success_count=success_count,
            total_count=len(results)
        )
        
        self.results[pipeline_name] = results
        
        return metrics
    
    def run_full_comparison(
        self,
        test_cases: List[Dict[str, Any]],
        pipelines_to_test: Optional[List[str]] = None,
        verbose: bool = True
    ) -> Dict[str, PipelineMetrics]:
        """
        Run comparison across all or selected pipelines.
        
        Args:
            test_cases: Test cases
            pipelines_to_test: Optional list of pipeline names
            verbose: Whether to show progress
            
        Returns:
            Metrics for each pipeline
        """
        if pipelines_to_test is None:
            pipelines_to_test = list(self.pipelines.keys())
        
        all_metrics = {}
        
        for pipeline_name in pipelines_to_test:
            if verbose:
                console.print(f"\n[bold cyan]Evaluating: {pipeline_name}[/bold cyan]")
            
            metrics = self.evaluate_pipeline(
                pipeline_name, 
                test_cases,
                verbose=False
            )
            all_metrics[pipeline_name] = metrics
        
        if verbose:
            self._display_comparison(all_metrics)
        
        return all_metrics
    
    def _results_match(
        self, 
        result1: List[Dict], 
        result2: List[Dict]
    ) -> bool:
        """Check if two query results match."""
        if not result1 and not result2:
            return True
        if not result1 or not result2:
            return False
        if len(result1) != len(result2):
            return False
        
        def normalize(results):
            return sorted([tuple(sorted(r.items())) for r in results])
        
        return normalize(result1) == normalize(result2)
    
    def _display_comparison(self, all_metrics: Dict[str, PipelineMetrics]):
        """Display comparison results."""
        table = Table(
            title="Pipeline Comparison Results",
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Pipeline", style="cyan")
        table.add_column("Exec Accuracy", justify="right")
        table.add_column("SQL Valid %", justify="right")
        table.add_column("Avg Score", justify="right")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Success", justify="right")
        
        display_names = {
            "single_agent": "Single Agent",
            "multi_agent_no_rag": "Multi-Agent (No RAG)",
            "multi_agent_rag_dense": "Multi-Agent RAG (Dense)",
            "multi_agent_rag_sparse": "Multi-Agent RAG (Sparse)",
            "multi_agent_rag_hybrid": "Multi-Agent RAG (Hybrid)"
        }
        
        for name, metrics in all_metrics.items():
            table.add_row(
                display_names.get(name, name),
                f"{metrics.execution_accuracy:.1%}",
                f"{metrics.sql_validity_rate:.1%}",
                f"{metrics.avg_score:.2f}",
                f"{metrics.avg_execution_time:.2f}",
                f"{metrics.success_count}/{metrics.total_count}"
            )
        
        console.print(table)
        
        # Find best
        best = max(all_metrics.items(), key=lambda x: x[1].execution_accuracy)
        fastest = min(all_metrics.items(), key=lambda x: x[1].avg_execution_time)
        
        console.print(Panel(
            f"[green]Best Accuracy: {display_names.get(best[0], best[0])} "
            f"({best[1].execution_accuracy:.1%})[/green]\n"
            f"[blue]Fastest: {display_names.get(fastest[0], fastest[0])} "
            f"({fastest[1].avg_execution_time:.2f}s)[/blue]",
            title="Summary"
        ))
    
    def generate_report(
        self,
        all_metrics: Dict[str, PipelineMetrics],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate detailed comparison report.
        
        Args:
            all_metrics: Metrics from run_full_comparison
            output_path: Optional path to save report
            
        Returns:
            Report string
        """
        lines = [
            "=" * 70,
            "MULTI-AGENT RAG ENHANCED TEXT-TO-SQL SYSTEM",
            "PIPELINE COMPARISON REPORT",
            "=" * 70,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 50,
            "",
            "This report compares three approaches to Text-to-SQL:",
            "1. Single Agent: Direct LLM call for SQL generation",
            "2. Multi-Agent No-RAG: 5 specialized agents, direct schema access",
            "3. Multi-Agent RAG: 5 agents with semantic schema retrieval",
            "",
            "DETAILED RESULTS",
            "-" * 50,
            ""
        ]
        
        for name, metrics in all_metrics.items():
            lines.extend([
                f"{name.upper().replace('_', ' ')}",
                f"  Execution Accuracy: {metrics.execution_accuracy:.2%}",
                f"  SQL Validity Rate:  {metrics.sql_validity_rate:.2%}",
                f"  Average Score:      {metrics.avg_score:.3f}",
                f"  Average Time:       {metrics.avg_execution_time:.2f}s",
                f"  Success Rate:       {metrics.success_count}/{metrics.total_count}",
                ""
            ])
        
        # Analysis
        lines.extend([
            "ANALYSIS",
            "-" * 50,
            ""
        ])
        
        # Compare approaches
        single = all_metrics.get("single_agent")
        multi_no_rag = all_metrics.get("multi_agent_no_rag")
        multi_rag = all_metrics.get("multi_agent_rag_hybrid")
        
        if single and multi_no_rag:
            improvement = (multi_no_rag.execution_accuracy - single.execution_accuracy) / (single.execution_accuracy + 0.001)
            lines.append(
                f"Multi-Agent vs Single Agent: "
                f"{'+' if improvement > 0 else ''}{improvement:.1%} accuracy improvement"
            )
        
        if multi_no_rag and multi_rag:
            improvement = (multi_rag.execution_accuracy - multi_no_rag.execution_accuracy) / (multi_no_rag.execution_accuracy + 0.001)
            lines.append(
                f"RAG vs No-RAG: "
                f"{'+' if improvement > 0 else ''}{improvement:.1%} accuracy improvement"
            )
        
        lines.extend([
            "",
            "CONCLUSIONS",
            "-" * 50,
            ""
        ])
        
        # Determine best approach
        best = max(all_metrics.items(), key=lambda x: x[1].execution_accuracy)
        
        if "rag_hybrid" in best[0]:
            lines.append(
                "The Hybrid RAG approach provides the best balance of accuracy "
                "by combining semantic and keyword-based schema retrieval."
            )
        elif "rag" in best[0]:
            lines.append(
                "RAG-enhanced retrieval significantly improves SQL generation "
                "by providing more relevant schema context."
            )
        elif "multi" in best[0]:
            lines.append(
                "Multi-agent decomposition improves accuracy by allowing "
                "specialized handling of each pipeline stage."
            )
        else:
            lines.append(
                "The single agent approach proves efficient for simple queries "
                "but may struggle with complex multi-table scenarios."
            )
        
        lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 50,
            "- For complex databases: Use Multi-Agent RAG (Hybrid)",
            "- For simple schemas: Multi-Agent No-RAG is sufficient",
            "- For quick prototyping: Single Agent provides baseline",
            "",
            "=" * 70
        ])
        
        report = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(report)
            console.print(f"[green]Report saved to {output_path}[/green]")
        
        return report
    
    def save_results(self, output_path: str):
        """Save all results to JSON."""
        output = {
            name: results 
            for name, results in self.results.items()
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        console.print(f"[green]Results saved to {output_path}[/green]")


def create_sample_test_cases(db_path: str) -> List[Dict[str, Any]]:
    """Create sample test cases for a database."""
    return [
        {
            "question": "How many records are in the main table?",
            "db_path": db_path
        },
        {
            "question": "List all unique values in the first column",
            "db_path": db_path
        },
        {
            "question": "What is the average of numeric values?",
            "db_path": db_path
        }
    ]

