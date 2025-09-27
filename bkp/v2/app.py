# app.py

import streamlit as st
import requests
import uuid
from pathlib import Path
import sqlite3
import json
import datetime
from typing import Optional

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"
DATA_DIR = Path("./data")
INCOMING_DIR = DATA_DIR / "incoming"
SQLITE_DBS_DIR = DATA_DIR / "sqlite_dbs"
SESSION_DB_PATH = DATA_DIR / "prism_sessions.db"
INCOMING_DIR.mkdir(exist_ok=True, parents=True)
SQLITE_DBS_DIR.mkdir(exist_ok=True, parents=True)

# ==============================================================================
# --- Session Persistence Manager ---
# ==============================================================================
class SessionManager:
    """Handles saving and loading Streamlit session state to a SQLite database."""
    def __init__(self, db_path):
        self.db_path = db_path
        self._create_table()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    last_updated TIMESTAMP NOT NULL
                )
            """)

    def save_state(self, session_id: str, state_dict: dict):
        """Saves the session state as a JSON string."""
        state_json = json.dumps(state_dict)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, state_json, last_updated) VALUES (?, ?, ?)",
                (session_id, state_json, datetime.datetime.now())
            )

    def load_state(self, session_id: str) -> Optional[dict]:
        """Loads the session state from a JSON string."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return None
        return None

# --- Helper Functions ---
def reset_session():
    """Clears session state to start over."""
    st.session_state.clear()
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.sources = {}
    st.session_state.active_source_name = None

def display_chat_messages():
    """Displays the chat history for the active source."""
    source_name = st.session_state.active_source_name
    if source_name and source_name in st.session_state.sources:
        for msg in st.session_state.sources[source_name].get("messages", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("plot_path"):
                    st.image(msg["plot_path"])
                if msg.get("step_log"):
                    with st.expander("View Agent Steps"):
                        st.markdown("\n".join(f"- {step}" for step in msg["step_log"]))

# --- Main App Logic ---
st.set_page_config(page_title="PRISM", layout="wide")
st.title("🔮 PRISM: A Multi-Agent Framework")

if "session_id" not in st.session_state:
    reset_session()

session_manager = SessionManager(SESSION_DB_PATH)

# --- Sidebar: Data Source Manager ---
with st.sidebar:
    st.header("Session Control")
    if st.button("Start New Session"):
        reset_session()
        st.rerun()
    
    st.info(f"**Current Session ID:**")
    st.code(st.session_state.session_id, language=None)
    st.caption("Copy this ID to resume your session later.")

    with st.form("resume_form"):
        resume_id = st.text_input("Paste Session ID to Resume")
        if st.form_submit_button("Resume Session"):
            if resume_id:
                loaded_state = session_manager.load_state(resume_id)
                if loaded_state:
                    st.session_state.session_id = resume_id
                    st.session_state.sources = loaded_state.get("sources", {})
                    st.session_state.active_source_name = loaded_state.get("active_source_name")
                    st.success("Session resumed successfully!")
                    st.rerun()
                else:
                    st.error("Session ID not found.")
    
    st.markdown("---")
    st.header("Data Source Manager")
    
    with st.expander("➕ Add New Data Source", expanded=True):
        
        file_tab, db_tab = st.tabs(["📁 File Upload", "🗄️ Database"])
        
        with file_tab:
            with st.form("file_form", clear_on_submit=True):
                file_source_name = st.text_input("File Source Name", key="file_source_name")
                uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
                
                submitted = st.form_submit_button("Add File Source")
                if submitted and uploaded_file and file_source_name:
                    if file_source_name in st.session_state.sources:
                        st.warning("Source name already exists.")
                    else:
                        file_path = INCOMING_DIR / f"{st.session_state.session_id}_{uploaded_file.name}"
                        with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        source_config = {"type": "file", "path": str(file_path)}
                        st.session_state.sources[file_source_name] = {"config": source_config, "analyzed": False}
                        st.rerun()

        with db_tab:
            db_type = st.selectbox("Database Type", ["postgresql", "mysql", "sqlite"], key="db_type_selector")
            
            with st.form("db_form"):
                db_source_name = st.text_input("DB Source Name", key="db_source_name")
                db_config = None
                
                if db_type == "sqlite":
                    sqlite_file = st.file_uploader("Upload SQLite Database File", type=['db', 'sqlite', 'sqlite3'])
                    if sqlite_file:
                        save_path = SQLITE_DBS_DIR / f"{st.session_state.session_id}_{sqlite_file.name}"
                        with open(save_path, "wb") as f: f.write(sqlite_file.getbuffer())
                        db_config = {"type": "sqlite", "path": str(save_path)}
                else:
                    default_ports = {"postgresql": 5432, "mysql": 3306}
                    default_users = {"postgresql": "postgres", "mysql": "root"}
                    
                    host = st.text_input("Host", "localhost", key="db_host")
                    port = st.number_input("Port", value=default_ports[db_type], key="db_port")
                    username = st.text_input("Username", value=default_users[db_type], key="db_user")
                    password = st.text_input("Password", type="password", key="db_pass")
                    database = st.text_input("Database Name", value=default_users[db_type], key="db_name")
                    db_config = {
                        "type": db_type, "host": host, "port": port,
                        "username": username, "password": password, "database": database
                    }

                submitted = st.form_submit_button("Add DB Source")
                if submitted and db_source_name and db_config:
                    if db_source_name in st.session_state.sources:
                        st.warning("Source name already exists.")
                    else:
                        st.session_state.sources[db_source_name] = {"config": db_config, "analyzed": False}
                        st.rerun()

    st.markdown("---")
    
    st.subheader("Configured Sources")
    if not st.session_state.sources:
        st.caption("No data sources added yet.")
    
    for name, source_data in st.session_state.sources.items():
        col1, col2 = st.columns([3, 2])
        with col1:
            st.write(f"**{name}** (`{source_data['config']['type']}`)")
        with col2:
            if not source_data.get("analyzed"):
                if st.button("Analyze", key=f"analyze_{name}", use_container_width=True):
                    with st.spinner(f"Analyzing {name}..."):
                        try:
                            response = requests.post(f"{BACKEND_URL}/process_source", json={"source_config": source_data['config']})
                            response.raise_for_status()
                            result = response.json()
                            
                            if result and "summary" in result:
                                st.session_state.sources[name].update({
                                    "analyzed": True,
                                    "summary": result["summary"],
                                    "data_context": result["data_context"],
                                    "messages": [{"role": "assistant", "content": result["summary"]}]
                                })
                                st.session_state.active_source_name = name
                                st.rerun()
                            else:
                                st.error("Backend returned an invalid response.")

                        except requests.RequestException as e:
                            st.error(f"Error: {e.response.json()['detail'] if e.response else e}")
            else:
                if st.button("Chat", key=f"chat_{name}", type="primary" if st.session_state.active_source_name == name else "secondary", use_container_width=True):
                    st.session_state.active_source_name = name
                    st.rerun()

# ==============================================================================
# --- Main Content Area with Tabs ---
# ==============================================================================
insights_tab, modeling_tab = st.tabs(["📊 Data Insights", "🤖 Predictive Modeling"])

with insights_tab:
    if not st.session_state.active_source_name:
        st.info("Welcome to PRISM. Please add and analyze a data source from the sidebar to begin your conversation.")
    else:
        active_source = st.session_state.sources[st.session_state.active_source_name]
        st.header(f"Chat with: `{st.session_state.active_source_name}`")
        
        display_chat_messages()
        
        if prompt := st.chat_input(f"Ask a question about {st.session_state.active_source_name}..."):
            active_source["messages"].append({"role": "user", "content": prompt})
            st.rerun()

        if active_source["messages"] and active_source["messages"][-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("PRISM is thinking..."):
                    try:
                        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in active_source["messages"][:-1]])
                        
                        payload = {
                            "session_id": st.session_state.session_id,
                            "question": active_source["messages"][-1]["content"],
                            "history": history_str,
                            "source_config": active_source["config"],
                            "data_context": active_source["data_context"],
                            "summary": active_source["summary"]
                        }
                        
                        response = requests.post(f"{BACKEND_URL}/invoke_insights", json=payload)
                        response.raise_for_status()
                        result = response.json()

                        assistant_message = {"role": "assistant", "content": result["final_insight"]}
                        if result.get("plot_path"): assistant_message["plot_path"] = result["plot_path"]
                        if result.get("step_log"): assistant_message["step_log"] = result["step_log"]
                        
                        active_source["messages"].append(assistant_message)
                        st.rerun()

                    except requests.RequestException as e:
                        st.error(f"Error communicating with backend: {e.response.json()['detail'] if e.response else e}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")

with modeling_tab:
    st.header("Generate an ML Pipeline")
    
    if "modeling" not in st.session_state:
        st.session_state.modeling = {
            "source_name": None, "task": "", "generated_code": None,
            "step_log": [], "execution_results": None
        }

    with st.container(border=True):
        st.subheader("1. Configure Modeling Task")
        
        source_options = [name for name, data in st.session_state.sources.items() if data.get("analyzed")]
        if not source_options:
            st.warning("Please add and analyze at least one data source in the sidebar first.")
        else:
            selected_source = st.selectbox("Select Data Source for Modeling", options=source_options)
            task_description = st.text_area("Describe your modeling objective", 
                                            placeholder="e.g., Predict the 'price' column using all other features. It is a regression problem. Use a Gradient Boosting model.")
            
            if st.button("Generate ML Pipeline", type="primary", disabled=not selected_source or not task_description):
                st.session_state.modeling = {
                    "source_name": selected_source, "task": task_description, "generated_code": None,
                    "step_log": [], "execution_results": None
                }
                
                source_info = st.session_state.sources[selected_source]
                payload = {
                    "session_id": st.session_state.session_id,
                    "task_description": task_description,
                    "source_config": source_info["config"],
                    "data_context": source_info["data_context"]
                }
                
                with st.status("Generating ML Pipeline...", expanded=True) as status:
                    try:
                        st.write("📖 Preparing data...")
                        # The new backend flow handles this internally now
                        st.write("📊 Analyzing dataset...")
                        st.write("🤖 Planner agent is analyzing the task and data...")
                        response = requests.post(f"{BACKEND_URL}/start_modeling_pipeline", json=payload)
                        response.raise_for_status()
                        result = response.json()
                        
                        st.session_state.modeling["generated_code"] = result["generated_code"]
                        st.session_state.modeling["step_log"] = result["step_log"]
                        st.session_state.modeling["download_path"] = result["download_path"]
                        
                        status.update(label="Code Generation Complete!", state="complete")
                        st.rerun()
                    except requests.RequestException as e:
                        status.update(label="Generation Failed", state="error")
                        st.error(f"Error: {e.response.json()['detail'] if e.response else e}")

    if st.session_state.modeling["generated_code"]:
        with st.container(border=True):
            st.subheader("2. Review and Execute Pipeline")
            
            with st.expander("View Agent Steps for Generation"):
                st.markdown("\n".join(f"- {step}" for step in st.session_state.modeling["step_log"]))
            
            st.code(st.session_state.modeling["generated_code"], language="python")
            
            col1, col2 = st.columns(2)
            with col1:
                with open(st.session_state.modeling["download_path"], "rb") as fp:
                    st.download_button(
                        label="Download Pipeline as .zip", data=fp,
                        file_name=f"{st.session_state.session_id}_pipeline.zip",
                        mime="application/zip", use_container_width=True
                    )
            with col2:
                if st.button("🚀 Proceed to Execute & Train Model", use_container_width=True):
                    with st.status("Executing Pipeline...", expanded=True) as status:
                        try:
                            st.write("Sandbox environment is running the code...")
                            payload = {"session_id": st.session_state.session_id}
                            response = requests.post(f"{BACKEND_URL}/execute_modeling_pipeline", json=payload)
                            response.raise_for_status()
                            result = response.json()
                            st.session_state.modeling["execution_results"] = result
                            status.update(label="Execution Complete!", state="complete")
                            st.rerun()
                        except requests.RequestException as e:
                            status.update(label="Execution Failed", state="error")
                            st.error(f"Error: {e.response.json()['detail'] if e.response else e}")
    
    if st.session_state.modeling["execution_results"]:
        with st.container(border=True):
            st.subheader("3. View Results and Artifacts")
            results = st.session_state.modeling["execution_results"]
            
            st.text_area("Execution Log", results["execution_log"], height=300)
            
            if results.get("artifacts"):
                st.success("Model and metrics saved successfully!")
                for name, path in results["artifacts"].items():
                    with open(path, "rb") as fp:
                        st.download_button(f"Download {name}", data=fp, file_name=name)
            else:
                st.error("Execution finished, but no artifacts were found. Check the log for details.")

# --- Save state at the end of every script run ---
if st.session_state.get("sources"):
    state_to_save = {
        "sources": st.session_state.sources,
        "active_source_name": st.session_state.active_source_name
    }
    session_manager.save_state(st.session_state.session_id, state_to_save)