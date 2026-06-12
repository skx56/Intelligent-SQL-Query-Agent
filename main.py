"""
Intelligent SQL Query Agent

Main entry point for running the Text-to-SQL pipeline with different approaches:
1. Single Agent (baseline)
2. Multi-Agent without RAG
3. Multi-Agent with RAG (LangGraph + FAISS)

Usage:
    python main.py --mode single --question "How many students?" --db path/to/db.sqlite
    python main.py --mode compare --question "..." --db path/to/db.sqlite
    python main.py --evaluate --test-file test_cases.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import OLLAMA_MODEL, SPIDER_DIR
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager, get_spider_databases
from pipelines import (
    SingleAgentPipeline,
    MultiAgentNoRAGPipeline,
    MultiAgentRAGPipeline
)
from evaluation import SchemaRetrievalComparison, PipelineEvaluator

console = Console()


def display_welcome():
    """Display welcome message."""
    console.print(Panel(
        """[bold cyan]Intelligent SQL Query Agent[/bold cyan]

[dim]Convert natural language questions to SQL queries using:
• Single Agent (baseline)
• Multi-Agent without RAG
• Multi-Agent with RAG (LangGraph + FAISS)

Features:
• Spider dataset support
• 3 retrieval methods (Dense, Sparse, Hybrid)
• Comprehensive evaluation and comparison[/dim]""",
        title="Welcome",
        border_style="cyan"
    ))


def run_single_query(
    question: str,
    db_path: str,
    mode: str = "single",
    retrieval_method: str = "hybrid",
    verbose: bool = True
):
    """
    Run a single query through the specified pipeline.
    
    Args:
        question: Natural language question
        db_path: Path to SQLite database
        mode: Pipeline mode (single, multi, rag)
        retrieval_method: For RAG mode (dense, sparse, hybrid)
        verbose: Show detailed output
    """
    llm = OllamaClient()
    
    if mode == "single":
        console.print("[cyan]Using Single Agent Pipeline[/cyan]")
        pipeline = SingleAgentPipeline(llm)
    elif mode == "multi":
        console.print("[cyan]Using Multi-Agent Pipeline (No RAG)[/cyan]")
        pipeline = MultiAgentNoRAGPipeline(llm)
    elif mode == "rag":
        console.print(f"[cyan]Using Multi-Agent RAG Pipeline ({retrieval_method})[/cyan]")
        pipeline = MultiAgentRAGPipeline(llm, retrieval_method=retrieval_method)
    else:
        console.print(f"[red]Unknown mode: {mode}[/red]")
        return
    
    pipeline.set_verbose(verbose)
    result = pipeline.run(question, db_path)
    
    if not verbose:
        # Display minimal result
        console.print("\n[bold]Generated SQL:[/bold]")
        console.print(result.get("sql", "No SQL generated"))
        
        if result.get("success") and result.get("result"):
            console.print(f"\n[bold]Results:[/bold] {len(result['result'])} rows")
            if len(result['result']) <= 5:
                for row in result['result']:
                    console.print(f"  {row}")
        
        if result.get("error"):
            console.print(f"\n[red]Error: {result['error']}[/red]")


def compare_pipelines(question: str, db_path: str):
    """
    Compare all pipeline approaches on a single question.
    
    Args:
        question: Natural language question
        db_path: Database path
    """
    console.print(Panel(
        f"[bold]Comparing pipelines for:[/bold]\n{question}",
        title="Pipeline Comparison"
    ))
    
    llm = OllamaClient()
    
    pipelines = {
        "Single Agent": SingleAgentPipeline(llm),
        "Multi-Agent (No RAG)": MultiAgentNoRAGPipeline(llm),
        "Multi-Agent RAG (Dense)": MultiAgentRAGPipeline(llm, "dense"),
        "Multi-Agent RAG (Sparse)": MultiAgentRAGPipeline(llm, "sparse"),
        "Multi-Agent RAG (Hybrid)": MultiAgentRAGPipeline(llm, "hybrid"),
    }
    
    results = {}
    
    for name, pipeline in pipelines.items():
        console.print(f"\n[dim]Running {name}...[/dim]")
        pipeline.set_verbose(False)
        result = pipeline.run(question, db_path)
        results[name] = result
    
    # Display comparison table
    table = Table(title="Pipeline Comparison Results")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Success", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("SQL (truncated)")
    
    for name, result in results.items():
        status = "[green]✓[/green]" if result.get("success") else "[red]✗[/red]"
        sql = result.get("sql", "")[:50] + "..." if len(result.get("sql", "")) > 50 else result.get("sql", "")
        
        table.add_row(
            name,
            status,
            f"{result.get('score', 0):.2f}",
            f"{result.get('execution_time', 0):.2f}",
            sql
        )
    
    console.print(table)


def compare_retrieval_methods(db_path: str, test_cases_path: Optional[str] = None):
    """
    Compare schema retrieval methods.
    
    Args:
        db_path: Database path
        test_cases_path: Optional path to test cases JSON
    """
    console.print(Panel(
        "[bold]Schema Retrieval Method Comparison[/bold]\n"
        "Comparing Dense (FAISS), Sparse (BM25), and Hybrid retrieval",
        title="Retrieval Analysis"
    ))
    
    # Load or create test cases
    if test_cases_path and Path(test_cases_path).exists():
        with open(test_cases_path) as f:
            test_cases = json.load(f)
    else:
        # Create sample test cases based on schema
        from evaluation.schema_retrieval_comparison import create_sample_test_cases
        test_cases = create_sample_test_cases()
    
    comparison = SchemaRetrievalComparison()
    results = comparison.run_comparison(db_path, test_cases)
    
    # Generate and display report
    report = comparison.generate_report(results)
    console.print(report)


def run_evaluation(test_file: str, output_dir: str = "results"):
    """
    Run full pipeline evaluation.
    
    Args:
        test_file: Path to test cases JSON
        output_dir: Directory for output files
    """
    console.print(Panel(
        "[bold]Full Pipeline Evaluation[/bold]",
        title="Evaluation"
    ))
    
    # Load test cases
    with open(test_file) as f:
        test_cases = json.load(f)
    
    console.print(f"Loaded {len(test_cases)} test cases")
    
    # Run evaluation
    evaluator = PipelineEvaluator()
    all_metrics = evaluator.run_full_comparison(test_cases)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    evaluator.save_results(str(output_path / "evaluation_results.json"))
    evaluator.generate_report(all_metrics, str(output_path / "evaluation_report.txt"))


def interactive_mode():
    """Run interactive query mode."""
    console.print(Panel(
        "[bold]Interactive Mode[/bold]\n"
        "Enter natural language questions to generate SQL.\n"
        "Type 'exit' to quit, 'help' for commands.",
        title="Interactive"
    ))
    
    db_path = None
    mode = "rag"
    llm = OllamaClient()
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]Question>[/bold cyan] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'help':
                console.print("""
Commands:
  exit       - Exit interactive mode
  help       - Show this help
  set db <path>  - Set database path
  set mode <single|multi|rag>  - Set pipeline mode
  list dbs   - List Spider databases
  show schema - Show current database schema
                """)
                continue
            
            if user_input.lower().startswith('set db '):
                db_path = user_input[7:].strip()
                console.print(f"[green]Database set to: {db_path}[/green]")
                continue
            
            if user_input.lower().startswith('set mode '):
                mode = user_input[9:].strip()
                console.print(f"[green]Mode set to: {mode}[/green]")
                continue
            
            if user_input.lower() == 'list dbs':
                dbs = get_spider_databases(SPIDER_DIR)
                if dbs:
                    for db in dbs[:10]:
                        console.print(f"  {db}")
                else:
                    console.print("[yellow]No Spider databases found[/yellow]")
                continue
            
            if user_input.lower() == 'show schema':
                if not db_path:
                    console.print("[red]Set database first: set db <path>[/red]")
                    continue
                with DatabaseManager(db_path) as db:
                    console.print(db.get_schema_text())
                continue
            
            # Process as question
            if not db_path:
                console.print("[red]Set database first: set db <path>[/red]")
                continue
            
            run_single_query(user_input, db_path, mode, verbose=True)
            
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Intelligent SQL Query Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --question "How many students?" --db school.sqlite
  python main.py --mode rag --retrieval hybrid --question "..." --db ...
  python main.py --compare --question "..." --db ...
  python main.py --interactive
  python main.py --evaluate --test-file test_cases.json
        """
    )
    
    parser.add_argument(
        "--question", "-q",
        help="Natural language question"
    )
    
    parser.add_argument(
        "--db",
        help="Path to SQLite database"
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["single", "multi", "rag"],
        default="rag",
        help="Pipeline mode (default: rag)"
    )
    
    parser.add_argument(
        "--retrieval", "-r",
        choices=["dense", "sparse", "hybrid"],
        default="hybrid",
        help="Retrieval method for RAG mode (default: hybrid)"
    )
    
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare all pipelines on the question"
    )
    
    parser.add_argument(
        "--compare-retrieval",
        action="store_true",
        help="Compare retrieval methods"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run interactive mode"
    )
    
    parser.add_argument(
        "--evaluate", "-e",
        action="store_true",
        help="Run full evaluation"
    )
    
    parser.add_argument(
        "--test-file",
        help="Path to test cases JSON for evaluation"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="results",
        help="Output directory for evaluation results"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    display_welcome()
    
    # Handle different modes
    if args.interactive:
        interactive_mode()
    
    elif args.evaluate:
        if not args.test_file:
            console.print("[red]--test-file required for evaluation[/red]")
            return
        run_evaluation(args.test_file, args.output_dir)
    
    elif args.compare and args.question and args.db:
        compare_pipelines(args.question, args.db)
    
    elif args.compare_retrieval and args.db:
        compare_retrieval_methods(args.db, args.test_file)
    
    elif args.question and args.db:
        run_single_query(
            args.question,
            args.db,
            args.mode,
            args.retrieval,
            args.verbose
        )
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

