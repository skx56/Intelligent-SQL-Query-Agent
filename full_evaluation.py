"""
Full Evaluation Script - All Available Databases in Spider Dataset

Output Structure:
results/
├── world_1/
│   ├── detailed_results.json      - Detailed results for each question
│   ├── summary_metrics.json       - Summary metrics
│   ├── evaluation_report.html     - HTML report
│   ├── evaluation_report.csv      - Results in CSV format
│   ├── evaluation_report.md       - Markdown report
│   └── charts/                    - Charts
├── concert_singer/
│   └── ... (same structure)
├── student_transcripts_tracking/
│   └── ... (same structure)
... (all other databases)
└── combined/
    ├── all_databases_comparison.html   - All DB comparison
    ├── all_databases_comparison.csv    - CSV comparison
    ├── combined_summary.json           - Combined summary
    └── charts/                         - Comparison charts
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import csv

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track, Progress, SpinnerColumn, TextColumn

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from config.config import SPIDER_DIR
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from utils.sql_utils import full_evaluation, exact_set_match, component_matching
from pipelines import SingleAgentPipeline, MultiAgentNoRAGPipeline, MultiAgentRAGPipeline

console = Console()

# Results directory
RESULTS_DIR = Path("results")

# Get all available databases from Spider dataset
def get_all_databases() -> List[str]:
    """Get all available databases from Spider dataset directory."""
    db_dir = SPIDER_DIR / "database"
    if not db_dir.exists():
        return []
    
    databases = []
    for db_folder in db_dir.iterdir():
        if db_folder.is_dir():
            db_file = db_folder / f"{db_folder.name}.sqlite"
            if db_file.exists():
                databases.append(db_folder.name)
    
    return sorted(databases)

# Selected databases for evaluation (big/representative databases with more tables)
FEATURED_DATABASES = [
    "student_transcripts_tracking",   # 11 tables
    "concert_singer",                 # 4 tables
    "world_1",                        # 4 tables
    "dog_kennels",                    # 8 tables
    "car_1",                          # 6 tables
]


def estimate_hardness(query: str) -> str:
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


def load_all_questions(db_id: str, exclude_hard: bool = True) -> List[Dict]:
    """Load all questions for a database from Spider dev.json"""
    dev_path = SPIDER_DIR / "dev.json"
    
    with open(dev_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = []
    for d in data:
        if d['db_id'] == db_id:
            hardness = estimate_hardness(d['query'])
            if exclude_hard and hardness == 'hard':
                continue
            d['hardness'] = hardness
            questions.append(d)
    
    return questions


def run_single_db_evaluation(
    db_id: str,
    exclude_hard: bool = True,
    limit: int = None,
    llm: OllamaClient = None
) -> Tuple[List[Dict], Dict]:
    """
    Run evaluation for a single database.
    
    Returns:
        (detailed_results, summary_metrics)
    """
    # Load questions
    questions = load_all_questions(db_id, exclude_hard)
    if limit:
        questions = questions[:limit]
    
    db_path = SPIDER_DIR / "database" / db_id / f"{db_id}.sqlite"
    
    console.print(Panel(
        f"[bold]Database: {db_id}[/bold]\n"
        f"Questions: {len(questions)}\n"
        f"Exclude Hard: {exclude_hard}",
        title=f"🗄️ Evaluating {db_id}"
    ))
    
    # Initialize pipelines
    if llm is None:
        llm = OllamaClient()
    
    pipelines = {
        "Single_Agent": SingleAgentPipeline(llm),
        "Multi_Agent": MultiAgentNoRAGPipeline(llm),
        "Multi_Agent_RAG": MultiAgentRAGPipeline(llm, retrieval_method="hybrid")
    }
    
    # Set all to non-verbose
    for p in pipelines.values():
        p.set_verbose(False)
    
    # Results storage
    detailed_results = []
    metrics = {name: {
        "total": 0,
        "execution_valid": 0,
        "execution_correct": 0,
        "exact_set_match": 0,
        "component_score_sum": 0,
        "select_match": 0,
        "from_match": 0,
        "where_match": 0,
        "groupby_match": 0,
        "orderby_match": 0,
        "total_time": 0,
        "by_hardness": {"easy": {"total": 0, "correct": 0}, "medium": {"total": 0, "correct": 0}}
    } for name in pipelines.keys()}
    
    # Run evaluation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"[{db_id}] Evaluating {len(questions)} questions...", total=len(questions))
        
        for i, q in enumerate(questions):
            question_result = {
                "id": i + 1,
                "question": q["question"],
                "gold_sql": q["query"],
                "hardness": q["hardness"],
                "db_id": db_id,
                "pipelines": {}
            }
            
            progress.update(task, description=f"[{db_id}] Q{i+1}/{len(questions)}: {q['question'][:40]}...")
            
            for name, pipeline in pipelines.items():
                try:
                    # Run pipeline
                    result = pipeline.run(q["question"], str(db_path))
                    gen_sql = result.get("sql", "")
                    
                    # Full evaluation
                    if gen_sql:
                        eval_result = full_evaluation(gen_sql, q["query"], str(db_path))
                        
                        pipeline_result = {
                            "generated_sql": gen_sql,
                            "execution_time": result.get("execution_time", 0),
                            "execution_valid": eval_result["execution_accuracy"]["valid"],
                            "execution_correct": eval_result["execution_accuracy"]["correct"],
                            "exact_set_match": exact_set_match(
                                eval_result["execution_accuracy"].get("gen_result", []),
                                eval_result["execution_accuracy"].get("gold_result", [])
                            ) if eval_result["execution_accuracy"]["valid"] else False,
                            "component_score": eval_result["component_matching"]["overall_score"],
                            "select_match": eval_result["component_matching"]["select_match"],
                            "from_match": eval_result["component_matching"]["from_match"],
                            "where_match": eval_result["component_matching"]["where_match"],
                            "groupby_match": eval_result["component_matching"]["groupby_match"],
                            "orderby_match": eval_result["component_matching"]["orderby_match"],
                            "error": eval_result["execution_accuracy"].get("error")
                        }
                    else:
                        pipeline_result = {
                            "generated_sql": "",
                            "execution_time": result.get("execution_time", 0),
                            "execution_valid": False,
                            "execution_correct": False,
                            "exact_set_match": False,
                            "component_score": 0,
                            "select_match": False,
                            "from_match": False,
                            "where_match": False,
                            "groupby_match": False,
                            "orderby_match": False,
                            "error": "No SQL generated"
                        }
                    
                    question_result["pipelines"][name] = pipeline_result
                    
                    # Update metrics
                    m = metrics[name]
                    m["total"] += 1
                    m["execution_valid"] += 1 if pipeline_result["execution_valid"] else 0
                    m["execution_correct"] += 1 if pipeline_result["execution_correct"] else 0
                    m["exact_set_match"] += 1 if pipeline_result["exact_set_match"] else 0
                    m["component_score_sum"] += pipeline_result["component_score"]
                    m["select_match"] += 1 if pipeline_result["select_match"] else 0
                    m["from_match"] += 1 if pipeline_result["from_match"] else 0
                    m["where_match"] += 1 if pipeline_result["where_match"] else 0
                    m["groupby_match"] += 1 if pipeline_result["groupby_match"] else 0
                    m["orderby_match"] += 1 if pipeline_result["orderby_match"] else 0
                    m["total_time"] += pipeline_result["execution_time"]
                    
                    # By hardness
                    h = q["hardness"]
                    if h in m["by_hardness"]:
                        m["by_hardness"][h]["total"] += 1
                        if pipeline_result["execution_correct"]:
                            m["by_hardness"][h]["correct"] += 1
                    
                except Exception as e:
                    question_result["pipelines"][name] = {
                        "error": str(e),
                        "execution_valid": False,
                        "execution_correct": False,
                        "generated_sql": "",
                        "execution_time": 0
                    }
                    metrics[name]["total"] += 1
            
            detailed_results.append(question_result)
            progress.advance(task)
    
    # Calculate percentages
    summary_metrics = {}
    for name, m in metrics.items():
        total = m["total"] if m["total"] > 0 else 1
        summary_metrics[name] = {
            "total_questions": m["total"],
            "execution_valid_rate": m["execution_valid"] / total,
            "execution_accuracy": m["execution_correct"] / total,
            "exact_set_match_rate": m["exact_set_match"] / total,
            "avg_component_score": m["component_score_sum"] / total,
            "select_match_rate": m["select_match"] / total,
            "from_match_rate": m["from_match"] / total,
            "where_match_rate": m["where_match"] / total,
            "groupby_match_rate": m["groupby_match"] / total,
            "orderby_match_rate": m["orderby_match"] / total,
            "avg_time_per_question": m["total_time"] / total,
            "total_time": m["total_time"],
            "by_hardness": {
                h: {
                    "total": v["total"],
                    "correct": v["correct"],
                    "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0
                }
                for h, v in m["by_hardness"].items()
            }
        }
    
    return detailed_results, summary_metrics


def save_db_results(detailed_results: List[Dict], summary_metrics: Dict, db_id: str):
    """Save results to separate folder for each database"""
    
    # Create database-specific directory
    db_dir = RESULTS_DIR / db_id
    db_dir.mkdir(parents=True, exist_ok=True)
    
    charts_dir = db_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    
    console.print(f"\n[cyan]Saving results for {db_id}...[/cyan]")
    
    # 1. Detailed Results JSON
    with open(db_dir / "detailed_results.json", 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    console.print(f"  [green]✓ detailed_results.json[/green]")
    
    # 2. Summary Metrics JSON
    with open(db_dir / "summary_metrics.json", 'w', encoding='utf-8') as f:
        json.dump(summary_metrics, f, indent=2)
    console.print(f"  [green]✓ summary_metrics.json[/green]")
    
    # 3. CSV Results
    save_csv_results(detailed_results, summary_metrics, db_dir, db_id)
    console.print(f"  [green]✓ evaluation_results.csv[/green]")
    
    # 4. HTML Report
    save_html_report(detailed_results, summary_metrics, db_id, db_dir / "evaluation_report.html")
    console.print(f"  [green]✓ evaluation_report.html[/green]")
    
    # 5. Markdown Report
    save_markdown_report(detailed_results, summary_metrics, db_id, db_dir / "evaluation_report.md")
    console.print(f"  [green]✓ evaluation_report.md[/green]")
    
    # 6. Charts
    save_charts(summary_metrics, db_id, charts_dir)
    console.print(f"  [green]✓ charts/ (4 charts)[/green]")


def save_csv_results(detailed_results: List[Dict], summary_metrics: Dict, output_dir: Path, db_id: str):
    """Save results in CSV format"""
    
    # 1. Detailed results CSV
    csv_path = output_dir / "evaluation_results.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "ID", "Question", "Hardness", "Gold SQL",
            "Single_Agent_SQL", "Single_Agent_Correct", "Single_Agent_Time",
            "Multi_Agent_SQL", "Multi_Agent_Correct", "Multi_Agent_Time",
            "Multi_Agent_RAG_SQL", "Multi_Agent_RAG_Correct", "Multi_Agent_RAG_Time"
        ])
        
        # Data rows
        for r in detailed_results:
            row = [
                r["id"],
                r["question"],
                r["hardness"],
                r["gold_sql"]
            ]
            
            for pname in ["Single_Agent", "Multi_Agent", "Multi_Agent_RAG"]:
                p = r["pipelines"].get(pname, {})
                row.extend([
                    p.get("generated_sql", ""),
                    "Yes" if p.get("execution_correct") else "No",
                    f"{p.get('execution_time', 0):.1f}"
                ])
            
            writer.writerow(row)
    
    # 2. Summary metrics CSV
    summary_csv_path = output_dir / "summary_metrics.csv"
    with open(summary_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Pipeline", "Total Questions", "Execution Accuracy", "Exact Set Match",
            "Component Score", "SELECT Match", "FROM Match", "WHERE Match",
            "GROUP BY Match", "ORDER BY Match", "Avg Time (s)", "Total Time (s)"
        ])
        
        for name, m in summary_metrics.items():
            writer.writerow([
                name.replace("_", " "),
                m["total_questions"],
                f"{m['execution_accuracy']:.1%}",
                f"{m['exact_set_match_rate']:.1%}",
                f"{m['avg_component_score']:.1%}",
                f"{m['select_match_rate']:.1%}",
                f"{m['from_match_rate']:.1%}",
                f"{m['where_match_rate']:.1%}",
                f"{m['groupby_match_rate']:.1%}",
                f"{m['orderby_match_rate']:.1%}",
                f"{m['avg_time_per_question']:.1f}",
                f"{m['total_time']:.1f}"
            ])


def save_html_report(detailed_results: List[Dict], summary_metrics: Dict, db_id: str, output_path: Path):
    """Create HTML report"""
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text-to-SQL Evaluation - {db_id}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #e2e8f0;
            --muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        h2 {{
            color: var(--primary);
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }}
        .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
        .card {{
            background: var(--card);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .card h3 {{ font-size: 1rem; color: var(--muted); margin-bottom: 0.5rem; }}
        .card .value {{
            font-size: 2.5rem;
            font-weight: bold;
        }}
        .success {{ color: var(--success); }}
        .warning {{ color: var(--warning); }}
        .danger {{ color: var(--danger); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: var(--card);
            border-radius: 0.5rem;
            overflow: hidden;
        }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ background: rgba(99, 102, 241, 0.2); font-weight: 600; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .badge-easy {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .badge-medium {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
        .sql-box {{
            background: #0d1117;
            padding: 1rem;
            border-radius: 0.5rem;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            margin: 0.5rem 0;
            border-left: 3px solid var(--primary);
        }}
        .progress-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary), #a855f7);
            border-radius: 4px;
        }}
        .question-card {{
            background: var(--card);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin: 1rem 0;
        }}
        .pipeline-results {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }}
        .pipeline-result {{
            background: rgba(0,0,0,0.2);
            padding: 1rem;
            border-radius: 0.5rem;
        }}
        .pipeline-result h4 {{ font-size: 0.9rem; margin-bottom: 0.5rem; }}
        .chart-container {{
            background: var(--card);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 0.5rem; }}
        @media (max-width: 768px) {{
            .pipeline-results {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Intelligent SQL Query Agent</h1>
        <p class="subtitle">Evaluation Report | Database: <strong>{db_id}</strong> | {datetime.now().strftime("%Y-%m-%d %H:%M")} | Total: {len(detailed_results)} questions</p>
        
        <h2>📊 Summary - 3 Pipeline Comparison</h2>
        <div class="grid">
'''
    
    # Summary cards
    for name, m in summary_metrics.items():
        acc_class = "success" if m["execution_accuracy"] >= 0.7 else "warning" if m["execution_accuracy"] >= 0.5 else "danger"
        html += f'''
            <div class="card">
                <h3>{name.replace("_", " ")}</h3>
                <div class="value {acc_class}">{m["execution_accuracy"]:.1%}</div>
                <p style="color: var(--muted); font-size: 0.9rem;">Execution Accuracy</p>
                <div class="progress-bar"><div class="progress-fill" style="width: {m["execution_accuracy"]*100}%"></div></div>
                <div style="margin-top: 1rem; display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
                    <div>Set Match: <strong>{m["exact_set_match_rate"]:.1%}</strong></div>
                    <div>Component: <strong>{m["avg_component_score"]:.1%}</strong></div>
                    <div>Avg Time: <strong>{m["avg_time_per_question"]:.1f}s</strong></div>
                    <div>Total: <strong>{m["total_questions"]} Q</strong></div>
                </div>
            </div>
'''
    
    html += '''
        </div>
        
        <h2>📈 Detailed Comparison Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Pipeline</th>
                    <th>Execution Accuracy</th>
                    <th>Exact Set Match</th>
                    <th>SELECT Match</th>
                    <th>FROM Match</th>
                    <th>WHERE Match</th>
                    <th>GROUP BY Match</th>
                    <th>ORDER BY Match</th>
                    <th>Avg Time</th>
                </tr>
            </thead>
            <tbody>
'''
    
    for name, m in summary_metrics.items():
        badge_class = 'badge-success' if m['execution_accuracy'] >= 0.7 else 'badge-danger'
        html += f'''
                <tr>
                    <td><strong>{name.replace("_", " ")}</strong></td>
                    <td><span class="badge {badge_class}">{m['execution_accuracy']:.1%}</span></td>
                    <td>{m['exact_set_match_rate']:.1%}</td>
                    <td>{m['select_match_rate']:.1%}</td>
                    <td>{m['from_match_rate']:.1%}</td>
                    <td>{m['where_match_rate']:.1%}</td>
                    <td>{m['groupby_match_rate']:.1%}</td>
                    <td>{m['orderby_match_rate']:.1%}</td>
                    <td>{m['avg_time_per_question']:.1f}s</td>
                </tr>
'''
    
    html += '''
            </tbody>
        </table>
        
        <h2>📊 Charts</h2>
        <div class="grid">
            <div class="chart-container">
                <h3>Accuracy Comparison</h3>
                <img src="charts/accuracy_comparison.png" alt="Accuracy">
            </div>
            <div class="chart-container">
                <h3>Time Comparison</h3>
                <img src="charts/time_comparison.png" alt="Time">
            </div>
            <div class="chart-container">
                <h3>Component Breakdown</h3>
                <img src="charts/component_breakdown.png" alt="Components">
            </div>
            <div class="chart-container">
                <h3>By Difficulty Level</h3>
                <img src="charts/accuracy_by_difficulty.png" alt="Difficulty">
            </div>
        </div>
        
        <h2>📝 All Question Results</h2>
'''
    
    # All questions
    for r in detailed_results:
        html += f'''
        <div class="question-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong>Q{r['id']}</strong>
                <span class="badge badge-{r['hardness']}">{r['hardness'].upper()}</span>
            </div>
            <p style="margin-bottom: 0.5rem;">{r['question']}</p>
            <div class="sql-box">Gold: {r['gold_sql']}</div>
            <div class="pipeline-results">
'''
        for pname, presult in r.get("pipelines", {}).items():
            status = "✅" if presult.get("execution_correct") else "❌"
            sql = presult.get("generated_sql", "ERROR")[:100]
            time_val = presult.get("execution_time", 0)
            html += f'''
                <div class="pipeline-result">
                    <h4>{pname.replace("_", " ")} {status}</h4>
                    <div style="font-size: 0.8rem; color: var(--muted);">Time: {time_val:.1f}s</div>
                    <div class="sql-box" style="font-size: 0.75rem;">{sql}{'...' if len(presult.get("generated_sql", "")) > 100 else ''}</div>
                </div>
'''
        html += '''
            </div>
        </div>
'''
    
    html += '''
        <footer style="text-align: center; padding: 2rem; color: var(--muted);">
            <p>Generated by Intelligent SQL Query Agent</p>
        </footer>
    </div>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def save_markdown_report(detailed_results: List[Dict], summary_metrics: Dict, db_id: str, output_path: Path):
    """Create Markdown report"""
    
    lines = [
        f"# 🤖 Intelligent SQL Query Agent Evaluation",
        f"",
        f"**Database:** {db_id}  ",
        f"**Total Questions:** {len(detailed_results)}  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"---",
        f"",
        f"## 📊 Summary - 3 Pipeline Comparison",
        f"",
        f"| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |",
        f"|----------|-------------------|-----------------|-----------------|----------|",
    ]
    
    for name, m in summary_metrics.items():
        lines.append(
            f"| **{name.replace('_', ' ')}** | {m['execution_accuracy']:.1%} | "
            f"{m['exact_set_match_rate']:.1%} | {m['avg_component_score']:.1%} | "
            f"{m['avg_time_per_question']:.1f}s |"
        )
    
    # Winner
    best = max(summary_metrics.items(), key=lambda x: x[1]["execution_accuracy"])
    lines.extend([
        f"",
        f"### 🏆 Best: {best[0].replace('_', ' ')} ({best[1]['execution_accuracy']:.1%})",
        f"",
        f"---",
        f"",
        f"## 📈 Component Matching",
        f"",
        f"| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |",
        f"|----------|--------|------|-------|----------|----------|",
    ])
    
    for name, m in summary_metrics.items():
        lines.append(
            f"| {name.replace('_', ' ')} | {m['select_match_rate']:.0%} | "
            f"{m['from_match_rate']:.0%} | {m['where_match_rate']:.0%} | "
            f"{m['groupby_match_rate']:.0%} | {m['orderby_match_rate']:.0%} |"
        )
    
    lines.extend([f"", f"---", f"", f"## 📝 Detailed Results", f""])
    
    for r in detailed_results[:50]:  # First 50
        emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(r["hardness"], "⚪")
        lines.append(f"### Q{r['id']} {emoji}")
        lines.append(f"**{r['question']}**")
        lines.append(f"```sql")
        lines.append(f"-- Gold: {r['gold_sql']}")
        lines.append(f"```")
        
        for pname, p in r.get("pipelines", {}).items():
            status = "✅" if p.get("execution_correct") else "❌"
            lines.append(f"- **{pname}** {status}: `{p.get('generated_sql', 'N/A')[:60]}...`")
        
        lines.append(f"")
    
    if len(detailed_results) > 50:
        lines.append(f"*... and {len(detailed_results) - 50} more questions*")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def save_charts(summary_metrics: Dict, db_id: str, charts_dir: Path):
    """Create and save charts"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        plt.style.use('dark_background')
        pipelines = list(summary_metrics.keys())
        colors = ['#22c55e', '#3b82f6', '#a855f7']
        
        # 1. Accuracy Comparison
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(pipelines))
        width = 0.25
        
        exec_acc = [summary_metrics[p]["execution_accuracy"] * 100 for p in pipelines]
        set_match = [summary_metrics[p]["exact_set_match_rate"] * 100 for p in pipelines]
        comp_score = [summary_metrics[p]["avg_component_score"] * 100 for p in pipelines]
        
        ax.bar(x - width, exec_acc, width, label='Execution Accuracy', color='#22c55e')
        ax.bar(x, set_match, width, label='Exact Set Match', color='#3b82f6')
        ax.bar(x + width, comp_score, width, label='Component Score', color='#a855f7')
        
        ax.set_ylabel('Score (%)')
        ax.set_title(f'Pipeline Performance - {db_id}')
        ax.set_xticks(x)
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        ax.legend()
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        plt.savefig(charts_dir / "accuracy_comparison.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 2. Time Comparison
        fig, ax = plt.subplots(figsize=(8, 5))
        times = [summary_metrics[p]["avg_time_per_question"] for p in pipelines]
        bars = ax.bar(pipelines, times, color=colors)
        ax.set_ylabel('Average Time (seconds)')
        ax.set_title(f'Average Time per Question - {db_id}')
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        
        for bar, time in zip(bars, times):
            ax.annotate(f'{time:.1f}s', xy=(bar.get_x() + bar.get_width() / 2, time),
                       xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(charts_dir / "time_comparison.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 3. Component Breakdown
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        components = ['select_match_rate', 'from_match_rate', 'where_match_rate', 'groupby_match_rate', 'orderby_match_rate']
        comp_names = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
        
        for idx, (pname, ax) in enumerate(zip(pipelines, axes)):
            values = [summary_metrics[pname][c] * 100 for c in components]
            ax.bar(comp_names, values, color=colors[idx])
            ax.set_title(pname.replace("_", " "))
            ax.set_ylim(0, 100)
            ax.set_ylabel('Match Rate (%)')
        
        plt.suptitle(f'Component Matching - {db_id}', fontsize=14)
        plt.tight_layout()
        plt.savefig(charts_dir / "component_breakdown.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 4. Accuracy by Difficulty
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(pipelines))
        width = 0.35
        
        easy_acc = []
        medium_acc = []
        for p in pipelines:
            by_h = summary_metrics[p]["by_hardness"]
            easy_acc.append(by_h["easy"]["accuracy"] * 100 if by_h["easy"]["total"] > 0 else 0)
            medium_acc.append(by_h["medium"]["accuracy"] * 100 if by_h["medium"]["total"] > 0 else 0)
        
        ax.bar(x - width/2, easy_acc, width, label='Easy', color='#22c55e')
        ax.bar(x + width/2, medium_acc, width, label='Medium', color='#f59e0b')
        
        ax.set_ylabel('Accuracy (%)')
        ax.set_title(f'Accuracy by Difficulty - {db_id}')
        ax.set_xticks(x)
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        ax.legend()
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        plt.savefig(charts_dir / "accuracy_by_difficulty.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
    except ImportError:
        console.print("[yellow]matplotlib not installed, skipping charts[/yellow]")


def save_combined_results(all_results: Dict[str, Tuple], combined_metrics: Dict):
    """Save combined comparison of all databases"""
    
    combined_dir = RESULTS_DIR / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = combined_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    
    console.print(f"\n[bold cyan]Saving combined results...[/bold cyan]")
    
    # 1. Combined Summary JSON
    summary_data = {
        "evaluation_date": datetime.now().isoformat(),
        "databases": list(all_results.keys()),
        "total_questions": sum(combined_metrics[p]["total"] for p in combined_metrics),
        "pipelines": {}
    }
    
    for pname, m in combined_metrics.items():
        summary_data["pipelines"][pname] = {
            "total_questions": m["total"],
            "correct_answers": m["correct"],
            "execution_accuracy": m["correct"] / m["total"] if m["total"] > 0 else 0,
            "total_time_seconds": m["time"],
            "avg_time_per_question": m["time"] / m["total"] if m["total"] > 0 else 0
        }
    
    summary_data["per_database"] = {}
    for db_id, (detailed, summary) in all_results.items():
        summary_data["per_database"][db_id] = {
            "total_questions": len(detailed),
            "pipelines": summary
        }
    
    with open(combined_dir / "combined_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    console.print(f"  [green]✓ combined_summary.json[/green]")
    
    # 2. Combined CSV
    csv_path = combined_dir / "all_databases_comparison.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["Database", "Pipeline", "Total Questions", "Correct", "Accuracy", "Avg Time (s)"])
        
        # Per-database rows
        for db_id, (detailed, summary) in all_results.items():
            for pname, m in summary.items():
                writer.writerow([
                    db_id,
                    pname.replace("_", " "),
                    m["total_questions"],
                    int(m["execution_accuracy"] * m["total_questions"]),
                    f"{m['execution_accuracy']:.1%}",
                    f"{m['avg_time_per_question']:.1f}"
                ])
        
        writer.writerow([])  # Empty row
        writer.writerow(["COMBINED TOTALS", "", "", "", "", ""])
        
        for pname, m in combined_metrics.items():
            acc = m["correct"] / m["total"] if m["total"] > 0 else 0
            avg_time = m["time"] / m["total"] if m["total"] > 0 else 0
            writer.writerow([
                "ALL DATABASES",
                pname.replace("_", " "),
                m["total"],
                m["correct"],
                f"{acc:.1%}",
                f"{avg_time:.1f}"
            ])
    
    console.print(f"  [green]✓ all_databases_comparison.csv[/green]")
    
    # 3. Combined HTML Report
    save_combined_html(all_results, combined_metrics, combined_dir / "all_databases_comparison.html")
    console.print(f"  [green]✓ all_databases_comparison.html[/green]")
    
    # 4. Combined Charts
    save_combined_charts(all_results, combined_metrics, charts_dir)
    console.print(f"  [green]✓ charts/ (comparison charts)[/green]")


def save_combined_html(all_results: Dict, combined_metrics: Dict, output_path: Path):
    """Combined HTML report for 5 databases"""
    
    total_questions = sum(combined_metrics[p]["total"] for p in combined_metrics)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Combined Evaluation - All Databases</title>
    <style>
        :root {{
            --primary: #6366f1; --success: #22c55e; --warning: #f59e0b; --danger: #ef4444;
            --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 2.5rem; background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }}
        h2 {{ color: var(--primary); margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--primary); }}
        .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
        .card {{ background: var(--card); border-radius: 1rem; padding: 1.5rem; }}
        .card h3 {{ color: var(--muted); margin-bottom: 0.5rem; }}
        .card .value {{ font-size: 2.5rem; font-weight: bold; }}
        .success {{ color: var(--success); }}
        .warning {{ color: var(--warning); }}
        .danger {{ color: var(--danger); }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; background: var(--card); border-radius: 0.5rem; overflow: hidden; }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ background: rgba(99, 102, 241, 0.2); }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
        .badge-success {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .db-section {{ margin: 2rem 0; padding: 1.5rem; background: var(--card); border-radius: 1rem; }}
        .db-title {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }}
        .db-title h3 {{ color: var(--primary); }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem; }}
        .chart-container {{ background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 0.5rem; }}
        .chart-container img {{ width: 100%; height: auto; }}
        .winner {{ background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(99, 102, 241, 0.2)); border: 2px solid var(--success); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Intelligent SQL Query Agent</h1>
        <p class="subtitle">Combined Evaluation Report | 5 Databases | {datetime.now().strftime("%Y-%m-%d %H:%M")} | Total: {total_questions // 3} unique questions tested</p>
        
        <h2>🏆 Combined Results - 3 Pipeline Comparison</h2>
        <div class="grid">
'''
    
    # Combined cards
    best_pipeline = max(combined_metrics.items(), key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] > 0 else 0)
    
    for pname, m in combined_metrics.items():
        acc = m["correct"] / m["total"] if m["total"] > 0 else 0
        acc_class = "success" if acc >= 0.7 else "warning" if acc >= 0.5 else "danger"
        is_winner = pname == best_pipeline[0]
        
        html += f'''
            <div class="card {'winner' if is_winner else ''}">
                <h3>{pname.replace("_", " ")} {'🏆' if is_winner else ''}</h3>
                <div class="value {acc_class}">{acc:.1%}</div>
                <p style="color: var(--muted);">Combined Accuracy ({m["total"]} questions)</p>
                <div style="margin-top: 1rem; font-size: 0.9rem;">
                    <div>Correct: <strong>{m["correct"]}/{m["total"]}</strong></div>
                    <div>Total Time: <strong>{m["time"]:.0f}s</strong></div>
                    <div>Avg Time: <strong>{m["time"]/m["total"]:.1f}s</strong></div>
                </div>
            </div>
'''
    
    html += '''
        </div>
        
        <h2>📊 Database-Based Comparison</h2>
        <table>
            <thead>
                <tr>
                    <th>Database</th>
                    <th>Questions</th>
                    <th>Single Agent</th>
                    <th>Multi Agent</th>
                    <th>Multi Agent RAG</th>
                    <th>Best</th>
                </tr>
            </thead>
            <tbody>
'''
    
    for db_id, (detailed, summary) in all_results.items():
        db_best = max(summary.items(), key=lambda x: x[1]["execution_accuracy"])
        
        html += f'''
                <tr>
                    <td><strong>{db_id}</strong></td>
                    <td>{len(detailed)}</td>
'''
        for pname in ["Single_Agent", "Multi_Agent", "Multi_Agent_RAG"]:
            m = summary.get(pname, {})
            acc = m.get("execution_accuracy", 0)
            badge_class = "badge-success" if acc >= 0.7 else "badge-warning" if acc >= 0.5 else "badge-danger"
            html += f'                    <td><span class="badge {badge_class}">{acc:.1%}</span></td>\n'
        
        html += f'''                    <td><strong>{db_best[0].replace("_", " ")}</strong></td>
                </tr>
'''
    
    html += '''
            </tbody>
        </table>
        
        <h2>📈 Comparison Charts</h2>
        <div class="chart-grid">
            <div class="chart-container">
                <h4>Combined Accuracy</h4>
                <img src="charts/combined_accuracy.png" alt="Combined Accuracy">
            </div>
            <div class="chart-container">
                <h4>Per-Database Comparison</h4>
                <img src="charts/per_database_comparison.png" alt="Per DB">
            </div>
            <div class="chart-container">
                <h4>Time Comparison</h4>
                <img src="charts/combined_time.png" alt="Time">
            </div>
            <div class="chart-container">
                <h4>Accuracy Heatmap</h4>
                <img src="charts/accuracy_heatmap.png" alt="Heatmap">
            </div>
        </div>
'''
    
    # Per-database sections
    for db_id, (detailed, summary) in all_results.items():
        html += f'''
        <div class="db-section">
            <div class="db-title">
                <h3>🗄️ {db_id}</h3>
                <span style="color: var(--muted);">({len(detailed)} questions)</span>
            </div>
            <table>
                <tr>
                    <th>Pipeline</th>
                    <th>Accuracy</th>
                    <th>Set Match</th>
                    <th>Component Score</th>
                    <th>Avg Time</th>
                </tr>
'''
        for pname, m in summary.items():
            badge_class = "badge-success" if m["execution_accuracy"] >= 0.7 else "badge-warning" if m["execution_accuracy"] >= 0.5 else "badge-danger"
            html += f'''
                <tr>
                    <td>{pname.replace("_", " ")}</td>
                    <td><span class="badge {badge_class}">{m["execution_accuracy"]:.1%}</span></td>
                    <td>{m["exact_set_match_rate"]:.1%}</td>
                    <td>{m["avg_component_score"]:.1%}</td>
                    <td>{m["avg_time_per_question"]:.1f}s</td>
                </tr>
'''
        html += '''
            </table>
        </div>
'''
    
    html += '''
        <footer style="text-align: center; padding: 2rem; color: var(--muted);">
            <p>Generated by Intelligent SQL Query Agent</p>
            <p>Databases: world_1, concert_singer, student_transcripts_tracking</p>
        </footer>
    </div>
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def save_combined_charts(all_results: Dict, combined_metrics: Dict, charts_dir: Path):
    """Combined comparison charts"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        plt.style.use('dark_background')
        pipelines = list(combined_metrics.keys())
        databases = list(all_results.keys())
        colors = ['#22c55e', '#3b82f6', '#a855f7']
        db_colors = ['#f59e0b', '#ec4899', '#06b6d4']
        
        # 1. Combined Accuracy Bar Chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        accs = [combined_metrics[p]["correct"] / combined_metrics[p]["total"] * 100 
                if combined_metrics[p]["total"] > 0 else 0 for p in pipelines]
        
        bars = ax.bar(pipelines, accs, color=colors)
        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Combined Accuracy Across All Databases')
        ax.set_ylim(0, 100)
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        
        for bar, acc in zip(bars, accs):
            ax.annotate(f'{acc:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, acc),
                       xytext=(0, 3), textcoords="offset points", ha='center', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(charts_dir / "combined_accuracy.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 2. Per-Database Comparison (Grouped Bar)
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(databases))
        width = 0.25
        
        for i, pname in enumerate(pipelines):
            accs = []
            for db_id in databases:
                summary = all_results[db_id][1]
                accs.append(summary[pname]["execution_accuracy"] * 100)
            
            ax.bar(x + i * width, accs, width, label=pname.replace("_", " "), color=colors[i])
        
        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Per-Database Accuracy Comparison')
        ax.set_xticks(x + width)
        ax.set_xticklabels(databases)
        ax.legend()
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        plt.savefig(charts_dir / "per_database_comparison.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 3. Combined Time Comparison
        fig, ax = plt.subplots(figsize=(10, 6))
        
        avg_times = [combined_metrics[p]["time"] / combined_metrics[p]["total"] 
                     if combined_metrics[p]["total"] > 0 else 0 for p in pipelines]
        
        bars = ax.bar(pipelines, avg_times, color=colors)
        ax.set_ylabel('Average Time per Question (seconds)')
        ax.set_title('Combined Time Comparison')
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        
        for bar, t in zip(bars, avg_times):
            ax.annotate(f'{t:.1f}s', xy=(bar.get_x() + bar.get_width() / 2, t),
                       xytext=(0, 3), textcoords="offset points", ha='center')
        
        plt.tight_layout()
        plt.savefig(charts_dir / "combined_time.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
        # 4. Accuracy Heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data = []
        for db_id in databases:
            row = []
            summary = all_results[db_id][1]
            for pname in pipelines:
                row.append(summary[pname]["execution_accuracy"] * 100)
            data.append(row)
        
        data = np.array(data)
        im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        
        ax.set_xticks(np.arange(len(pipelines)))
        ax.set_yticks(np.arange(len(databases)))
        ax.set_xticklabels([p.replace("_", "\n") for p in pipelines])
        ax.set_yticklabels(databases)
        
        # Add text annotations
        for i in range(len(databases)):
            for j in range(len(pipelines)):
                text = ax.text(j, i, f'{data[i, j]:.1f}%', ha="center", va="center", 
                              color="black" if data[i, j] > 50 else "white", fontweight='bold')
        
        ax.set_title('Accuracy Heatmap (Database × Pipeline)')
        fig.colorbar(im, ax=ax, label='Accuracy %')
        
        plt.tight_layout()
        plt.savefig(charts_dir / "accuracy_heatmap.png", dpi=150, facecolor='#0f172a')
        plt.close()
        
    except ImportError:
        console.print("[yellow]matplotlib not installed, skipping charts[/yellow]")


def run_full_evaluation(
    db_ids: List[str] = None,
    exclude_hard: bool = True,
    limit_per_db: int = None
):
    """
    Main evaluation function - Test all databases and save results.
    """
    if db_ids is None:
        db_ids = FEATURED_DATABASES
    
    console.print(Panel(
        f"[bold]🚀 Full Multi-Database Evaluation[/bold]\n\n"
        f"Total Databases: {len(db_ids)}\n"
        f"Databases: {', '.join(db_ids[:10])}{'...' if len(db_ids) > 10 else ''}\n"
        f"Exclude Hard: {exclude_hard}\n"
        f"Limit per DB: {limit_per_db or 'All questions'}",
        title="Starting Evaluation",
        border_style="cyan"
    ))
    
    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Initialize shared LLM client
    llm = OllamaClient()
    
    # Store all results
    all_results = {}
    combined_metrics = {
        "Single_Agent": {"total": 0, "correct": 0, "time": 0},
        "Multi_Agent": {"total": 0, "correct": 0, "time": 0},
        "Multi_Agent_RAG": {"total": 0, "correct": 0, "time": 0}
    }
    
    # Run evaluation for each database
    for db_id in db_ids:
        console.print(f"\n{'='*60}")
        console.print(f"[bold cyan]Database: {db_id}[/bold cyan]")
        console.print(f"{'='*60}\n")
        
        try:
            detailed, summary = run_single_db_evaluation(
                db_id=db_id,
                exclude_hard=exclude_hard,
                limit=limit_per_db,
                llm=llm
            )
            
            # Save individual database results
            save_db_results(detailed, summary, db_id)
            
            # Store for combined analysis
            all_results[db_id] = (detailed, summary)
            
            # Update combined metrics
            for pname in combined_metrics.keys():
                if pname in summary:
                    m = summary[pname]
                    combined_metrics[pname]["total"] += m["total_questions"]
                    combined_metrics[pname]["correct"] += int(m["execution_accuracy"] * m["total_questions"])
                    combined_metrics[pname]["time"] += m["total_time"]
            
            # Display database summary
            display_db_summary(summary, db_id)
            
        except Exception as e:
            console.print(f"[red]Error evaluating {db_id}: {e}[/red]")
            import traceback
            traceback.print_exc()
    
    # Save combined results
    if len(all_results) > 1:
        save_combined_results(all_results, combined_metrics)
    
    # Display final combined summary
    display_combined_summary(combined_metrics, all_results)
    
    return all_results, combined_metrics


def display_db_summary(summary: Dict, db_id: str):
    """Display summary for a single database"""
    table = Table(title=f"📊 {db_id} Results")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Accuracy", justify="center")
    table.add_column("Set Match", justify="center")
    table.add_column("Avg Time", justify="right")
    
    for name, m in summary.items():
        table.add_row(
            name.replace("_", " "),
            f"{m['execution_accuracy']:.1%}",
            f"{m['exact_set_match_rate']:.1%}",
            f"{m['avg_time_per_question']:.1f}s"
        )
    
    console.print(table)


def display_combined_summary(combined_metrics: Dict, all_results: Dict):
    """Display combined results"""
    console.print(f"\n{'='*60}")
    console.print(f"[bold green]🏆 COMBINED RESULTS - ALL DATABASES[/bold green]")
    console.print(f"{'='*60}\n")
    
    table = Table(title="📊 Final Combined Results")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Total Q", justify="center")
    table.add_column("Correct", justify="center")
    table.add_column("Accuracy", justify="center")
    table.add_column("Total Time", justify="right")
    
    for name, m in combined_metrics.items():
        acc = m["correct"] / m["total"] if m["total"] > 0 else 0
        table.add_row(
            name.replace("_", " "),
            str(m["total"]),
            str(m["correct"]),
            f"{acc:.1%}",
            f"{m['time']:.0f}s"
        )
    
    console.print(table)
    
    # Winner
    best = max(combined_metrics.items(), key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] > 0 else 0)
    best_acc = best[1]["correct"] / best[1]["total"] if best[1]["total"] > 0 else 0
    
    console.print(Panel(
        f"[bold green]🏆 WINNER: {best[0].replace('_', ' ')}[/bold green]\n"
        f"Combined Accuracy: {best_acc:.1%} ({best[1]['correct']}/{best[1]['total']})",
        title="Final Result",
        border_style="green"
    ))
    
    console.print(f"\n[bold]📁 Results saved to:[/bold]")
    for db_id in all_results.keys():
        console.print(f"  • results/{db_id}/")
    if len(all_results) > 1:
        console.print(f"  • results/combined/")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent SQL Query Agent Full Evaluation")
    parser.add_argument("--db", default=None, help="Single database or comma-separated list")
    parser.add_argument("--all", action="store_true", help="Run on all available databases (default)")
    parser.add_argument("--exclude-hard", action="store_true", default=True, help="Exclude hard questions")
    parser.add_argument("--include-hard", action="store_true", help="Include hard questions")
    parser.add_argument("--limit", type=int, default=None, help="Limit questions per database")
    
    args = parser.parse_args()
    
    exclude_hard = not args.include_hard
    
    if args.db:
        if "," in args.db:
            db_list = [db.strip() for db in args.db.split(",")]
        else:
            db_list = [args.db]
    else:
        db_list = FEATURED_DATABASES  # Default: all available databases
    
    run_full_evaluation(
        db_ids=db_list,
        exclude_hard=exclude_hard,
        limit_per_db=args.limit
    )


if __name__ == "__main__":
    main()
