"""
Evaluator Agent - Evaluates SQL query quality and correctness
"""

from typing import Any, Dict, List, Optional
import re

from .base_agent import BaseAgent
from utils.llm_client import OllamaClient


class EvaluatorAgent(BaseAgent):
    """
    Evaluates generated SQL queries and execution results.
    
    Evaluation criteria:
    - Syntax correctness
    - Execution success
    - Result accuracy (vs ground truth if available)
    - Query efficiency
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize Evaluator Agent.
        
        Args:
            llm_client: Ollama client for LLM-based evaluation
        """
        super().__init__(
            name="Evaluator Agent",
            description="Evaluates SQL quality and correctness"
        )
        self.llm = llm_client or OllamaClient()
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the generated SQL and execution results.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with 'score' and 'evaluation_details'
        """
        sql = state.get("generated_sql", "")
        execution_success = state.get("execution_success", False)
        execution_result = state.get("execution_result")
        execution_error = state.get("execution_error")
        question = state.get("question", "")
        
        self.log("Evaluating query and results...")
        
        evaluation = {
            "syntax_score": 0.0,
            "execution_score": 0.0,
            "semantic_score": 0.0,
            "efficiency_score": 0.0,
            "overall_score": 0.0,
            "feedback": []
        }
        
        # 1. Syntax evaluation
        syntax_eval = self._evaluate_syntax(sql)
        evaluation["syntax_score"] = syntax_eval["score"]
        evaluation["feedback"].extend(syntax_eval["feedback"])
        
        # 2. Execution evaluation
        exec_eval = self._evaluate_execution(execution_success, execution_error)
        evaluation["execution_score"] = exec_eval["score"]
        evaluation["feedback"].extend(exec_eval["feedback"])
        
        # 3. Semantic evaluation (does the result answer the question?)
        if execution_success and execution_result is not None:
            semantic_eval = self._evaluate_semantics(question, sql, execution_result)
            evaluation["semantic_score"] = semantic_eval["score"]
            evaluation["feedback"].extend(semantic_eval["feedback"])
        
        # 4. Efficiency evaluation
        efficiency_eval = self._evaluate_efficiency(sql)
        evaluation["efficiency_score"] = efficiency_eval["score"]
        evaluation["feedback"].extend(efficiency_eval["feedback"])
        
        # Calculate overall score (weighted average)
        weights = {
            "syntax": 0.15,
            "execution": 0.35,
            "semantic": 0.35,
            "efficiency": 0.15
        }
        
        evaluation["overall_score"] = (
            evaluation["syntax_score"] * weights["syntax"] +
            evaluation["execution_score"] * weights["execution"] +
            evaluation["semantic_score"] * weights["semantic"] +
            evaluation["efficiency_score"] * weights["efficiency"]
        )
        
        state["score"] = evaluation["overall_score"]
        state["evaluation_details"] = evaluation
        
        self.log(f"Evaluation complete. Score: {evaluation['overall_score']:.2f}")
        
        return state
    
    def _evaluate_syntax(self, sql: str) -> Dict[str, Any]:
        """
        Evaluate SQL syntax quality.
        
        Args:
            sql: SQL query
            
        Returns:
            Evaluation result
        """
        if not sql:
            return {"score": 0.0, "feedback": ["No SQL query provided"]}
        
        score = 1.0
        feedback = []
        
        # Check for basic SQL structure
        sql_upper = sql.upper()
        
        # Check if it starts with a valid keyword
        valid_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']
        if not any(sql_upper.strip().startswith(kw) for kw in valid_keywords):
            score -= 0.5
            feedback.append("Query doesn't start with a valid SQL keyword")
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            score -= 0.3
            feedback.append("Unbalanced parentheses")
        
        # Check for proper quoting
        if sql.count("'") % 2 != 0:
            score -= 0.2
            feedback.append("Unbalanced single quotes")
        
        # Check for semicolon
        if not sql.strip().endswith(';'):
            score -= 0.1
            feedback.append("Query should end with semicolon")
        
        # Bonus for good practices
        if 'AS ' in sql_upper and 'JOIN' in sql_upper:
            score = min(1.0, score + 0.1)
            feedback.append("Good: Uses aliases with JOINs")
        
        return {"score": max(0.0, score), "feedback": feedback}
    
    def _evaluate_execution(
        self, 
        success: bool, 
        error: Optional[str]
    ) -> Dict[str, Any]:
        """
        Evaluate query execution result.
        
        Args:
            success: Whether execution was successful
            error: Error message if any
            
        Returns:
            Evaluation result
        """
        if success:
            return {
                "score": 1.0, 
                "feedback": ["Query executed successfully"]
            }
        
        score = 0.0
        feedback = []
        
        if error:
            feedback.append(f"Execution failed: {error}")
            
            # Partial credit for common fixable errors
            error_lower = error.lower()
            if "no such table" in error_lower:
                score = 0.2
                feedback.append("Table name might be incorrect")
            elif "no such column" in error_lower:
                score = 0.3
                feedback.append("Column name might be incorrect")
            elif "syntax error" in error_lower:
                score = 0.1
                feedback.append("SQL syntax needs correction")
        
        return {"score": score, "feedback": feedback}
    
    def _evaluate_semantics(
        self, 
        question: str, 
        sql: str, 
        result: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate if the query semantically answers the question.
        
        Args:
            question: Original question
            sql: Generated SQL
            result: Execution result
            
        Returns:
            Evaluation result
        """
        score = 0.5  # Base score for successful execution with results
        feedback = []
        
        question_lower = question.lower()
        sql_upper = sql.upper()
        
        # Check for count questions
        if any(kw in question_lower for kw in ['how many', 'count', 'number of']):
            if 'COUNT(' in sql_upper:
                score += 0.25
                feedback.append("Correctly uses COUNT for counting question")
            else:
                score -= 0.25
                feedback.append("Question asks for count but query doesn't use COUNT")
        
        # Check for aggregate questions
        aggregate_keywords = {
            'average': 'AVG(',
            'avg': 'AVG(',
            'sum': 'SUM(',
            'total': 'SUM(',
            'maximum': 'MAX(',
            'max': 'MAX(',
            'minimum': 'MIN(',
            'min': 'MIN('
        }
        
        for kw, agg_func in aggregate_keywords.items():
            if kw in question_lower:
                if agg_func in sql_upper:
                    score += 0.2
                    feedback.append(f"Correctly uses {agg_func[:-1]} for {kw} question")
                break
        
        # Check result validity
        if result:
            if len(result) > 0:
                score += 0.15
                feedback.append(f"Query returned {len(result)} results")
        else:
            feedback.append("Query returned no results")
        
        return {"score": min(1.0, score), "feedback": feedback}
    
    def _evaluate_efficiency(self, sql: str) -> Dict[str, Any]:
        """
        Evaluate query efficiency.
        
        Args:
            sql: SQL query
            
        Returns:
            Evaluation result
        """
        score = 1.0
        feedback = []
        
        sql_upper = sql.upper()
        
        # Check for SELECT *
        if 'SELECT *' in sql_upper:
            score -= 0.2
            feedback.append("Consider selecting specific columns instead of *")
        
        # Check for missing WHERE in large table operations
        if 'DELETE' in sql_upper or 'UPDATE' in sql_upper:
            if 'WHERE' not in sql_upper:
                score -= 0.5
                feedback.append("UPDATE/DELETE without WHERE clause is risky")
        
        # Check for DISTINCT
        if 'DISTINCT' in sql_upper:
            feedback.append("Uses DISTINCT - ensure it's necessary")
        
        # Check for subqueries (might be inefficient)
        subquery_count = sql_upper.count('SELECT') - 1
        if subquery_count > 2:
            score -= 0.2
            feedback.append("Multiple subqueries may impact performance")
        
        # Bonus for LIMIT
        if 'LIMIT' in sql_upper:
            score = min(1.0, score + 0.1)
            feedback.append("Good: Uses LIMIT to restrict results")
        
        return {"score": max(0.0, score), "feedback": feedback}
    
    def compare_with_ground_truth(
        self,
        generated_sql: str,
        ground_truth_sql: str,
        generated_result: List[Dict[str, Any]],
        ground_truth_result: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare generated SQL with ground truth.
        
        Args:
            generated_sql: Generated SQL query
            ground_truth_sql: Ground truth SQL query
            generated_result: Execution result of generated query
            ground_truth_result: Execution result of ground truth query
            
        Returns:
            Comparison metrics
        """
        # Normalize SQL for comparison
        def normalize_sql(sql):
            sql = sql.upper()
            sql = re.sub(r'\s+', ' ', sql)
            sql = sql.strip().rstrip(';')
            return sql
        
        gen_normalized = normalize_sql(generated_sql)
        gt_normalized = normalize_sql(ground_truth_sql)
        
        # Exact match
        exact_sql_match = gen_normalized == gt_normalized
        
        # Result comparison
        def normalize_results(results):
            if not results:
                return []
            return sorted([tuple(sorted(r.items())) for r in results])
        
        gen_results_norm = normalize_results(generated_result)
        gt_results_norm = normalize_results(ground_truth_result)
        
        execution_match = gen_results_norm == gt_results_norm
        
        # Calculate result overlap
        if generated_result and ground_truth_result:
            gen_set = set(map(str, gen_results_norm))
            gt_set = set(map(str, gt_results_norm))
            
            if gt_set:
                recall = len(gen_set & gt_set) / len(gt_set)
            else:
                recall = 1.0 if not gen_set else 0.0
                
            if gen_set:
                precision = len(gen_set & gt_set) / len(gen_set)
            else:
                precision = 1.0 if not gt_set else 0.0
                
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        else:
            recall = 1.0 if (not generated_result and not ground_truth_result) else 0.0
            precision = recall
            f1 = recall
        
        return {
            "exact_sql_match": exact_sql_match,
            "execution_match": execution_match,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
    
    def evaluate_direct(
        self,
        sql: str,
        question: str,
        execution_success: bool,
        execution_result: Optional[List[Dict[str, Any]]] = None,
        execution_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Direct evaluation without state management.
        
        Args:
            sql: SQL query
            question: Original question
            execution_success: Whether execution succeeded
            execution_result: Query results
            execution_error: Error message
            
        Returns:
            Evaluation results
        """
        state = {
            "generated_sql": sql,
            "question": question,
            "execution_success": execution_success,
            "execution_result": execution_result,
            "execution_error": execution_error
        }
        
        result = self.process(state)
        
        return {
            "score": result["score"],
            "details": result["evaluation_details"]
        }

