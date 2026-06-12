"""
Demo Script - Test on a single database

Loads questions for a specific database from Spider dev.json
and compares 3 pipelines.
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from config.config import SPIDER_DIR
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from utils.sql_utils import compare_sql, normalize_sql, full_evaluation, exact_set_match, component_matching
from pipelines import SingleAgentPipeline, MultiAgentNoRAGPipeline, MultiAgentRAGPipeline

console = Console()


def estimate_hardness(query):
    """Estimate difficulty from SQL query"""
    q = query.upper()
    join_count = q.count(' JOIN ')
    has_subquery = 'SELECT' in q[q.find('FROM'):] if 'FROM' in q else False
    has_group = 'GROUP BY' in q
    has_having = 'HAVING' in q
    has_union = 'UNION' in q or 'INTERSECT' in q or 'EXCEPT' in q
    
    if has_union or has_subquery or join_count >= 2 or has_having:
        return 'hard'
    elif join_count == 1 or has_group:
        return 'medium'
    else:
        return 'easy'


def load_questions(db_id: str, limit: int = None, exclude_hard: bool = False):
    """Load questions for a specific database from dev.json
    
    Args:
        db_id: Database ID
        limit: Max number of questions
        exclude_hard: If True, only return easy and medium questions
    """
    dev_path = SPIDER_DIR / "dev.json"
    
    with open(dev_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = [d for d in data if d['db_id'] == db_id]
    
    # Filter by hardness if requested
    if exclude_hard:
        questions = [q for q in questions if estimate_hardness(q['query']) in ['easy', 'medium']]
    
    # Add hardness info
    for q in questions:
        q['hardness'] = estimate_hardness(q['query'])
    
    if limit:
        questions = questions[:limit]
    
    return questions


def show_questions(db_id: str, exclude_hard: bool = False):
    """Display all questions for a database"""
    questions = load_questions(db_id, exclude_hard=exclude_hard)
    
    filter_text = " (Easy+Medium only)" if exclude_hard else ""
    console.print(f"\n[bold cyan]{db_id} Database - {len(questions)} Questions{filter_text}[/bold cyan]\n")
    
    for i, q in enumerate(questions[:15], 1):
        hardness = q.get('hardness', '?')
        color = {'easy': 'green', 'medium': 'yellow', 'hard': 'red'}.get(hardness, 'white')
        console.print(f"[yellow]{i}.[/yellow] [{color}][{hardness.upper()}][/{color}] {q['question']}")
        console.print(f"   [dim]SQL: {q['query'][:70]}...[/dim]\n" if len(q['query']) > 70 else f"   [dim]SQL: {q['query']}[/dim]\n")


def run_single_demo(db_id: str, question_idx: int = 0, mode: str = "single"):
    """Run a single question through specified pipeline"""
    questions = load_questions(db_id)
    q = questions[question_idx]
    
    db_path = SPIDER_DIR / "database" / db_id / f"{db_id}.sqlite"
    
    console.print(Panel(
        f"[bold]Question:[/bold] {q['question']}\n"
        f"[bold]Gold SQL:[/bold] {q['query']}",
        title=f"Test #{question_idx + 1}"
    ))
    
    llm = OllamaClient()
    
    if mode == "single":
        pipeline = SingleAgentPipeline(llm)
    elif mode == "multi":
        pipeline = MultiAgentNoRAGPipeline(llm)
    else:
        pipeline = MultiAgentRAGPipeline(llm, retrieval_method="hybrid")
    
    pipeline.set_verbose(True)
    result = pipeline.run(q['question'], str(db_path))
    
    # Compare with gold
    console.print(f"\n[bold]Generated SQL:[/bold] {result.get('sql', 'N/A')}")
    console.print(f"[bold]Gold SQL:[/bold] {q['query']}")
    
    gen_sql = result.get('sql', '')
    gold_sql = q['query']
    
    if gen_sql:
        # Full evaluation with all metrics
        eval_result = full_evaluation(gen_sql, gold_sql, str(db_path))
        
        # 1. Execution Accuracy
        exec_acc = eval_result["execution_accuracy"]
        console.print(f"\n[bold]━━━ 1. Execution Accuracy ━━━[/bold]")
        console.print(f"  SQL Valid (executed without errors): [{'green' if exec_acc['valid'] else 'red'}]{exec_acc['valid']}[/]")
        console.print(f"  Result Correct (result is correct): [{'green' if exec_acc['correct'] else 'red'}]{exec_acc['correct']}[/]")
        if exec_acc.get('gen_result'):
            gen_preview = str(exec_acc['gen_result'][:2])[:60]
            gold_preview = str(exec_acc['gold_result'][:2])[:60]
            console.print(f"  Generated Result: {gen_preview}...")
            console.print(f"  Gold Result:      {gold_preview}...")
        if exec_acc.get('error'):
            console.print(f"  [red]Error: {exec_acc['error']}[/red]")
        
        # 2. Component Matching
        comp = eval_result["component_matching"]
        console.print(f"\n[bold]━━━ 2. Component Matching ━━━[/bold]")
        console.print(f"  SELECT (aggregates): [{'green' if comp['select_match'] else 'red'}]{comp['select_match']}[/]")
        console.print(f"  FROM (tables):       [{'green' if comp['from_match'] else 'red'}]{comp['from_match']}[/]")
        console.print(f"  WHERE (conditions):  [{'green' if comp['where_match'] else 'red'}]{comp['where_match']}[/]")
        console.print(f"  GROUP BY:            [{'green' if comp['groupby_match'] else 'yellow'}]{comp['groupby_match']}[/]")
        console.print(f"  [bold]Overall Score: {comp['overall_score']:.0%}[/bold]")
        
        # 3. Exact Set Match
        if exec_acc.get('gen_result') and exec_acc.get('gold_result'):
            set_match = exact_set_match(exec_acc['gen_result'], exec_acc['gold_result'])
            console.print(f"\n[bold]━━━ 3. Exact Set Match ━━━[/bold]")
            console.print(f"  Set Match (order independent): [{'green' if set_match else 'red'}]{set_match}[/]")
        
        # Summary
        summary = eval_result["summary"]
        console.print(f"\n[bold]━━━ SUMMARY ━━━[/bold]")
        total_score = (
            (1 if summary['execution_correct'] else 0) * 0.5 +
            summary['component_score'] * 0.3 +
            (1 if summary['semantic_similar'] else 0) * 0.2
        )
        console.print(f"  [bold cyan]Final Score: {total_score:.0%}[/bold cyan]")
    
    return result


def run_comparison(db_id: str, num_questions: int = 5, exclude_hard: bool = False):
    """Compare all pipelines on multiple questions"""
    questions = load_questions(db_id, limit=num_questions, exclude_hard=exclude_hard)
    db_path = SPIDER_DIR / "database" / db_id / f"{db_id}.sqlite"
    
    console.print(Panel(
        f"[bold]Database:[/bold] {db_id}\n"
        f"[bold]Number of Questions:[/bold] {num_questions}\n"
        f"[bold]Pipelines:[/bold] Single Agent, Multi-Agent (No RAG), Multi-Agent (RAG)",
        title="Comparison Test"
    ))
    
    llm = OllamaClient()
    
    pipelines = {
        "Single Agent": SingleAgentPipeline(llm),
        "Multi-Agent": MultiAgentNoRAGPipeline(llm),
        "Multi-Agent RAG": MultiAgentRAGPipeline(llm, retrieval_method="hybrid")
    }
    
    results = {name: {"success": 0, "match": 0, "total_time": 0} for name in pipelines}
    
    for i, q in enumerate(track(questions, description="Testing...")):
        console.print(f"\n[bold]Q{i+1}:[/bold] {q['question'][:60]}...")
        
        # Get gold result
        try:
            with DatabaseManager(str(db_path)) as db:
                gold_result = db.execute_query(q['query'])
        except:
            gold_result = None
        
        for name, pipeline in pipelines.items():
            pipeline.set_verbose(False)
            result = pipeline.run(q['question'], str(db_path))
            
            results[name]["total_time"] += result.get("execution_time", 0)
            
            if result.get("success"):
                results[name]["success"] += 1
                
                if gold_result and result.get("result") == gold_result:
                    results[name]["match"] += 1
    
    # Display results
    table = Table(title="Pipeline Comparison Results")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Success", justify="center")
    table.add_column("Exact Match", justify="center")
    table.add_column("Avg Time", justify="right")
    
    for name, stats in results.items():
        table.add_row(
            name,
            f"{stats['success']}/{num_questions}",
            f"{stats['match']}/{num_questions}",
            f"{stats['total_time']/num_questions:.1f}s"
        )
    
    console.print(table)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Spider Demo")
    parser.add_argument("--db", default="world_1", help="Database ID (default: world_1)")
    parser.add_argument("--list", action="store_true", help="List questions")
    parser.add_argument("--test", type=int, default=None, help="Test question index")
    parser.add_argument("--mode", choices=["single", "multi", "rag"], default="single")
    parser.add_argument("--compare", type=int, default=None, help="Compare pipelines on N questions")
    parser.add_argument("--easy", action="store_true", help="Only use easy and medium questions (exclude hard)")
    
    args = parser.parse_args()
    
    if args.list:
        show_questions(args.db, exclude_hard=args.easy)
    elif args.test is not None:
        run_single_demo(args.db, args.test, args.mode)
    elif args.compare:
        run_comparison(args.db, args.compare, exclude_hard=args.easy)
    else:
        # Default: show questions
        show_questions(args.db, exclude_hard=args.easy)
        console.print("\n[dim]Usage:[/dim]")
        console.print("  python run_demo.py --list                    # List questions")
        console.print("  python run_demo.py --list --easy             # Only easy+medium")
        console.print("  python run_demo.py --test 0                  # Test first question")
        console.print("  python run_demo.py --test 0 --mode rag       # Test with RAG")
        console.print("  python run_demo.py --compare 5               # Compare 5 questions")
        console.print("  python run_demo.py --compare 5 --easy        # Compare 5 easy questions")
        console.print("  python run_demo.py --db world_1 --list --easy # Different DB")


if __name__ == "__main__":
    main()

