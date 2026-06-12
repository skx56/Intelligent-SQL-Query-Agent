"""
Base Agent class for all agents in the system
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from rich.console import Console

console = Console()


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    All agents share common functionality and must implement
    the process method for their specific task.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self.verbose = False
    
    def set_verbose(self, verbose: bool):
        """Enable or disable verbose output."""
        self.verbose = verbose
    
    def log(self, message: str, style: str = "dim"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            console.print(f"[{style}][{self.name}] {message}[/{style}]")
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state dictionary
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"


class AgentState:
    """
    Shared state object passed between agents in the pipeline.
    """
    
    def __init__(self):
        # Input
        self.question: str = ""
        self.db_path: str = ""
        
        # Planner output
        self.query_type: str = ""
        self.plan: Dict[str, Any] = {}
        
        # Schema output
        self.schema: str = ""
        self.relevant_tables: list = []
        self.foreign_keys: Dict = {}
        
        # SQL output
        self.generated_sql: str = ""
        self.sql_explanation: str = ""
        
        # Executor output
        self.execution_result: Any = None
        self.execution_error: Optional[str] = None
        self.execution_success: bool = False
        
        # Evaluator output
        self.score: float = 0.0
        self.evaluation_details: Dict[str, Any] = {}
        
        # Metadata
        self.errors: list = []
        self.retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "question": self.question,
            "db_path": self.db_path,
            "query_type": self.query_type,
            "plan": self.plan,
            "schema": self.schema,
            "relevant_tables": self.relevant_tables,
            "foreign_keys": self.foreign_keys,
            "generated_sql": self.generated_sql,
            "sql_explanation": self.sql_explanation,
            "execution_result": self.execution_result,
            "execution_error": self.execution_error,
            "execution_success": self.execution_success,
            "score": self.score,
            "evaluation_details": self.evaluation_details,
            "errors": self.errors,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create state from dictionary."""
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state

