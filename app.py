"""
🤖 Intelligent SQL Query Agent
Interactive Streamlit UI

Enhanced with:
- Multi-database comparison support
- Improved UI/UX with featured databases
- Batch evaluation mode
"""

import streamlit as st
import json
import time
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Project imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config.config import SPIDER_DIR, OLLAMA_MODEL
from utils.llm_client import OllamaClient
from utils.database import DatabaseManager
from pipelines import SingleAgentPipeline, MultiAgentNoRAGPipeline, MultiAgentRAGPipeline


# Featured databases for the project demo
FEATURED_DATABASES = {
    "world_1": {
        "name": "🌍 World Database",
        "description": "Countries, cities, languages - Basic difficulty",
        "tables": ["country", "city", "countrylanguage"],
        "sample_questions": [
            "What are the names of countries that became independent after 1950?",
            "How many countries have a republic as their form of government?",
            "What is the total surface area of countries in the Caribbean region?",
            "Which countries have population over 100 million?",
            "What are the official languages spoken in Europe?"
        ]
    },
    "concert_singer": {
        "name": "🎵 Concert Singer",
        "description": "Concerts, singers, stadiums - Medium difficulty",
        "tables": ["stadium", "singer", "concert", "singer_in_concert"],
        "sample_questions": [
            "How many concerts are there?",
            "What are the names of all stadiums with capacity over 50000?",
            "Which singer has performed in the most concerts?",
            "List all concerts held in 2014",
            "What is the average capacity of stadiums?"
        ]
    },
    "student_transcripts_tracking": {
        "name": "🎓 Student Transcripts",
        "description": "Students, courses, grades - Complex joins (11 tables)",
        "tables": ["Students", "Courses", "Transcripts", "Departments"],
        "sample_questions": [
            "How many students are enrolled?",
            "What courses are offered by the Computer Science department?",
            "What is the average grade for each course?",
            "Which students have taken more than 5 courses?",
            "List all courses with their department names"
        ]
    },
    "dog_kennels": {
        "name": "🐕 Dog Kennels",
        "description": "Dogs, breeds, owners, treatments - Complex schema (8 tables)",
        "tables": ["Breeds", "Charges", "Sizes", "Treatment_Types", "Owners", "Dogs", "Professionals", "Treatments"],
        "sample_questions": [
            "How many dogs are registered?",
            "What are the different dog breeds?",
            "Which owners have the most dogs?",
            "What treatments are available?",
            "List all professionals and their specialties"
        ]
    },
    "car_1": {
        "name": "🚗 Car Database",
        "description": "Cars, makers, models, countries - Medium complexity (6 tables)",
        "tables": ["continents", "countries", "car_makers", "model_list", "car_names", "cars_data"],
        "sample_questions": [
            "How many car makers are there?",
            "What are the car models from each maker?",
            "Which countries produce the most cars?",
            "What is the average horsepower by continent?",
            "List all car names with their makers"
        ]
    }
}

# Page config
st.set_page_config(
    page_title="Text-to-SQL System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@400;500;700&display=swap');
    
    :root {
        --primary: #6366f1;
        --secondary: #a855f7;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
    }
    
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .sql-box {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.5rem;
        font-family: 'JetBrains Mono', monospace;
        border-left: 4px solid #6366f1;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .pipeline-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .pipeline-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    
    .success-badge {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
    }
    
    .error-badge {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
    }
    
    .schema-table {
        background: #1e293b;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    div[data-testid="stExpander"] {
        background: #1e293b;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Batch Evaluation Mode - Lighter background */
    div[data-testid="stExpander"]:has(summary:contains("Batch Evaluation")) {
        background: #4a5568 !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }
    
    div[data-testid="stExpander"]:has(summary:contains("Batch Evaluation")) > div {
        background: #4a5568 !important;
    }
    
    /* Alternative: Style batch evaluation section directly */
    .batch-evaluation-section {
        background: #4a5568 !important;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
</style>
""", unsafe_allow_html=True)


def get_available_databases():
    """Get list of available databases from Spider dataset (limited to featured databases)"""
    # Only return the selected demo databases
    selected_dbs = [
        "student_transcripts_tracking",
        "concert_singer",
        "world_1",
        "dog_kennels",
        "car_1",
        "real_estate_properties",
    ]
    db_dir = SPIDER_DIR / "database"
    if not db_dir.exists():
        return []
    
    # Filter to only include selected databases that exist
    available = []
    for db_name in selected_dbs:
        db_path = db_dir / db_name / f"{db_name}.sqlite"
        if db_path.exists():
            available.append(db_name)
    
    return sorted(available)


def get_database_schema(db_path: str) -> dict:
    """Extract schema information from database"""
    try:
        with DatabaseManager(db_path) as db:
            schema = db.get_schema()
            tables = db.get_tables()
            
            schema_info = {}
            for table in tables:
                columns = db.get_columns(table)
                foreign_keys = db.get_foreign_keys(table)
                schema_info[table] = {
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }
            return schema_info
    except Exception as e:
        st.error(f"Schema extraction error: {e}")
        return {}


def load_sample_questions(db_id: str, limit: int = 10) -> list:
    """Load sample questions for a database"""
    dev_path = SPIDER_DIR / "dev.json"
    if not dev_path.exists():
        return []
    
    try:
        with open(dev_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        questions = [d for d in data if d['db_id'] == db_id][:limit]
        return questions
    except:
        return []


@st.cache_resource
def get_llm_client():
    """Get cached LLM client"""
    return OllamaClient()


@st.cache_resource
def get_pipelines(_llm):
    """Get cached pipelines"""
    return {
        "Single Agent": SingleAgentPipeline(_llm),
        "Multi-Agent": MultiAgentNoRAGPipeline(_llm),
        "Multi-Agent RAG": MultiAgentRAGPipeline(_llm, retrieval_method="hybrid")
    }


def run_pipeline(pipeline, question: str, db_path: str):
    """Run a pipeline and return results"""
    start_time = time.time()
    try:
        result = pipeline.run(question, db_path)
        execution_time = time.time() - start_time
        return {
            "success": True,
            "sql": result.get("sql", ""),
            "result": result.get("result"),
            "execution_time": execution_time,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "sql": "",
            "result": None,
            "execution_time": time.time() - start_time,
            "error": str(e)
        }


def main():
    # Initialize session state for selected database
    if "selected_db" not in st.session_state:
        st.session_state.selected_db = list(FEATURED_DATABASES.keys())[0]
    
    # Track which widget was used to select the database
    if "db_source" not in st.session_state:
        st.session_state.db_source = "radio"  # "radio" or "dropdown"
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Intelligent SQL Query Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Natural Language to SQL Query Converter with Multi-Agent Architecture</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # Featured database selection
        st.markdown("#### 🌟 Featured Databases")
        featured_db_keys = list(FEATURED_DATABASES.keys())
        current_index = featured_db_keys.index(st.session_state.selected_db) if st.session_state.selected_db in featured_db_keys else 0
        
        featured_db = st.radio(
            "Select Database",
            featured_db_keys,
            format_func=lambda x: FEATURED_DATABASES[x]["name"],
            index=current_index,
            key="db_radio"
        )
        
        # Also allow other databases
        databases = get_available_databases()
        with st.expander("📂 Or choose from all databases"):
            all_db = st.selectbox(
                "All Databases",
                databases,
                index=databases.index(st.session_state.selected_db) if st.session_state.selected_db in databases else 0,
                key="all_db_selectbox"
            )
            if st.button("Use this database", key="use_db_button"):
                st.session_state.selected_db = all_db
                st.session_state.db_source = "dropdown"
                # Set prev_radio_value to what the radio will show after rerun
                # If selected_db is not in featured list, radio will show first featured (index 0)
                # If selected_db is in featured list, radio will show selected_db
                if all_db in featured_db_keys:
                    st.session_state.prev_radio_value = all_db
                else:
                    st.session_state.prev_radio_value = featured_db_keys[0]  # First featured
                st.rerun()
        
        # Track previous radio value to detect actual user changes
        if "prev_radio_value" not in st.session_state:
            st.session_state.prev_radio_value = featured_db
        
        # Update from radio button only if:
        # 1. Current source is "radio" (not from dropdown), OR
        # 2. User explicitly changed the radio button (different from previous value)
        radio_actually_changed = featured_db != st.session_state.prev_radio_value
        
        if st.session_state.db_source == "radio":
            # Radio button is the active source, sync with it
            if featured_db != st.session_state.selected_db:
                st.session_state.selected_db = featured_db
            st.session_state.prev_radio_value = featured_db
        elif radio_actually_changed:
            # User explicitly changed the radio button while dropdown was active
            # Switch back to radio button control
            st.session_state.selected_db = featured_db
            st.session_state.db_source = "radio"
            st.session_state.prev_radio_value = featured_db
        else:
            # Dropdown is active and radio hasn't changed - keep dropdown selection
            # Update prev_radio_value to current to prevent false positives
            st.session_state.prev_radio_value = featured_db
        
        selected_db = st.session_state.selected_db
        
        # Display database info
        if selected_db in FEATURED_DATABASES:
            db_info = FEATURED_DATABASES[selected_db]
            st.caption(db_info["description"])
        else:
            st.caption(f"Database: {selected_db}")
        db_path = str(SPIDER_DIR / "database" / selected_db / f"{selected_db}.sqlite")
        
        # Pipeline selection
        st.markdown("---")
        st.markdown("### 🔧 Pipeline Selection")
        
        pipeline_option = st.radio(
            "Choose Pipeline",
            ["Single Agent", "Multi-Agent", "Multi-Agent RAG", "Compare All"],
            index=3,  # Default to Compare All for demonstration
            help="Single: One LLM call\nMulti: Multiple specialized agents\nMulti+RAG: With schema retrieval"
        )
        
        # RAG settings (if applicable)
        if pipeline_option in ["Multi-Agent RAG", "Compare All"]:
            st.markdown("---")
            st.markdown("### 🔍 RAG Settings")
            retrieval_method = st.selectbox(
                "Retrieval Method",
                ["hybrid", "dense", "sparse"],
                help="Dense: Semantic search\nSparse: Keyword search\nHybrid: Both combined"
            )
            top_k = st.slider("Top-K Tables", 1, 10, 5)
        else:
            retrieval_method = "hybrid"
            top_k = 5
        
        # Schema viewer
        st.markdown("---")
        st.markdown("### 📊 Database Schema")
        
        schema_info = get_database_schema(db_path)
        for table, info in schema_info.items():
            with st.expander(f"📋 {table}"):
                cols = info.get("columns", [])
                for col in cols:
                    col_name = col[1] if isinstance(col, tuple) else col
                    col_type = col[2] if isinstance(col, tuple) and len(col) > 2 else "?"
                    st.markdown(f"`{col_name}` ({col_type})")
        
        # Model info
        st.markdown("---")
        st.markdown("### 🧠 Model Info")
        st.info(f"**LLM:** {OLLAMA_MODEL}\n\n**Embedding:** all-MiniLM-L6-v2\n\n**SQLglot:** Enabled")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Enter Your Question")
        
        # Featured sample questions from our curated list
        if selected_db in FEATURED_DATABASES:
            st.markdown("**📝 Sample Questions (click to use):**")
            sample_qs = FEATURED_DATABASES[selected_db]["sample_questions"]
            
            # Display as clickable buttons in 2 columns
            q_cols = st.columns(2)
            for i, sq in enumerate(sample_qs):
                with q_cols[i % 2]:
                    if st.button(f"📌 {sq[:50]}...", key=f"sample_{i}", help=sq):
                        st.session_state.question = sq
        else:
            # Fallback to loading from Spider dev.json
            sample_questions = load_sample_questions(selected_db, 5)
            if sample_questions:
                st.markdown("**📝 Sample Questions:**")
                for i, sq in enumerate(sample_questions):
                    if st.button(f"Q{i+1}: {sq['question'][:40]}...", key=f"sample_{i}"):
                        st.session_state.question = sq["question"]
        
        # Question input
        question = st.text_area(
            "Your question in natural language:",
            value=st.session_state.get("question", ""),
            height=100,
            placeholder="e.g., What are the names of countries with population over 1 million?"
        )
        
        # Generate button
        generate_btn = st.button("🚀 Generate SQL", type="primary", use_container_width=True)
        
        # Batch evaluation mode
        with st.expander("🔬 Batch Evaluation Mode", expanded=False):
            st.markdown("Run all sample questions and compare pipelines")
            if st.button("Run Batch Evaluation", key="batch_eval"):
                st.session_state.batch_mode = True
    
    with col2:
        st.markdown("### 📈 Quick Stats")
        if schema_info:
            st.metric("Tables", len(schema_info))
            total_cols = sum(len(info.get("columns", [])) for info in schema_info.values())
            st.metric("Total Columns", total_cols)
        
        # Database info card
        if selected_db in FEATURED_DATABASES:
            st.markdown("### 📋 Database Info")
            st.markdown(f"**Tables:** {', '.join(FEATURED_DATABASES[selected_db]['tables'])}")
    
    # Results section
    if generate_btn and question:
        st.markdown("---")
        st.markdown("### 📊 Results")
        
        try:
            llm = get_llm_client()
            
            if pipeline_option == "Compare All":
                # Compare all pipelines
                st.markdown("#### 🔄 Comparing All Pipelines...")
                
                pipelines = {
                    "Single Agent": SingleAgentPipeline(llm),
                    "Multi-Agent": MultiAgentNoRAGPipeline(llm),
                    "Multi-Agent RAG": MultiAgentRAGPipeline(llm, retrieval_method=retrieval_method)
                }
                
                results = {}
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, (name, pipeline) in enumerate(pipelines.items()):
                    status_text.text(f"Running {name}...")
                    results[name] = run_pipeline(pipeline, question, db_path)
                    progress_bar.progress((i + 1) / len(pipelines))
                
                status_text.empty()
                progress_bar.empty()
                
                # Display comparison
                cols = st.columns(3)
                for i, (name, result) in enumerate(results.items()):
                    with cols[i]:
                        st.markdown(f"#### {name}")
                        
                        if result["success"]:
                            st.success(f"✅ Success ({result['execution_time']:.1f}s)")
                            st.code(result["sql"], language="sql")
                            
                            # Always show results section
                            with st.expander("📋 Query Result", expanded=True):
                                if result["result"]:
                                    if isinstance(result["result"], list):
                                        df = pd.DataFrame(result["result"])
                                        st.dataframe(df, use_container_width=True)
                                    else:
                                        st.write(result["result"])
                                else:
                                    st.info("Query executed successfully but returned no results.")
                        else:
                            st.error(f"❌ Error: {result['error']}")
                            st.code(result.get("sql", ""), language="sql")
                
                # Comparison chart
                st.markdown("#### ⏱️ Execution Time Comparison")
                times_df = pd.DataFrame([
                    {"Pipeline": name, "Time (s)": result["execution_time"]}
                    for name, result in results.items()
                ])
                fig = px.bar(
                    times_df, x="Pipeline", y="Time (s)",
                    color="Pipeline",
                    color_discrete_sequence=["#6366f1", "#a855f7", "#ec4899"]
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Single pipeline
                with st.spinner(f"Running {pipeline_option}..."):
                    if pipeline_option == "Single Agent":
                        pipeline = SingleAgentPipeline(llm)
                    elif pipeline_option == "Multi-Agent":
                        pipeline = MultiAgentNoRAGPipeline(llm)
                    else:
                        pipeline = MultiAgentRAGPipeline(llm, retrieval_method=retrieval_method)
                    
                    result = run_pipeline(pipeline, question, db_path)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### 📝 Generated SQL")
                    if result["success"]:
                        st.code(result["sql"], language="sql")
                    else:
                        st.error(f"Error: {result['error']}")
                
                with col2:
                    st.markdown("#### ⚡ Metrics")
                    st.metric("Execution Time", f"{result['execution_time']:.2f}s")
                    st.metric("Status", "✅ Success" if result["success"] else "❌ Failed")
                
                # Always show query results section
                st.markdown("#### 📊 Query Results")
                if result["success"] and result["result"]:
                    if isinstance(result["result"], list):
                        df = pd.DataFrame(result["result"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Download option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "query_results.csv",
                            "text/csv"
                        )
                    else:
                        st.write(result["result"])
                elif result["success"] and not result["result"]:
                    st.info("Query executed successfully but returned no results.")
                else:
                    st.warning(f"Query failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Make sure Ollama is running with the correct model.")
    
    # Batch Evaluation Mode
    if st.session_state.get("batch_mode") and selected_db in FEATURED_DATABASES:
        st.markdown("---")
        st.markdown('<div class="batch-evaluation-section">', unsafe_allow_html=True)
        st.markdown("### 🔬 Batch Evaluation Results")
        
        try:
            llm = get_llm_client()
            batch_questions = FEATURED_DATABASES[selected_db]["sample_questions"]
            
            pipelines_to_test = {
                "Single Agent": SingleAgentPipeline(llm),
                "Multi-Agent": MultiAgentNoRAGPipeline(llm),
                "Multi-Agent RAG": MultiAgentRAGPipeline(llm, retrieval_method="hybrid")
            }
            
            all_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_steps = len(batch_questions) * len(pipelines_to_test)
            current_step = 0
            
            for q_idx, q in enumerate(batch_questions):
                for p_name, pipeline in pipelines_to_test.items():
                    status_text.text(f"Testing Q{q_idx+1} with {p_name}...")
                    result = run_pipeline(pipeline, q, db_path)
                    all_results.append({
                        "Question": q[:50] + "...",
                        "Pipeline": p_name,
                        "Success": "✅" if result["success"] else "❌",
                        "Time (s)": f"{result['execution_time']:.1f}",
                        "SQL": result["sql"][:80] + "..." if result["sql"] else "N/A"
                    })
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
            
            progress_bar.empty()
            status_text.empty()
            
            # Display results table
            results_df = pd.DataFrame(all_results)
            st.dataframe(results_df, use_container_width=True)
            
            # Summary statistics
            st.markdown("#### 📊 Summary")
            summary_cols = st.columns(3)
            
            for i, p_name in enumerate(pipelines_to_test.keys()):
                pipeline_results = [r for r in all_results if r["Pipeline"] == p_name]
                success_count = sum(1 for r in pipeline_results if r["Success"] == "✅")
                avg_time = sum(float(r["Time (s)"]) for r in pipeline_results) / len(pipeline_results)
                
                with summary_cols[i]:
                    st.metric(
                        p_name,
                        f"{success_count}/{len(pipeline_results)} ✅",
                        f"Avg: {avg_time:.1f}s"
                    )
            
            # Clear batch mode
            st.session_state.batch_mode = False
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Batch evaluation error: {e}")
            st.session_state.batch_mode = False
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #64748b; padding: 1rem;">
            <p>Built with ❤️ using Streamlit, LangGraph, FAISS, SQLglot and Ollama</p>
            <p>Intelligent SQL Query Agent</p>
            <p style="font-size: 0.8rem;">Featured Databases: World, Concert Singer, Student Transcripts</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()


