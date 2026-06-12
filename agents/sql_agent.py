"""
SQL Agent - Generates SQL queries from natural language using LLM

Enhanced with:
- Few-shot examples for better SQL generation
- SQLglot for SQL validation and optimization
- Improved prompts with database-specific rules
"""

from typing import Any, Dict, List, Optional
import re

from .base_agent import BaseAgent
from utils.llm_client import OllamaClient
from config.config import SQL_MAX_RETRIES

# SQLglot for SQL post-processing
try:
    import sqlglot
    SQLGLOT_AVAILABLE = True
except ImportError:
    SQLGLOT_AVAILABLE = False


# Few-shot examples for common query patterns
FEW_SHOT_EXAMPLES = """
EXAMPLES:

Example 1 - Simple COUNT:
Question: How many countries are there?
SQL: SELECT COUNT(*) FROM country;

Example 2 - COUNT with condition:
Question: How many countries have population over 1 million?
SQL: SELECT COUNT(*) FROM country WHERE Population > 1000000;

Example 3 - Aggregation:
Question: What is the total population of countries in Asia?
SQL: SELECT SUM(Population) FROM country WHERE Continent = 'Asia';

Example 4 - Finding specific values:
Question: What are the names of countries that became independent after 1990?
SQL: SELECT Name FROM country WHERE IndepYear > 1990;

Example 5 - JOIN query:
Question: What languages are spoken in Germany?
SQL: SELECT cl.Language FROM countrylanguage cl JOIN country c ON cl.CountryCode = c.Code WHERE c.Name = 'Germany';

Example 6 - GROUP BY with aggregation:
Question: How many countries are in each continent?
SQL: SELECT Continent, COUNT(*) as CountryCount FROM country GROUP BY Continent;

Example 7 - ORDER BY with LIMIT:
Question: What are the top 5 most populous countries?
SQL: SELECT Name, Population FROM country ORDER BY Population DESC LIMIT 5;

Example 8 - Multiple conditions:
Question: What are the republics in Europe with population over 10 million?
SQL: SELECT Name FROM country WHERE Continent = 'Europe' AND GovernmentForm = 'Republic' AND Population > 10000000;
"""


class SQLAgent(BaseAgent):
    """
    Generates SQL queries from natural language questions using LLM.
    
    Takes schema information and query plan to generate accurate SQL.
    """
    
    def __init__(self, llm_client: OllamaClient = None):
        """
        Initialize SQL Agent.
        
        Args:
            llm_client: Ollama client for LLM operations
        """
        super().__init__(
            name="SQL Agent",
            description="Generates SQL queries from natural language"
        )
        self.llm = llm_client or OllamaClient()
        self.max_retries = SQL_MAX_RETRIES
    
    def _create_sql_prompt(
        self, 
        question: str, 
        schema: str, 
        plan: Dict[str, Any],
        error_feedback: Optional[str] = None
    ) -> str:
        """
        Create enhanced prompt for SQL generation with few-shot examples.
        
        Args:
            question: User question
            schema: Database schema
            plan: Query plan from planner
            error_feedback: Previous error for retry
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "Generate a SQLite query to answer the following question.",
            "",
            "=" * 50,
            "DATABASE SCHEMA:",
            "=" * 50,
            schema,
            "",
        ]
        
        # Add few-shot examples
        prompt_parts.extend([
            "=" * 50,
            FEW_SHOT_EXAMPLES,
            "=" * 50,
            ""
        ])
        
        if plan:
            prompt_parts.extend([
                "QUERY ANALYSIS:",
                f"- Query Type: {plan.get('query_type', 'SELECT')}",
                f"- Complexity: {plan.get('complexity', 'simple')}",
                f"- Required Tables: {', '.join(plan.get('required_tables', []))}",
                ""
            ])
        
        if error_feedback:
            prompt_parts.extend([
                "⚠️ PREVIOUS ERROR - Please fix:",
                error_feedback,
                ""
            ])
        
        prompt_parts.extend([
            "=" * 50,
            "YOUR TASK:",
            "=" * 50,
            f"Question: {question}",
            "",
            "Generate ONLY the SQL query (no explanations):",
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_system_prompt(self) -> str:
        """Create enhanced system prompt for SQL generation."""
        return """You are an expert SQLite query generator. Convert natural language questions into valid, optimized SQLite queries.

CRITICAL RULES:
1. Generate ONLY the SQL query - no explanations, no markdown
2. Use EXACT column and table names from the schema (case-sensitive!)
3. For simple counts, use COUNT(*) - avoid COUNT(DISTINCT) unless duplicates are possible
4. NEVER add unnecessary JOINs - only join tables when you need columns from multiple tables
5. String comparisons are CASE-SENSITIVE in SQLite - use exact values from schema
6. Always end queries with semicolon
7. Use table aliases (e.g., c for country) when joining tables
8. For aggregations without grouping, don't add GROUP BY unnecessarily

COMMON MISTAKES TO AVOID:
- Don't join tables unless the question requires data from multiple tables
- Don't use 'republic' when the value is 'Republic' (case matters!)
- Don't add WHERE conditions that weren't asked for
- Don't return extra columns beyond what's asked

OUTPUT FORMAT:
Return ONLY the SQL query, nothing else. No explanations, no markdown code blocks."""
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SQL query from question and schema.
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated state with 'generated_sql' and 'sql_explanation'
        """
        question = state.get("question", "")
        schema = state.get("schema", "")
        plan = state.get("plan", {})
        
        if not question:
            state["errors"] = state.get("errors", []) + ["No question provided"]
            return state
        
        if not schema:
            state["errors"] = state.get("errors", []) + ["No schema provided"]
            return state
        
        self.log(f"Generating SQL for: {question[:50]}...")
        
        error_feedback = None
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                prompt = self._create_sql_prompt(question, schema, plan, error_feedback)
                
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=self._create_system_prompt(),
                    temperature=0.1
                )
                
                # Extract SQL from response
                sql = self.llm.extract_sql(response)
                sql = self._clean_sql(sql)
                
                # Validate SQL syntax
                validation_result = self._validate_sql(sql)
                
                if validation_result["valid"]:
                    state["generated_sql"] = sql
                    state["sql_explanation"] = self._generate_explanation(sql, question)
                    state["retry_count"] = retry_count
                    self.log(f"SQL generated successfully after {retry_count} retries")
                    return state
                else:
                    error_feedback = validation_result["error"]
                    retry_count += 1
                    self.log(f"Validation failed, retry {retry_count}: {error_feedback}")
                    
            except Exception as e:
                error_feedback = str(e)
                retry_count += 1
                self.log(f"Generation error, retry {retry_count}: {e}")
        
        # Max retries exceeded
        state["errors"] = state.get("errors", []) + [f"SQL generation failed after {self.max_retries} attempts"]
        state["generated_sql"] = ""
        state["retry_count"] = retry_count
        
        return state
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean, normalize and optimize SQL query using SQLglot.
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Cleaned and optimized SQL query
        """
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Remove markdown code block markers
        sql = re.sub(r'^```\w*\n?', '', sql)
        sql = re.sub(r'\n?```$', '', sql)
        sql = re.sub(r'^```', '', sql)
        sql = re.sub(r'```$', '', sql)
        
        # Remove any text before SELECT/INSERT/UPDATE/DELETE
        for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']:
            if keyword in sql.upper():
                idx = sql.upper().find(keyword)
                sql = sql[idx:]
                break
        
        # Ensure single semicolon at end
        sql = sql.rstrip(';').strip() + ';'
        
        # Normalize whitespace
        sql = re.sub(r'\s+', ' ', sql)
        
        # Try to optimize with SQLglot
        if SQLGLOT_AVAILABLE:
            sql = self._optimize_with_sqlglot(sql)
        
        return sql
    
    def _optimize_with_sqlglot(self, sql: str) -> str:
        """
        Optimize SQL using SQLglot.
        
        Args:
            sql: SQL query to optimize
            
        Returns:
            Optimized SQL query
        """
        try:
            # Parse the SQL
            parsed = sqlglot.parse_one(sql, dialect="sqlite")
            
            # Format nicely
            optimized = parsed.sql(dialect="sqlite", pretty=False)
            
            # Ensure semicolon
            if not optimized.endswith(';'):
                optimized += ';'
            
            return optimized
        except Exception as e:
            self.log(f"SQLglot optimization failed: {e}, using original SQL")
            return sql
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL syntax using SQLglot and basic checks.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Validation result with 'valid' and 'error' keys
        """
        if not sql or sql == ';':
            return {"valid": False, "error": "Empty SQL query"}
        
        # Check for basic SQL structure
        sql_upper = sql.upper()
        valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
        
        if not any(sql_upper.strip().startswith(keyword) for keyword in valid_starts):
            return {"valid": False, "error": "Query must start with a valid SQL keyword"}
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            return {"valid": False, "error": "Unbalanced parentheses"}
        
        # Check for balanced quotes
        single_quotes = sql.count("'")
        if single_quotes % 2 != 0:
            return {"valid": False, "error": "Unbalanced single quotes"}
        
        # Use SQLglot for advanced validation
        if SQLGLOT_AVAILABLE:
            try:
                sqlglot.parse_one(sql, dialect="sqlite")
            except sqlglot.errors.ParseError as e:
                return {"valid": False, "error": f"SQL syntax error: {str(e)[:100]}"}
            except Exception as e:
                # Don't fail on other errors, just log
                self.log(f"SQLglot validation warning: {e}")
        
        return {"valid": True, "error": None}
    
    def _generate_explanation(self, sql: str, question: str) -> str:
        """
        Generate a brief explanation of the SQL query.
        
        Args:
            sql: Generated SQL query
            question: Original question
            
        Returns:
            Explanation string
        """
        # Simple pattern-based explanation
        sql_upper = sql.upper()
        
        explanations = []
        
        if 'SELECT' in sql_upper:
            if 'COUNT(' in sql_upper:
                explanations.append("Counts records")
            elif 'AVG(' in sql_upper:
                explanations.append("Calculates average")
            elif 'SUM(' in sql_upper:
                explanations.append("Calculates sum")
            elif 'MAX(' in sql_upper:
                explanations.append("Finds maximum")
            elif 'MIN(' in sql_upper:
                explanations.append("Finds minimum")
            else:
                explanations.append("Retrieves data")
        
        if 'JOIN' in sql_upper:
            explanations.append("joins multiple tables")
        
        if 'WHERE' in sql_upper:
            explanations.append("with filtering conditions")
        
        if 'GROUP BY' in sql_upper:
            explanations.append("grouped by category")
        
        if 'ORDER BY' in sql_upper:
            explanations.append("sorted by specified column")
        
        if 'LIMIT' in sql_upper:
            explanations.append("limited to specific number of results")
        
        return " ".join(explanations) if explanations else "SQL query generated"
    
    def generate_sql_direct(
        self, 
        question: str, 
        schema: str
    ) -> str:
        """
        Direct SQL generation without state management.
        
        Args:
            question: User question
            schema: Database schema
            
        Returns:
            Generated SQL query
        """
        state = {
            "question": question,
            "schema": schema,
            "plan": {}
        }
        
        result = self.process(state)
        return result.get("generated_sql", "")

