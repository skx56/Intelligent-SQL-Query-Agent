"""
Planner Agent - Analyzes user questions and creates query execution plans
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from utils.llm_client import OllamaClient


class PlannerAgent(BaseAgent):
    """
    Analyzes user's natural language question and determines:
    - Query type (SELECT, COUNT, AGGREGATE, JOIN, etc.)
    - Required operations
    - Execution strategy
    """
    
    QUERY_TYPES = [
        "SELECT",      # Simple column selection
        "COUNT",       # Counting records
        "AGGREGATE",   # SUM, AVG, MIN, MAX operations
        "JOIN",        # Multi-table queries
        "GROUPBY",     # Grouped aggregations
        "ORDERBY",     # Sorted results
        "FILTER",      # WHERE clause queries
        "SUBQUERY",    # Nested queries
        "COMPLEX"      # Multiple operations combined
    ]
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize Planner Agent.
        
        Args:
            llm_client: Ollama client for LLM operations
        """
        super().__init__(
            name="Planner Agent",
            description="Analyzes questions and creates execution plans"
        )
        self.llm = llm_client or OllamaClient()
    
    def _create_planning_prompt(self, question: str) -> str:
        """Create prompt for query planning."""
        return f"""Analyze the following natural language question and create a query plan.

Question: {question}

Determine:
1. Query Type: One of {self.QUERY_TYPES}
2. Required Tables: List tables likely needed
3. Required Columns: List columns likely needed
4. Operations: List SQL operations needed (SELECT, WHERE, JOIN, GROUP BY, etc.)
5. Complexity: Rate from 1-5 (1=simple, 5=very complex)

Respond in this exact JSON format:
{{
    "query_type": "<primary query type>",
    "required_tables": ["table1", "table2"],
    "required_columns": ["col1", "col2"],
    "operations": ["SELECT", "WHERE", "JOIN"],
    "complexity": 3,
    "reasoning": "Brief explanation of the plan"
}}

Only respond with the JSON, no other text."""

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process question and create execution plan.
        
        Args:
            state: Current pipeline state with 'question' key
            
        Returns:
            Updated state with 'query_type' and 'plan'
        """
        question = state.get("question", "")
        
        if not question:
            state["errors"] = state.get("errors", []) + ["No question provided"]
            return state
        
        self.log(f"Analyzing question: {question[:50]}...")
        
        # Generate plan using LLM
        prompt = self._create_planning_prompt(question)
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are a SQL query planning expert. Analyze questions and output JSON plans.",
                temperature=0.1
            )
            
            plan = self.llm.extract_json(response)
            
            if plan:
                state["query_type"] = plan.get("query_type", "SELECT")
                state["plan"] = plan
                self.log(f"Plan created: {plan.get('query_type')} with complexity {plan.get('complexity')}")
            else:
                # Fallback to simple analysis
                state["query_type"] = self._simple_query_type_detection(question)
                state["plan"] = {
                    "query_type": state["query_type"],
                    "complexity": 2,
                    "reasoning": "Fallback analysis"
                }
                self.log("Using fallback query type detection")
                
        except Exception as e:
            state["errors"] = state.get("errors", []) + [f"Planning error: {str(e)}"]
            state["query_type"] = self._simple_query_type_detection(question)
            state["plan"] = {"query_type": state["query_type"], "error": str(e)}
        
        return state
    
    def _simple_query_type_detection(self, question: str) -> str:
        """
        Simple rule-based query type detection as fallback.
        
        Args:
            question: User question
            
        Returns:
            Detected query type
        """
        question_lower = question.lower()
        
        # Keywords for each query type
        type_keywords = {
            "COUNT": ["how many", "count", "number of", "total number"],
            "AGGREGATE": ["average", "avg", "sum", "total", "maximum", "max", "minimum", "min"],
            "GROUPBY": ["each", "per", "by category", "grouped", "for each"],
            "ORDERBY": ["top", "highest", "lowest", "most", "least", "ranked", "sorted"],
            "JOIN": ["and their", "along with", "with their", "related", "associated"],
            "FILTER": ["where", "which", "that have", "with", "whose"],
        }
        
        for query_type, keywords in type_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return query_type
        
        return "SELECT"
    
    def analyze_complexity(self, question: str) -> int:
        """
        Estimate query complexity from question.
        
        Args:
            question: User question
            
        Returns:
            Complexity score 1-5
        """
        complexity = 1
        question_lower = question.lower()
        
        # Increase complexity for certain patterns
        complexity_indicators = [
            (["and", "also", "as well as"], 1),
            (["join", "combine", "merge"], 1),
            (["group by", "for each", "per"], 1),
            (["subquery", "nested", "within"], 2),
            (["having", "where", "filter"], 1),
            (["order by", "sort", "rank"], 1),
        ]
        
        for keywords, score in complexity_indicators:
            if any(kw in question_lower for kw in keywords):
                complexity += score
        
        return min(complexity, 5)

