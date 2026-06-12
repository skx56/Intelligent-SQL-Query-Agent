"""
3 Pipeline Comparison Analysis
"""
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.config import SPIDER_DIR
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from utils.sql_utils import compare_sql, get_query_type
from pipelines import SingleAgentPipeline, MultiAgentNoRAGPipeline, MultiAgentRAGPipeline

console = Console()


def run_analysis(db_id: str = "world_1", num_questions: int = 3):
    """Run analysis on multiple questions with all 3 pipelines"""
    
    # Load questions (easy only)
    dev_path = SPIDER_DIR / "dev.json"
    with open(dev_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter easy questions
    questions = []
    for d in data:
        if d['db_id'] == db_id:
            q = d['query'].upper()
            # Easy: no JOIN, no subquery
            if ' JOIN ' not in q and 'SELECT' not in q[q.find('FROM'):] if 'FROM' in q else True:
                questions.append(d)
    
    questions = questions[:num_questions]
    db_path = SPIDER_DIR / "database" / db_id / f"{db_id}.sqlite"
    
    console.print(Panel(
        f"[bold]Database:[/bold] {db_id}\n"
        f"[bold]Number of Questions:[/bold] {num_questions} (EASY only)",
        title="📊 3 Pipeline Analysis"
    ))
    
    # Initialize
    llm = OllamaClient()
    pipelines = {
        "Single": SingleAgentPipeline(llm),
        "Multi": MultiAgentNoRAGPipeline(llm),
        "RAG": MultiAgentRAGPipeline(llm, retrieval_method="hybrid")
    }
    
    results = []
    
    for i, q in enumerate(questions):
        console.print(f"\n[bold cyan]═══ Question {i+1}/{num_questions} ═══[/bold cyan]")
        console.print(f"[yellow]Q:[/yellow] {q['question']}")
        console.print(f"[dim]Gold: {q['query']}[/dim]")
        
        # Get gold result
        try:
            with DatabaseManager(str(db_path)) as db:
                gold_result = db.execute_query(q['query'])
                gold_values = [list(r.values()) for r in gold_result]
        except Exception as e:
            gold_values = None
            console.print(f"[red]Gold SQL error: {e}[/red]")
        
        row = {
            "question": q['question'][:50],
            "gold_sql": q['query'][:50]
        }
        
        for name, pipeline in pipelines.items():
            pipeline.set_verbose(False)
            result = pipeline.run(q['question'], str(db_path))
            
            gen_sql = result.get('sql', '')
            
            # SQL comparison
            if gen_sql:
                comparison = compare_sql(gen_sql, q['query'])
                
                # Execution match
                exec_match = False
                if result.get('result') and gold_values:
                    gen_values = [list(r.values()) for r in result['result']]
                    exec_match = gen_values == gold_values
                
                row[f"{name}_sql"] = gen_sql[:40]
                row[f"{name}_time"] = result.get('execution_time', 0)
                row[f"{name}_exec_match"] = exec_match
                row[f"{name}_semantic"] = comparison['semantic_similar']
            else:
                row[f"{name}_sql"] = "ERROR"
                row[f"{name}_time"] = 0
                row[f"{name}_exec_match"] = False
                row[f"{name}_semantic"] = False
        
        results.append(row)
    
    # Summary table
    console.print("\n")
    table = Table(title="📊 Pipeline Comparison Summary")
    table.add_column("Question", style="cyan", max_width=30)
    table.add_column("Single\nExec✓", justify="center")
    table.add_column("Single\nTime", justify="right")
    table.add_column("Multi\nExec✓", justify="center")
    table.add_column("Multi\nTime", justify="right")
    table.add_column("RAG\nExec✓", justify="center")
    table.add_column("RAG\nTime", justify="right")
    
    totals = {"Single": {"match": 0, "time": 0}, "Multi": {"match": 0, "time": 0}, "RAG": {"match": 0, "time": 0}}
    
    for row in results:
        q_short = row['question'][:28] + ".." if len(row['question']) > 30 else row['question']
        
        single_match = "✅" if row.get('Single_exec_match') else "❌"
        multi_match = "✅" if row.get('Multi_exec_match') else "❌"
        rag_match = "✅" if row.get('RAG_exec_match') else "❌"
        
        table.add_row(
            q_short,
            single_match, f"{row.get('Single_time', 0):.1f}s",
            multi_match, f"{row.get('Multi_time', 0):.1f}s",
            rag_match, f"{row.get('RAG_time', 0):.1f}s"
        )
        
        for name in ["Single", "Multi", "RAG"]:
            if row.get(f'{name}_exec_match'):
                totals[name]["match"] += 1
            totals[name]["time"] += row.get(f'{name}_time', 0)
    
    # Total row
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{totals['Single']['match']}/{num_questions}[/bold]", f"[bold]{totals['Single']['time']:.0f}s[/bold]",
        f"[bold]{totals['Multi']['match']}/{num_questions}[/bold]", f"[bold]{totals['Multi']['time']:.0f}s[/bold]",
        f"[bold]{totals['RAG']['match']}/{num_questions}[/bold]", f"[bold]{totals['RAG']['time']:.0f}s[/bold]"
    )
    
    console.print(table)
    
    # Conclusion
    best_accuracy = max(totals.items(), key=lambda x: x[1]["match"])
    fastest = min(totals.items(), key=lambda x: x[1]["time"])
    
    console.print(Panel(
        f"[green]Most Accurate:[/green] {best_accuracy[0]} ({best_accuracy[1]['match']}/{num_questions} correct)\n"
        f"[blue]Fastest:[/blue] {fastest[0]} ({fastest[1]['time']:.0f}s total)",
        title="🏆 Results"
    ))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="world_1")
    parser.add_argument("-n", type=int, default=3)
    args = parser.parse_args()
    
    run_analysis(args.db, args.n)

