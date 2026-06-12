"""
SQL Utilities - SQL parsing, normalization and comparison using sqlglot
"""

import sqlglot
from sqlglot import exp
from typing import Optional, Tuple
from rich.console import Console

console = Console()


def normalize_sql(sql: str, dialect: str = "sqlite") -> str:
    """
    Normalize SQL query for comparison.
    
    - Converts to uppercase
    - Standardizes whitespace
    - Normalizes quotes
    
    Args:
        sql: SQL query string
        dialect: SQL dialect (sqlite, mysql, postgres, etc.)
        
    Returns:
        Normalized SQL string
    """
    try:
        # Parse and regenerate
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        normalized = parsed.sql(dialect=dialect, normalize=True, pretty=False)
        return normalized.upper().strip()
    except Exception as e:
        # Fallback to simple normalization
        return sql.upper().replace('"', "'").strip()


def parse_sql(sql: str, dialect: str = "sqlite"):
    """
    Parse SQL query into AST.
    
    Args:
        sql: SQL query string
        dialect: SQL dialect
        
    Returns:
        Parsed expression or None
    """
    try:
        return sqlglot.parse_one(sql, dialect=dialect)
    except Exception as e:
        console.print(f"[dim]SQL parse error: {e}[/dim]")
        return None


def compare_sql(sql1: str, sql2: str, dialect: str = "sqlite") -> dict:
    """
    Compare two SQL queries.
    
    Returns:
        dict with comparison results
    """
    result = {
        "exact_match": False,
        "normalized_match": False,
        "semantic_similar": False,
        "sql1_normalized": "",
        "sql2_normalized": "",
        "differences": []
    }
    
    # Exact match
    result["exact_match"] = sql1.strip() == sql2.strip()
    
    # Normalized match
    try:
        norm1 = normalize_sql(sql1, dialect)
        norm2 = normalize_sql(sql2, dialect)
        result["sql1_normalized"] = norm1
        result["sql2_normalized"] = norm2
        result["normalized_match"] = norm1 == norm2
    except Exception:
        pass
    
    # Semantic similarity check
    try:
        parsed1 = parse_sql(sql1, dialect)
        parsed2 = parse_sql(sql2, dialect)
        
        if parsed1 and parsed2:
            # Check if same query type
            same_type = type(parsed1) == type(parsed2)
            
            # Check tables used
            tables1 = set(t.name for t in parsed1.find_all(exp.Table))
            tables2 = set(t.name for t in parsed2.find_all(exp.Table))
            same_tables = tables1 == tables2
            
            # Check columns selected
            cols1 = set(c.name for c in parsed1.find_all(exp.Column) if c.name)
            cols2 = set(c.name for c in parsed2.find_all(exp.Column) if c.name)
            
            # Semantic similarity score
            result["semantic_similar"] = same_type and same_tables
            
            if tables1 != tables2:
                result["differences"].append(f"Tables: {tables1} vs {tables2}")
            if cols1 != cols2:
                result["differences"].append(f"Columns: {cols1} vs {cols2}")
                
    except Exception as e:
        result["differences"].append(f"Parse error: {e}")
    
    return result


def extract_tables(sql: str, dialect: str = "sqlite") -> list:
    """Extract table names from SQL."""
    try:
        parsed = parse_sql(sql, dialect)
        if parsed:
            return [t.name for t in parsed.find_all(exp.Table)]
    except Exception:
        pass
    return []


def extract_columns(sql: str, dialect: str = "sqlite") -> list:
    """Extract column names from SQL."""
    try:
        parsed = parse_sql(sql, dialect)
        if parsed:
            return [c.name for c in parsed.find_all(exp.Column) if c.name]
    except Exception:
        pass
    return []


def get_query_type(sql: str) -> str:
    """Get the type of SQL query."""
    sql_upper = sql.strip().upper()
    
    if sql_upper.startswith("SELECT"):
        if "COUNT(" in sql_upper:
            return "COUNT"
        if "AVG(" in sql_upper or "SUM(" in sql_upper or "MAX(" in sql_upper or "MIN(" in sql_upper:
            return "AGGREGATE"
        if "GROUP BY" in sql_upper:
            return "GROUPBY"
        if "JOIN" in sql_upper:
            return "JOIN"
        return "SELECT"
    elif sql_upper.startswith("INSERT"):
        return "INSERT"
    elif sql_upper.startswith("UPDATE"):
        return "UPDATE"
    elif sql_upper.startswith("DELETE"):
        return "DELETE"
    
    return "UNKNOWN"


def format_sql(sql: str, dialect: str = "sqlite") -> str:
    """Format SQL query for display."""
    try:
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        return parsed.sql(dialect=dialect, pretty=True)
    except Exception:
        return sql


# ============================================================
# SPIDER BENCHMARK METRICS
# ============================================================

def exact_set_match(result1: list, result2: list) -> bool:
    """
    Exact Set Match - Order doesn't matter, are result sets the same?
    
    Spider's official metric. Returns True if content is the same
    even if row order differs.
    """
    if not result1 and not result2:
        return True
    if not result1 or not result2:
        return False
    
    # Convert to sets of tuples for comparison
    def to_set(results):
        return set(
            tuple(sorted(str(v) for v in row.values()) if isinstance(row, dict) else tuple(str(x) for x in row))
            for row in results
        )
    
    set1 = to_set(result1)
    set2 = to_set(result2)
    
    return set1 == set2


def execution_accuracy(gen_sql: str, gold_sql: str, db_path: str) -> dict:
    """
    Execution Accuracy - Does SQL execute without errors + is result correct?
    
    Returns:
        dict with 'valid', 'correct', 'error' keys
    """
    import sqlite3
    
    result = {
        "valid": False,      # Did SQL execute?
        "correct": False,    # Is result correct?
        "error": None,
        "gen_result": None,
        "gold_result": None
    }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute gold SQL
        cursor.execute(gold_sql)
        gold_rows = [dict(row) for row in cursor.fetchall()]
        result["gold_result"] = gold_rows
        
        # Execute generated SQL
        try:
            cursor.execute(gen_sql)
            gen_rows = [dict(row) for row in cursor.fetchall()]
            result["gen_result"] = gen_rows
            result["valid"] = True
            
            # Compare results (exact set match)
            result["correct"] = exact_set_match(gen_rows, gold_rows)
            
        except sqlite3.Error as e:
            result["error"] = f"Generated SQL error: {e}"
            result["valid"] = False
        
        conn.close()
        
    except Exception as e:
        result["error"] = f"Database error: {e}"
    
    return result


def component_matching(gen_sql: str, gold_sql: str, dialect: str = "sqlite") -> dict:
    """
    Component Matching - Compare SQL components
    
    Checks SELECT, FROM, WHERE, GROUP BY, ORDER BY parts separately.
    """
    result = {
        "select_match": False,
        "from_match": False,
        "where_match": False,
        "groupby_match": False,
        "orderby_match": False,
        "overall_score": 0.0,
        "details": {}
    }
    
    try:
        gen_parsed = sqlglot.parse_one(gen_sql, dialect=dialect)
        gold_parsed = sqlglot.parse_one(gold_sql, dialect=dialect)
        
        # SELECT comparison
        gen_select = set(str(s) for s in gen_parsed.find_all(exp.Select))
        gold_select = set(str(s) for s in gold_parsed.find_all(exp.Select))
        
        # Tables (FROM)
        gen_tables = set(t.name.upper() for t in gen_parsed.find_all(exp.Table))
        gold_tables = set(t.name.upper() for t in gold_parsed.find_all(exp.Table))
        result["from_match"] = gen_tables == gold_tables
        result["details"]["tables"] = {"gen": list(gen_tables), "gold": list(gold_tables)}
        
        # WHERE conditions
        gen_where = gen_parsed.find(exp.Where)
        gold_where = gold_parsed.find(exp.Where)
        if gen_where and gold_where:
            # Simple comparison - column names
            gen_cols = set(c.name.upper() for c in gen_where.find_all(exp.Column) if c.name)
            gold_cols = set(c.name.upper() for c in gold_where.find_all(exp.Column) if c.name)
            result["where_match"] = gen_cols == gold_cols
            result["details"]["where_cols"] = {"gen": list(gen_cols), "gold": list(gold_cols)}
        elif not gen_where and not gold_where:
            result["where_match"] = True
        
        # GROUP BY
        gen_group = gen_parsed.find(exp.Group)
        gold_group = gold_parsed.find(exp.Group)
        if gen_group and gold_group:
            gen_group_cols = set(c.name.upper() for c in gen_group.find_all(exp.Column) if c.name)
            gold_group_cols = set(c.name.upper() for c in gold_group.find_all(exp.Column) if c.name)
            result["groupby_match"] = gen_group_cols == gold_group_cols
        elif not gen_group and not gold_group:
            result["groupby_match"] = True
        
        # ORDER BY
        gen_order = gen_parsed.find(exp.Order)
        gold_order = gold_parsed.find(exp.Order)
        if gen_order and gold_order:
            # Compare ORDER BY columns (similar to GROUP BY)
            gen_order_cols = set(c.name.upper() for c in gen_order.find_all(exp.Column) if c.name)
            gold_order_cols = set(c.name.upper() for c in gold_order.find_all(exp.Column) if c.name)
            result["orderby_match"] = gen_order_cols == gold_order_cols
            result["details"]["orderby_cols"] = {"gen": list(gen_order_cols), "gold": list(gold_order_cols)}
        elif not gen_order and not gold_order:
            result["orderby_match"] = True
        
        # Aggregate functions check
        gen_aggs = set(type(a).__name__ for a in gen_parsed.find_all(exp.AggFunc))
        gold_aggs = set(type(a).__name__ for a in gold_parsed.find_all(exp.AggFunc))
        result["details"]["aggregates"] = {"gen": list(gen_aggs), "gold": list(gold_aggs)}
        result["select_match"] = gen_aggs == gold_aggs
        
        # Overall score
        matches = [result["select_match"], result["from_match"], result["where_match"], result["groupby_match"], result["orderby_match"]]
        result["overall_score"] = sum(matches) / len(matches)
        
    except Exception as e:
        result["details"]["error"] = str(e)
    
    return result


def full_evaluation(gen_sql: str, gold_sql: str, db_path: str) -> dict:
    """
    Full evaluation - Calculate all metrics
    """
    result = {
        "execution_accuracy": {},
        "component_matching": {},
        "sql_comparison": {}
    }
    
    # 1. Execution Accuracy
    result["execution_accuracy"] = execution_accuracy(gen_sql, gold_sql, db_path)
    
    # 2. Component Matching
    result["component_matching"] = component_matching(gen_sql, gold_sql)
    
    # 3. SQL Comparison (existing)
    result["sql_comparison"] = compare_sql(gen_sql, gold_sql)
    
    # Summary
    result["summary"] = {
        "execution_valid": result["execution_accuracy"]["valid"],
        "execution_correct": result["execution_accuracy"]["correct"],
        "component_score": result["component_matching"]["overall_score"],
        "semantic_similar": result["sql_comparison"]["semantic_similar"]
    }
    
    return result


# Test
if __name__ == "__main__":
    sql1 = "SELECT count(*) FROM country WHERE GovernmentForm = 'Republic'"
    sql2 = "SELECT COUNT(DISTINCT c.Code) FROM country c WHERE c.GovernmentForm = 'Republic'"
    
    print("SQL 1:", sql1)
    print("SQL 2:", sql2)
    print("\nComparison:")
    
    result = compare_sql(sql1, sql2)
    for k, v in result.items():
        print(f"  {k}: {v}")

