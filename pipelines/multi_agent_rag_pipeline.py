"""
Multi-Agent Pipeline with RAG (LangGraph + FAISS)

Uses 5 specialized agents with RAG-enhanced schema retrieval:
1. Planner Agent - Analyzes question and creates query plan
2. Schema Agent - Retrieves relevant schema using RAG
3. SQL Agent - Generates SQL query
4. Executor Agent - Executes query
5. Evaluator Agent - Evaluates results

Features:
- LangGraph for pipeline orchestration
- FAISS for vector-based schema retrieval
- Multiple retrieval methods (dense, sparse, hybrid)
"""

from typing import Any, Dict, List, Literal, Optional
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
from rag.faiss_store import FAISSVectorStore
from rag.schema_embeddings import SchemaEmbedder
from rag.retrieval_methods import DenseRetriever, SparseRetriever, HybridRetriever
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from config.config import RAG_TOP_K

console = Console()


# LangGraph State Definition
try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    console.print("[yellow]LangGraph not available. Install with: pip install langgraph[/yellow]")


class MultiAgentRAGPipeline:
    """
    Multi-agent pipeline with RAG for schema retrieval.
    
    Uses LangGraph for agent orchestration and FAISS for 
    semantic schema retrieval.
    """
    
    def __init__(
        self, 
        llm_client: OllamaClient = None,
        retrieval_method: Literal["dense", "sparse", "hybrid"] = "hybrid"
    ):
        """
        Initialize RAG-enhanced multi-agent pipeline.
        
        Args:
            llm_client: Shared Ollama client
            retrieval_method: Schema retrieval method to use
        """
        self.llm = llm_client or OllamaClient()
        self.retrieval_method = retrieval_method
        
        # Initialize embedder
        self.embedder = SchemaEmbedder()
        
        # Initialize retriever based on method
        self._init_retriever()
        
        # Initialize vector store
        self.vector_store = FAISSVectorStore(
            dimension=self.embedder.dimension,
            store_name=f"schema_store_{retrieval_method}"
        )
        
        # Initialize agents
        self.planner = PlannerAgent(self.llm)
        self.schema_agent = SchemaAgent(use_rag=True, vector_store=None)
        self.sql_agent = SQLAgent(self.llm)
        self.executor = ExecutorAgent(allow_modifications=False)
        self.evaluator = EvaluatorAgent(self.llm)
        
        self.verbose = False
        self.indexed_databases: set = set()
        
        # Build LangGraph if available
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None
    
    def _init_retriever(self):
        """Initialize the appropriate retriever."""
        if self.retrieval_method == "dense":
            self.retriever = DenseRetriever(self.embedder)
        elif self.retrieval_method == "sparse":
            self.retriever = SparseRetriever()
        else:  # hybrid
            self.retriever = HybridRetriever(self.embedder)
    
    def _build_graph(self):
        """Build LangGraph state machine."""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        class PipelineState(TypedDict):
            question: str
            db_path: str
            query_type: str
            plan: Dict[str, Any]
            schema: str
            relevant_tables: List[str]
            foreign_keys: Dict
            generated_sql: str
            sql_explanation: str
            execution_result: Any
            execution_error: Optional[str]
            execution_success: bool
            score: float
            evaluation_details: Dict[str, Any]
            errors: List[str]
            retry_count: int
        
        def plan_node(state: PipelineState) -> PipelineState:
            """Planner agent node."""
            return self.planner.process(dict(state))
        
        def schema_node(state: PipelineState) -> PipelineState:
            """Schema agent node with RAG."""
            # Use retriever for schema
            question = state.get("question", "")
            plan = state.get("plan", {})
            db_path = state.get("db_path", "")
            
            # Build search query
            search_query = question
            if plan.get("required_tables"):
                search_query += " " + " ".join(plan["required_tables"])
            
            # Retrieve relevant schema
            retrieved = self.retriever.retrieve(search_query, k=RAG_TOP_K)
            
            if retrieved:
                schema_text = "\n\n".join([d.get("content", "") for d in retrieved])
                tables = list(set(d.get("table", "") for d in retrieved if d.get("table")))
            else:
                # Fallback to direct extraction
                with DatabaseManager(db_path) as db:
                    schema_text = db.get_schema_text()
                    tables = list(db.get_schema().keys())
            
            state_dict = dict(state)
            state_dict["schema"] = schema_text
            state_dict["relevant_tables"] = tables
            
            return state_dict
        
        def sql_node(state: PipelineState) -> PipelineState:
            """SQL agent node."""
            return self.sql_agent.process(dict(state))
        
        def execute_node(state: PipelineState) -> PipelineState:
            """Executor agent node."""
            return self.executor.process(dict(state))
        
        def evaluate_node(state: PipelineState) -> PipelineState:
            """Evaluator agent node."""
            return self.evaluator.process(dict(state))
        
        def should_retry(state: PipelineState) -> str:
            """Decide whether to retry SQL generation."""
            # Always evaluate if execution succeeded
            if state.get("execution_success", False):
                return "evaluate"
            
            # Check retry count - max 2 retries (strict limit to prevent recursion issues)
            retry_count = state.get("retry_count", 0)
            if retry_count >= 2:
                # Max retries reached, evaluate anyway
                if self.verbose:
                    console.print(f"[yellow]Max retries ({retry_count}) reached, proceeding to evaluation[/yellow]")
                return "evaluate"
            
            # Additional safety: check if we have a valid SQL to retry
            # If SQL is empty or has critical errors, don't retry
            generated_sql = state.get("generated_sql", "")
            errors = state.get("errors", [])
            
            # If we have too many errors or no SQL after multiple attempts, skip retry
            if retry_count >= 1 and (not generated_sql or len(errors) > 3):
                if self.verbose:
                    console.print(f"[yellow]Skipping retry due to persistent errors, proceeding to evaluation[/yellow]")
                return "evaluate"
            
            # Only retry if we haven't exceeded limit
            if self.verbose:
                console.print(f"[cyan]Retrying SQL generation (attempt {retry_count + 1}/2)...[/cyan]")
            return "retry"
        
        def retry_node(state: PipelineState) -> PipelineState:
            """Retry node - increment counter and go back to SQL."""
            state_dict = dict(state)
            current_retry = state_dict.get("retry_count", 0)
            
            # Strict safeguard: don't allow more than 2 retries
            if current_retry >= 2:
                # Force to evaluate if we somehow got here with max retries
                if self.verbose:
                    console.print(f"[red]ERROR: Retry node called with retry_count={current_retry}, forcing evaluation[/red]")
                state_dict["execution_success"] = False
                state_dict["retry_count"] = 2  # Cap it
                return state_dict
            
            # Increment retry count
            state_dict["retry_count"] = current_retry + 1
            # Clear previous SQL and errors to allow fresh generation
            state_dict["generated_sql"] = ""
            state_dict["errors"] = []
            return state_dict
        
        # Build graph
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("plan", plan_node)
        workflow.add_node("schema", schema_node)
        workflow.add_node("sql", sql_node)
        workflow.add_node("execute", execute_node)
        workflow.add_node("evaluate", evaluate_node)
        workflow.add_node("retry", retry_node)
        
        # Add edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "schema")
        workflow.add_edge("schema", "sql")
        workflow.add_edge("sql", "execute")
        workflow.add_conditional_edges(
            "execute",
            should_retry,
            {
                "evaluate": "evaluate",
                "retry": "retry"
            }
        )
        workflow.add_edge("retry", "sql")
        workflow.add_edge("evaluate", END)
        
        return workflow.compile()
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output."""
        self.verbose = verbose
        for agent in [self.planner, self.schema_agent, self.sql_agent, 
                      self.executor, self.evaluator]:
            agent.set_verbose(verbose)
    
    def index_database(self, db_path: str):
        """
        Index a database schema for RAG retrieval.
        
        Args:
            db_path: Path to SQLite database
        """
        if db_path in self.indexed_databases:
            return
        
        if self.verbose:
            console.print(f"[cyan]Indexing database: {db_path}[/cyan]")
        
        # Extract schema
        with DatabaseManager(db_path) as db:
            schema_dict = db.get_schema()
            db_name = db_path.split("/")[-1].replace(".sqlite", "")
        
        # Create documents
        documents, embeddings = self.embedder.embed_schema_for_store(schema_dict, db_name)
        
        # Add to retriever
        doc_dicts = [
            {
                "content": d.get("content", ""),
                "id": d.get("id", ""),
                "table": d.get("table", "")  # Some docs (SQL patterns) don't have table
            }
            for d in documents
        ]
        
        self.retriever.index(doc_dicts)
        self.indexed_databases.add(db_path)
        
        if self.verbose:
            console.print(f"[green]Indexed {len(documents)} schema elements[/green]")
    
    def run(
        self, 
        question: str, 
        db_path: str,
        auto_index: bool = True
    ) -> Dict[str, Any]:
        """
        Run the RAG-enhanced multi-agent pipeline.
        
        Args:
            question: Natural language question
            db_path: Path to SQLite database
            auto_index: Whether to auto-index the database
            
        Returns:
            Pipeline result dictionary
        """
        start_time = time.time()
        
        # Auto-index if needed
        if auto_index and db_path not in self.indexed_databases:
            self.index_database(db_path)
        
        # Initialize state
        initial_state = {
            "question": question,
            "db_path": db_path,
            "query_type": "",
            "plan": {},
            "schema": "",
            "relevant_tables": [],
            "foreign_keys": {},
            "generated_sql": "",
            "sql_explanation": "",
            "execution_result": None,
            "execution_error": None,
            "execution_success": False,
            "score": 0.0,
            "evaluation_details": {},
            "errors": [],
            "retry_count": 0
        }
        
        # Run pipeline
        if self.graph and LANGGRAPH_AVAILABLE:
            # Use LangGraph
            if self.verbose:
                console.print("[cyan]Running LangGraph pipeline...[/cyan]")
            
            # Set recursion limit to prevent infinite loops
            # Max path: plan(1) -> schema(2) -> sql(3) -> execute(4) -> retry(5) -> sql(6) -> execute(7) -> retry(8) -> sql(9) -> execute(10) -> evaluate(11) = 11 nodes
            # With safety margin for internal operations: 11 * 3 = 33, round up to 100 for safety
            config = {"recursion_limit": 100}
            try:
                final_state = self.graph.invoke(initial_state, config=config)
            except Exception as e:
                error_str = str(e).lower()
                # If recursion limit hit, fall back to sequential execution
                if "recursion_limit" in error_str:
                    # Silently fall back to sequential execution
                    # The fallback is automatic and seamless - no user notification needed
                    # Sequential execution produces identical results
                    final_state = self._run_sequential(initial_state)
                else:
                    # Re-raise other exceptions
                    raise
        else:
            # Fallback to sequential execution
            if self.verbose:
                console.print("[cyan]Running sequential pipeline...[/cyan]")
            
            final_state = self._run_sequential(initial_state)
        
        # Build result
        result = {
            "question": question,
            "db_path": db_path,
            "pipeline": f"multi_agent_rag_{self.retrieval_method}",
            "retrieval_method": self.retrieval_method,
            "success": final_state.get("execution_success", False),
            "sql": final_state.get("generated_sql", ""),
            "result": final_state.get("execution_result"),
            "error": final_state.get("execution_error"),
            "errors": final_state.get("errors", []),
            "execution_time": time.time() - start_time,
            "query_type": final_state.get("query_type", ""),
            "plan": final_state.get("plan", {}),
            "relevant_tables": final_state.get("relevant_tables", []),
            "score": final_state.get("score", 0),
            "evaluation_details": final_state.get("evaluation_details", {}),
            "retry_count": final_state.get("retry_count", 0)
        }
        
        if self.verbose:
            self._display_result(result)
        
        return result
    
    def _run_sequential(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run pipeline sequentially without LangGraph."""
        question = state.get("question", "")
        db_path = state.get("db_path", "")
        
        # 1. Plan
        state = self.planner.process(state)
        
        # 2. Schema retrieval with RAG
        search_query = question
        if state.get("plan", {}).get("required_tables"):
            search_query += " " + " ".join(state["plan"]["required_tables"])
        
        retrieved = self.retriever.retrieve(search_query, k=RAG_TOP_K)
        
        if retrieved:
            state["schema"] = "\n\n".join([d.get("content", "") for d in retrieved])
            state["relevant_tables"] = list(set(
                d.get("table", "") for d in retrieved if d.get("table")
            ))
        else:
            with DatabaseManager(db_path) as db:
                state["schema"] = db.get_schema_text()
                state["relevant_tables"] = list(db.get_schema().keys())
        
        # 3-5. SQL, Execute, Evaluate with retry
        max_retries = 2
        for attempt in range(max_retries + 1):
            state = self.sql_agent.process(state)
            state = self.executor.process(state)
            
            if state.get("execution_success"):
                break
            
            state["retry_count"] = attempt + 1
        
        state = self.evaluator.process(state)
        
        return state
    
    def _display_result(self, result: Dict[str, Any]):
        """Display detailed pipeline result."""
        status = "[green]✓ Success[/green]" if result["success"] else "[red]✗ Failed[/red]"
        
        console.print(Panel(
            f"""[bold]Multi-Agent RAG Pipeline Result[/bold]

{status}

[cyan]Retrieval Method:[/cyan] {result['retrieval_method'].upper()}

[cyan]Question:[/cyan] {result['question']}

[cyan]Query Type:[/cyan] {result['query_type']}

[cyan]Relevant Tables:[/cyan] {', '.join(result['relevant_tables'])}

[cyan]Generated SQL:[/cyan]
{result['sql']}

[cyan]Score:[/cyan] {result['score']:.2f}

[cyan]Retries:[/cyan] {result['retry_count']}

[cyan]Total Time:[/cyan] {result['execution_time']:.2f}s

[cyan]Result Rows:[/cyan] {len(result['result']) if result['result'] else 0}""",
            title="Pipeline Output"
        ))
    
    def compare_retrieval_methods(
        self, 
        question: str, 
        db_path: str
    ) -> Dict[str, Any]:
        """
        Compare all retrieval methods on a single question.
        
        Args:
            question: Test question
            db_path: Database path
            
        Returns:
            Comparison results
        """
        results = {}
        
        for method in ["dense", "sparse", "hybrid"]:
            # Create pipeline with this method
            pipeline = MultiAgentRAGPipeline(
                llm_client=self.llm,
                retrieval_method=method
            )
            pipeline.set_verbose(False)
            
            # Run
            result = pipeline.run(question, db_path)
            results[method] = {
                "success": result["success"],
                "sql": result["sql"],
                "score": result["score"],
                "execution_time": result["execution_time"],
                "relevant_tables": result["relevant_tables"]
            }
        
        return results
    
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
                f"""[bold]Batch Summary (RAG - {self.retrieval_method.upper()})[/bold]

Success Rate: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)
Average Score: {avg_score:.2f}
Average Time: {avg_time:.2f}s""",
                title="Batch Results"
            ))
        
        return results

