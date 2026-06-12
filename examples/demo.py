"""
Demo Script - Quick demonstration of the Text-to-SQL system

This script demonstrates all three pipeline approaches with a sample question.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from pipelines import (
    SingleAgentPipeline,
    MultiAgentNoRAGPipeline,
    MultiAgentRAGPipeline
)

console = Console()


def create_demo_database():
    """Create a simple demo database for testing."""
    import sqlite3
    
    db_path = Path(__file__).parent / "demo.sqlite"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            major TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            credits INTEGER,
            department TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY,
            student_id INTEGER,
            course_id INTEGER,
            grade TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    
    # Insert sample data
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM courses")
    cursor.execute("DELETE FROM enrollments")
    
    students = [
        (1, "Alice", 20, "Computer Science"),
        (2, "Bob", 22, "Mathematics"),
        (3, "Charlie", 21, "Physics"),
        (4, "Diana", 19, "Computer Science"),
        (5, "Eve", 23, "Mathematics"),
    ]
    cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?)", students)
    
    courses = [
        (1, "Introduction to Programming", 3, "CS"),
        (2, "Calculus I", 4, "Math"),
        (3, "Physics 101", 3, "Physics"),
        (4, "Data Structures", 3, "CS"),
        (5, "Linear Algebra", 3, "Math"),
    ]
    cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?)", courses)
    
    enrollments = [
        (1, 1, 1, "A"),
        (2, 1, 4, "B+"),
        (3, 2, 2, "A-"),
        (4, 2, 5, "B"),
        (5, 3, 3, "A"),
        (6, 4, 1, "A"),
        (7, 4, 4, "A-"),
        (8, 5, 2, "B+"),
    ]
    cursor.executemany("INSERT INTO enrollments VALUES (?, ?, ?, ?)", enrollments)
    
    conn.commit()
    conn.close()
    
    console.print(f"[green]Demo database created: {db_path}[/green]")
    return str(db_path)


def run_demo():
    """Run the demo."""
    console.print(Panel(
        "[bold cyan]Intelligent SQL Query Agent Demo[/bold cyan]\n\n"
        "This demo shows all three pipeline approaches:\n"
        "1. Single Agent\n"
        "2. Multi-Agent (No RAG)\n"
        "3. Multi-Agent (RAG - Hybrid)\n",
        title="Demo"
    ))
    
    # Create demo database
    db_path = create_demo_database()
    
    # Show schema
    console.print("\n[bold]Database Schema:[/bold]")
    with DatabaseManager(db_path) as db:
        console.print(db.get_schema_text())
    
    # Test questions
    questions = [
        "How many students are there?",
        "List all students majoring in Computer Science",
        "What is the average age of students?",
    ]
    
    # Initialize pipelines
    try:
        llm = OllamaClient()
        console.print("\n[green]Connected to Ollama LLM[/green]")
    except Exception as e:
        console.print(f"[red]Could not connect to Ollama: {e}[/red]")
        console.print("[yellow]Make sure Ollama is running: ollama serve[/yellow]")
        return
    
    pipelines = {
        "Single Agent": SingleAgentPipeline(llm),
        "Multi-Agent (No RAG)": MultiAgentNoRAGPipeline(llm),
        "Multi-Agent (RAG)": MultiAgentRAGPipeline(llm, "hybrid"),
    }
    
    # Run each question through each pipeline
    for question in questions:
        console.print(Panel(f"[bold]{question}[/bold]", title="Question"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Pipeline")
        table.add_column("SQL")
        table.add_column("Success")
        table.add_column("Time")
        
        for name, pipeline in pipelines.items():
            pipeline.set_verbose(False)
            
            try:
                result = pipeline.run(question, db_path)
                
                sql = result.get("sql", "")
                if len(sql) > 60:
                    sql = sql[:60] + "..."
                
                success = "[green]✓[/green]" if result.get("success") else "[red]✗[/red]"
                time_str = f"{result.get('execution_time', 0):.2f}s"
                
                table.add_row(name, sql, success, time_str)
                
            except Exception as e:
                table.add_row(name, f"Error: {str(e)[:30]}", "[red]✗[/red]", "-")
        
        console.print(table)
        console.print()
    
    console.print("[bold green]Demo completed![/bold green]")


if __name__ == "__main__":
    run_demo()

