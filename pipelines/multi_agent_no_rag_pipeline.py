"""
Multi-Agent Pipeline without RAG

Uses 5 specialized agents:
1. Planner Agent - Analyzes question and creates query plan
2. Schema Agent - Extracts database schema (direct from DB)
3. SQL Agent - Generates SQL query
4. Executor Agent - Executes query
5. Evaluator Agent - Evaluates results

No RAG/vector store - schema is read directly from database.
"""

from typing import Any, Dict, List, Optional
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents import (
    PlannerAgent,
    SchemaAgent,
    SQLAgent,
    ExecutorAgent,
    EvaluatorAgent
)
from agents.base_agent import AgentState
from utils.llm_client import OllamaClient

console = Console()


class MultiAgentNoRAGPipeline:
    """
    Multi-agent pipeline without RAG.
    
    Each agent handles a specific task in the Text-to-SQL process.
    Schema is extracted directly from the database.
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize multi-agent pipeline.
        
        Args:
            llm_client: Shared Ollama client
        """
        self.llm = llm_client or OllamaClient()
        
        # Initialize agents
        self.planner = PlannerAgent(self.llm)
        self.schema_agent = SchemaAgent(use_rag=False)
        self.sql_agent = SQLAgent(self.llm)
        self.executor = ExecutorAgent(allow_modifications=False)
        self.evaluator = EvaluatorAgent(self.llm)
        
        self.verbose = False
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output for all agents."""
        self.verbose = verbose
        for agent in [self.planner, self.schema_agent, self.sql_agent, 
                      self.executor, self.evaluator]:
            agent.set_verbose(verbose)
    
    def run(
        self, 
        question: str, 
        db_path: str,
        include_evaluation: bool = True
    ) -> Dict[str, Any]:
        """
        Run the multi-agent pipeline.
        
        Args:
            question: Natural language question
            db_path: Path to SQLite database
            include_evaluation: Whether to run evaluation
            
        Returns:
            Pipeline result dictionary
        """
        start_time = time.time()
        
        # Initialize state
        state = {
            "question": question,
            "db_path": db_path,
            "errors": [],
            "agent_timings": {}
        }
        
        pipeline_steps = [
            ("planner", self.planner),
            ("schema", self.schema_agent),
            ("sql", self.sql_agent),
            ("executor", self.executor),
        ]
        
        if include_evaluation:
            pipeline_steps.append(("evaluator", self.evaluator))
        
        # Run pipeline
        for step_name, agent in pipeline_steps:
            step_start = time.time()
            
            if self.verbose:
                console.print(f"[cyan]Running {agent.name}...[/cyan]")
            
            try:
                state = agent.process(state)
            except Exception as e:
                state["errors"].append(f"{step_name}: {str(e)}")
                if self.verbose:
                    console.print(f"[red]Error in {step_name}: {e}[/red]")
            
            state["agent_timings"][step_name] = time.time() - step_start
        
        # Build result
        result = {
            "question": question,
            "db_path": db_path,
            "pipeline": "multi_agent_no_rag",
            "success": state.get("execution_success", False),
            "sql": state.get("generated_sql", ""),
            "result": state.get("execution_result"),
            "error": state.get("execution_error"),
            "errors": state.get("errors", []),
            "execution_time": time.time() - start_time,
            "agent_timings": state.get("agent_timings", {}),
            "query_type": state.get("query_type", ""),
            "plan": state.get("plan", {}),
            "score": state.get("score", 0),
            "evaluation_details": state.get("evaluation_details", {})
        }
        
        if self.verbose:
            self._display_result(result)
        
        return result
    
    def _display_result(self, result: Dict[str, Any]):
        """Display detailed pipeline result."""
        status = "[green]✓ Success[/green]" if result["success"] else "[red]✗ Failed[/red]"
        
        # Agent timings table
        timing_table = Table(title="Agent Timings", show_header=True)
        timing_table.add_column("Agent", style="cyan")
        timing_table.add_column("Time (s)", justify="right")
        
        for agent, time_val in result["agent_timings"].items():
            timing_table.add_row(agent.capitalize(), f"{time_val:.3f}")
        
        console.print(Panel(
            f"""[bold]Multi-Agent Pipeline (No RAG) Result[/bold]

{status}

[cyan]Question:[/cyan] {result['question']}

[cyan]Query Type:[/cyan] {result['query_type']}

[cyan]Generated SQL:[/cyan]
{result['sql']}

[cyan]Score:[/cyan] {result['score']:.2f}

[cyan]Total Time:[/cyan] {result['execution_time']:.2f}s

[cyan]Result Rows:[/cyan] {len(result['result']) if result['result'] else 0}""",
            title="Pipeline Output"
        ))
        
        console.print(timing_table)
        
        if result.get("errors"):
            console.print("[red]Errors:[/red]")
            for error in result["errors"]:
                console.print(f"  - {error}")
    
    def run_with_retry(
        self, 
        question: str, 
        db_path: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Run pipeline with retry on failure.
        
        Args:
            question: Natural language question
            db_path: Database path
            max_retries: Maximum retry attempts
            
        Returns:
            Pipeline result
        """
        for attempt in range(max_retries):
            result = self.run(question, db_path)
            
            if result["success"]:
                return result
            
            if self.verbose:
                console.print(f"[yellow]Attempt {attempt + 1} failed, retrying...[/yellow]")
        
        return result
    
    def batch_run(
        self, 
        examples: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Run pipeline on multiple examples.
        
        Args:
            examples: List of question/db_path dicts
            
        Returns:
            List of results
        """
        results = []
        
        for i, example in enumerate(examples):
            if self.verbose:
                console.print(f"\n[bold]Example {i+1}/{len(examples)}[/bold]")
            
            result = self.run(
                question=example["question"],
                db_path=example["db_path"]
            )
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["execution_time"] for r in results) / len(results)
        avg_score = sum(r["score"] for r in results) / len(results)
        
        if self.verbose:
            console.print(Panel(
                f"""[bold]Batch Summary[/bold]

Success Rate: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)
Average Score: {avg_score:.2f}
Average Time: {avg_time:.2f}s""",
                title="Batch Results"
            ))
        
        return results
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get information about all agents."""
        return {
            "planner": self.planner.description,
            "schema": self.schema_agent.description,
            "sql": self.sql_agent.description,
            "executor": self.executor.description,
            "evaluator": self.evaluator.description
        }

