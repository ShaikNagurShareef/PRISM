# app.py

import streamlit as st
import requests
import uuid
from pathlib import Path
import sqlite3
import json
from datetime import datetime
import time
import shutil
import base64
import io
import zipfile
from typing import Optional
# ==============================================================================
# --- CORRECTED: Clear and distinct backend URLs ---
# ==============================================================================
PRISM_BACKEND_URL = "http://127.0.0.1:8000" # PRISM runs on port 8001
AUTORAG_API_BASE_URL = "http://127.0.0.1:8001" # AutoRAG runs on port 8000

DATA_DIR = Path("./data")
INCOMING_DIR = DATA_DIR / "incoming"
SQLITE_DBS_DIR = DATA_DIR / "sqlite_dbs"
REPORTS_DIR = DATA_DIR / "reports"
SESSION_DB_PATH = DATA_DIR / "prism_sessions.db"
INCOMING_DIR.mkdir(exist_ok=True, parents=True)
SQLITE_DBS_DIR.mkdir(exist_ok=True, parents=True)
REPORTS_DIR.mkdir(exist_ok=True, parents=True)

# ==============================================================================
# --- PRISM: Session Persistence Manager ---
# ==============================================================================
class SessionManager:
    """Handles saving and loading PRISM session state to a SQLite database."""
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
        state_json = json.dumps(state_dict)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, state_json, last_updated) VALUES (?, ?, ?)",
                (session_id, state_json, datetime.now())
            )

    def load_state(self, session_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return None
        return None

# ==============================================================================
# --- AutoRAG: Helper Functions for API Calls ---
# ==============================================================================
def get_capabilities():
    try:
        response = requests.get(f"{AUTORAG_API_BASE_URL}/rags/capabilities")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching AutoRAG capabilities: {e}. Please ensure the AutoRAG backend is running on port 8000.")
        return None

def get_all_rags():
    try:
        response = requests.get(f"{AUTORAG_API_BASE_URL}/rags/")
        response.raise_for_status()
        return response.json().get("rags", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching RAGs: {e}")
        return []

def create_rag(payload):
    try:
        response = requests.post(f"{AUTORAG_API_BASE_URL}/rags/", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try: error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError: error_detail = response.text
        st.error(f"Error creating RAG: {error_detail}")
        return None

def update_rag(rag_id, payload):
    try:
        response = requests.put(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try: error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError: error_detail = response.text
        st.error(f"Error updating RAG: {error_detail}")
        return None

def upload_file(rag_id, file):
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}/documents", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try: error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError: error_detail = response.text
        st.error(f"Error uploading file '{file.name}': {error_detail}")
        return None

def post_query(rag_id, query, session_id):
    payload = {"query": query, "session_id": session_id}
    try:
        response = requests.post(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting response: {e}")
        return None

def delete_rag_instance(rag_id):
    try:
        response = requests.delete(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting RAG: {e}")
        return None

def get_documents(rag_id):
    try:
        response = requests.get(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}/documents")
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching documents: {e}")
        return []

def get_chat_history(rag_id):
    try:
        response = requests.get(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}/chat/history")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching chat history: {e}")
        return []

def build_rag_image(rag_id):
    try:
        response = requests.post(f"{AUTORAG_API_BASE_URL}/rags/{rag_id}/export")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to trigger image build: {e}")
        return None

# ==============================================================================
# --- Combined Helper Functions ---
# ==============================================================================
def reset_session():
    """Clears session state for all PRISM features."""
    st.session_state.clear()
    # PRISM State
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.sources = {}
    st.session_state.active_source_name = None
    st.session_state.modeling = {
        "source_name": None, "task": "", "generated_code": None,
        "step_log": [], "execution_results": None
    }
    # AutoRAG State
    st.session_state.selected_rag_id = None
    st.session_state.editing_rag_id = None
    st.session_state.session_ids = {}
    st.session_state.chat_histories = {}

def display_chat_messages():
    """Displays the chat history for the active PRISM source."""
    source_name = st.session_state.active_source_name
    if source_name and source_name in st.session_state.sources:
        for msg in st.session_state.sources[source_name].get("messages", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("plot_path"): st.image(msg["plot_path"])
                if msg.get("step_log"):
                    with st.expander("View Agent Steps"):
                        st.markdown("\n".join(f"- {step}" for step in msg["step_log"]))

# ==============================================================================
# --- AutoRAG: UI Rendering Functions ---
# ==============================================================================
def handle_file_upload(rag_id):
    uploader_key = f"uploader_{rag_id}"
    if uploader_key in st.session_state and st.session_state[uploader_key]:
        uploaded_files = st.session_state[uploader_key]
        progress_bar = st.sidebar.progress(0, text="Uploading files...")
        for i, file in enumerate(uploaded_files):
            with st.spinner(f"Uploading '{file.name}'..."):
                result = upload_file(rag_id, file)
                if result: st.toast(f"✅ Successfully uploaded '{file.name}'", icon="🎉")
                else: st.toast(f"❌ Failed to upload '{file.name}'", icon="🔥")
            progress_bar.progress((i + 1) / len(uploaded_files), text=f"Uploaded {i+1}/{len(uploaded_files)}")
        st.sidebar.success("All files processed! Ingestion is happening in the background.")

def render_management_page():
    st.title("AutoRAG Management Dashboard")
    st.header("🚀 Create a New RAG Instance")
    with st.container(border=True):
        capabilities = get_capabilities()
        if not capabilities: return
        st.subheader("1. Core Components")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            llm_provider = st.selectbox("LLM Provider", list(capabilities["available_llms"].keys()), key="llm_provider")
            llm_model = st.selectbox("LLM Model", list(capabilities["available_llms"][st.session_state.llm_provider].keys()))
        with col2:
            embed_provider = st.selectbox("Embedding Provider", list(capabilities["available_embedders"].keys()), key="embed_provider")
            embed_model = st.selectbox("Embedding Model", list(capabilities["available_embedders"][st.session_state.embed_provider].keys()))
        with col3:
            vector_store = st.selectbox("Vector Store", list(capabilities["available_vector_stores"].keys()))
        with col4:
            chunker_name = st.selectbox("Chunking Strategy", list(capabilities["available_chunkers"].keys()), format_func=lambda x: capabilities["available_chunkers"][x]['name'])
        with st.form("create_rag_form"):
            st.subheader("2. Basic Information & Behavior")
            name = st.text_input("RAG Name*", placeholder="e.g., Financial Analyst Bot")
            description = st.text_area("Description*", placeholder="A short summary of what this RAG is for.")
            system_prompt = st.text_area("Custom System Prompt*", height=150, value="You are a helpful AI assistant...")
            submitted = st.form_submit_button("Create RAG Instance", use_container_width=True, type="primary")
            if submitted:
                if not name.strip() or not description.strip() or not system_prompt.strip():
                    st.warning("RAG Name, Description, and System Prompt are all required fields.")
                else:
                    payload = {"name": name, "description": description, "system_prompt": system_prompt, "config": {"llm_provider": llm_provider, "llm_model": llm_model, "embedding_provider": embed_provider, "embedding_model": embed_model, "vector_store": vector_store, "chunker": chunker_name}}
                    with st.spinner("Creating RAG instance..."):
                        result = create_rag(payload)
                        if result: st.success(f"Successfully created RAG: {result['name']}"); time.sleep(1); st.rerun()
    st.divider()
    st.header("📚 Available RAG Instances")
    rag_list = get_all_rags()
    if not rag_list:
        st.info("No RAG instances found. Create one above to get started.")
    else:
        for rag in rag_list:
            with st.container(border=True):
                cols = st.columns([3, 1, 1, 1])
                with cols[0]:
                    st.subheader(rag['name']); st.caption(f"ID: {rag['id']}"); st.write(rag['description'] or "_No description provided._")
                    with st.expander("View Configuration"): st.json(rag['config'])
                with cols[1]:
                    if st.button("💬 Chat", key=f"chat_{rag['id']}", use_container_width=True):
                        st.session_state.selected_rag_id = rag['id']; st.rerun()
                with cols[2]:
                    if st.button("✏️ Edit", key=f"edit_{rag['id']}", use_container_width=True):
                        st.session_state.editing_rag_id = rag['id']; st.rerun()
                # with cols[4]:
                #     if st.button("📦 Build Image", key=f"build_{rag['id']}", use_container_width=True):
                #         with st.spinner(f"Agent is building Docker image for '{rag['name']}'... This may take several minutes."):
                #             result = build_rag_image(rag['id'])
                #             if result and 'message' in result:
                #                 st.success("Agent finished!"); st.info("Agent's Final Message:"); st.code(result['message'], language='bash')
                #             else: st.error("Agent failed to build the image. Check the backend logs for details.")
                with cols[3]:
                    if st.button("🗑️ Delete", key=f"delete_{rag['id']}", use_container_width=True, type="secondary"):
                        st.session_state[f"confirm_delete_{rag['id']}"] = True
                if st.session_state.get(f"confirm_delete_{rag['id']}", False):
                    st.warning(f"Are you sure you want to delete '{rag['name']}'?", icon="⚠️")
                    c1, c2, c3 = st.columns([1, 1, 4])
                    with c1:
                        if st.button("Yes, delete", key=f"confirm_yes_{rag['id']}", use_container_width=True, type="primary"):
                            with st.spinner(f"Deleting RAG '{rag['name']}'..."):
                                result = delete_rag_instance(rag['id'])
                                if result: st.success(result['message']); del st.session_state[f"confirm_delete_{rag['id']}"]; time.sleep(2); st.rerun()
                    with c2:
                        if st.button("Cancel", key=f"confirm_no_{rag['id']}", use_container_width=True):
                            del st.session_state[f"confirm_delete_{rag['id']}"]; st.rerun()

def render_edit_page():
    st.title("✏️ Edit RAG Instance")
    rag_id = st.session_state.editing_rag_id
    rag_details = next((rag for rag in get_all_rags() if rag['id'] == rag_id), None)
    if not rag_details: st.error("Could not load RAG details."); time.sleep(2); st.rerun(); return
    if st.button("← Back to Management"): st.session_state.editing_rag_id = None; st.rerun()
    with st.container(border=True):
        capabilities = get_capabilities()
        if not capabilities: st.warning("Could not load platform capabilities."); return
        st.subheader("1. Core Components"); st.info("Changing core components (Embedder, Chunker) will trigger a full re-indexing of all documents.")
        current_config = rag_details['config']
        llm_providers = list(capabilities["available_llms"].keys()); embed_providers = list(capabilities["available_embedders"].keys()); chunker_keys = list(capabilities["available_chunkers"].keys())
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            llm_provider_idx = llm_providers.index(current_config.get('llm_provider')) if current_config.get('llm_provider') in llm_providers else 0
            llm_provider = st.selectbox("LLM Provider", llm_providers, index=llm_provider_idx, key="edit_llm_provider")
            llm_models = list(capabilities["available_llms"][st.session_state.edit_llm_provider].keys())
            llm_model_idx = llm_models.index(current_config.get('llm_model')) if current_config.get('llm_model') in llm_models else 0
            llm_model = st.selectbox("LLM Model", llm_models, index=llm_model_idx)
        with col2:
            embed_provider_idx = embed_providers.index(current_config.get('embedding_provider')) if current_config.get('embedding_provider') in embed_providers else 0
            embed_provider = st.selectbox("Embedding Provider", embed_providers, index=embed_provider_idx, key="edit_embed_provider")
            embed_models = list(capabilities["available_embedders"][st.session_state.edit_embed_provider].keys())
            embed_model_idx = embed_models.index(current_config.get('embedding_model')) if current_config.get('embedding_model') in embed_models else 0
            embed_model = st.selectbox("Embedding Model", embed_models, index=embed_model_idx)
        with col3:
            vector_store = st.selectbox("Vector Store", list(capabilities["available_vector_stores"].keys()), disabled=True); st.caption("Changing the vector store is not currently supported.")
        with col4:
            chunker_idx = chunker_keys.index(current_config.get('chunker')) if current_config.get('chunker') in chunker_keys else 0
            chunker_name = st.selectbox("Chunking Strategy", chunker_keys, index=chunker_idx, format_func=lambda x: capabilities["available_chunkers"][x]['name'])
        with st.form("edit_rag_form"):
            st.subheader("2. Basic Information & Behavior")
            name = st.text_input("RAG Name*", value=rag_details['name'])
            description = st.text_area("Description*", value=rag_details['description'])
            system_prompt = st.text_area("Custom System Prompt*", height=150, value=rag_details['system_prompt'])
            submitted = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
            if submitted:
                if not name.strip() or not description.strip() or not system_prompt.strip():
                    st.warning("Name, Description, and System Prompt are required.")
                else:
                    payload = {"name": name, "description": description, "system_prompt": system_prompt, "config": {"llm_provider": llm_provider, "llm_model": llm_model, "embedding_provider": embed_provider, "embedding_model": embed_model, "vector_store": vector_store, "chunker": chunker_name}}
                    with st.spinner("Updating RAG instance..."):
                        result = update_rag(rag_id, payload)
                        if result: st.success(f"Successfully updated RAG: {result['name']}. If core components were changed, re-indexing has begun."); st.session_state.editing_rag_id = None; time.sleep(2); st.rerun()

def render_chat_page():
    rag_id = st.session_state.selected_rag_id
    rag_details = next((rag for rag in get_all_rags() if rag['id'] == rag_id), None)
    if not rag_details: st.error("Could not load RAG details."); time.sleep(2); st.rerun(); return
    st.title(f"💬 Chat with: {rag_details['name']}")
    if st.button("← Back to Management"): st.session_state.selected_rag_id = None; st.rerun()
    if rag_id not in st.session_state.chat_histories or not st.session_state.chat_histories[rag_id]:
        with st.spinner("Loading chat history..."):
            history = get_chat_history(rag_id)
            reconstructed_history = []
            for msg in history:
                sources = msg.get("metadata", {}).get("sources", [])
                reconstructed_history.append({"role": msg["role"], "content": msg["content"], "sources": sources})
            st.session_state.chat_histories[rag_id] = reconstructed_history
    if rag_id not in st.session_state.session_ids: st.session_state.session_ids[rag_id] = None
    with st.sidebar:
        st.header("Knowledge Base"); st.info(f"Manage documents for '{rag_details['name']}'.")
        st.file_uploader("Upload new files", accept_multiple_files=True, key=f"uploader_{rag_id}", on_change=handle_file_upload, args=(rag_id,))
        st.divider(); st.subheader("Ingested Documents")
        with st.spinner("Loading document list..."): documents = get_documents(rag_id)
        if not documents: st.caption("No documents have been ingested yet.")
        else:
            for doc in documents:
                status_icon = "✅" if doc['status'] == 'COMPLETED' else '⏳' if doc['status'] in ['PROCESSING', 'PENDING'] else '❌'
                date_str = datetime.fromisoformat(doc['created_at']).strftime('%b %d, %H:%M')
                st.markdown(f"{status_icon} **{doc['file_name']}** (*{date_str}*)")
    for message in st.session_state.chat_histories.get(rag_id, []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("View Sources"):
                    for i, source in enumerate(message["sources"]):
                        st.info(f"**Source {i+1}:** `{source.get('document_name', 'Unknown')}`\n\n> {source.get('content_snippet', '')}")
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.chat_histories[rag_id].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."): response = post_query(rag_id, prompt, st.session_state.session_ids[rag_id])
            if response:
                full_response = response.get("answer", "Sorry, I encountered an error.")
                message_placeholder.markdown(full_response)
                sources = response.get("sources", [])
                if sources:
                    with st.expander("View Sources"):
                        for i, source in enumerate(sources):
                            st.info(f"**Source {i+1}:** `{source.get('document_name', 'Unknown')}`\n\n> {source.get('content_snippet', '')}")
                st.session_state.session_ids[rag_id] = response.get("session_id")
                st.session_state.chat_histories[rag_id].append({"role": "assistant", "content": full_response, "sources": sources})
            else:
                error_msg = "Failed to get a response from the server."
                message_placeholder.markdown(error_msg)
                st.session_state.chat_histories[rag_id].append({"role": "assistant", "content": error_msg, "sources": []})

# ==============================================================================
# --- Main Application ---
# ==============================================================================
# st.set_page_config(page_title="PRISM", layout="wide")
# st.title("🔮 PRISM: A Multi-Agent Framework")

st.set_page_config(
    page_title="PRISM",
    page_icon="PRISM.png", 
    layout="wide"
)
def get_base64_of_image(image_file):
    with open("PRISM.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_of_image("images/logo.png")

st.markdown(
    f"""
    <style>
    .title-container {{
        display: flex;
        align-items: center;
    }}
    .title-container img {{
        height: 75px;
        margin-right: 12px;
    }}
    </style>
    <div class="title-container">
        <img src="data:image/png;base64,{logo_base64}">
        <h1>PRISM: AI-Powered Data Intelligence</h1>
    </div>
    """,
    unsafe_allow_html=True
)

if "session_id" not in st.session_state:
    reset_session()

session_manager = SessionManager(SESSION_DB_PATH)

# --- Sidebar: Data Source Manager (for PRISM) ---
with st.sidebar:
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
                    default_users = {"postgresql": "nagurshareefshaik", "mysql": "root"}
                    default_dbs = {"postgresql": "healthcare", "mysql": "walmart"}
                    
                    host = st.text_input("Host", "localhost", key="db_host")
                    port = st.number_input("Port", value=default_ports[db_type], key="db_port")
                    username = st.text_input("Username", value=default_users[db_type], key="db_user")
                    password = st.text_input("Password", type="password", key="db_pass")
                    database = st.text_input("Database Name", value=default_dbs[db_type], key="db_name")
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
    
    st.subheader("Configured Data Sources")
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
                            response = requests.post(f"{PRISM_BACKEND_URL}/process_source", json={"source_config": source_data['config']})
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

    st.markdown("---")
    
    st.header("Session Control")
    if st.button("Start New Session"):
        reset_session()
        st.rerun()
    
    st.info(f"**Current Session ID:**")
    st.code(st.session_state.session_id, language=None)
    st.caption("Copy this ID to resume your PRISM session later.")

    with st.form("resume_form"):
        resume_id = st.text_input("Paste PRISM Session ID to Resume")
        if st.form_submit_button("Resume Session"):
            if resume_id:
                loaded_state = session_manager.load_state(resume_id)
                if loaded_state:
                    st.session_state.session_id = resume_id
                    st.session_state.sources = loaded_state.get("sources", {})
                    st.session_state.active_source_name = loaded_state.get("active_source_name")
                    st.session_state.modeling = loaded_state.get("modeling", st.session_state.modeling)
                    st.success("PRISM session resumed successfully!")
                    st.rerun()
                else:
                    st.error("PRISM Session ID not found.")
    
    st.markdown("---")

# ==============================================================================
# --- Main Content Area with Tabs ---
# ==============================================================================
insights_tab, modeling_tab, autorag_tab = st.tabs(["📊 Data Insights", "🤖 Predictive Modeling", "🧠 AutoRAG"])

with insights_tab:
    if not st.session_state.active_source_name:
        st.info("Welcome to PRISM. Please add and analyze a data source from the sidebar to begin your conversation.")
    else:
        active_source = st.session_state.sources[st.session_state.active_source_name]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(f"Chat with: `{st.session_state.active_source_name}`")
        
        if len(active_source.get("messages", [])) > 1:
            with col2:
                if st.button("⬇️ Download as MD (.zip)", use_container_width=True):
                    with st.spinner("Generating Markdown report..."):
                        try:
                            history_for_report = []
                            plot_files_to_zip = []
                            for msg in active_source.get("messages", []):
                                new_msg = msg.copy()
                                if "plot_path" in new_msg and Path(new_msg["plot_path"]).exists():
                                    plot_filename = Path(new_msg["plot_path"]).name
                                    new_msg["plot_path"] = f"assets/{plot_filename}"
                                    plot_files_to_zip.append((new_msg["plot_path"], Path(msg["plot_path"])))
                                history_for_report.append(new_msg)

                            payload = {"source_name": st.session_state.active_source_name, "chat_history": history_for_report}
                            response = requests.post(f"{PRISM_BACKEND_URL}/export_insights_report", json=payload)
                            response.raise_for_status()
                            result = response.json()
                            
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                                zf.writestr("report.md", result.get("report_markdown", ""))
                                for rel_path, abs_path in plot_files_to_zip:
                                    zf.write(abs_path, arcname=rel_path)
                            st.session_state.zip_report_bytes = zip_buffer.getvalue()
                        except requests.RequestException as e:
                            st.error(f"Failed to generate Markdown report: {e}")

        if "pdf_report_bytes" in st.session_state and st.session_state.pdf_report_bytes:
            st.download_button(
                label="Click again to save PDF",
                data=st.session_state.pdf_report_bytes,
                file_name=f"PRISM_Report_{st.session_state.active_source_name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            del st.session_state.pdf_report_bytes

        if "zip_report_bytes" in st.session_state and st.session_state.zip_report_bytes:
            st.download_button(
                label="Click again to save ZIP",
                data=st.session_state.zip_report_bytes,
                file_name=f"PRISM_Report_{st.session_state.active_source_name.replace(' ', '_')}.zip",
                mime="application/zip"
            )
            del st.session_state.zip_report_bytes

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
                        
                        response = requests.post(f"{PRISM_BACKEND_URL}/invoke_insights", json=payload)
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
                        st.write("🤖 Planner agent is analyzing the task and data...")
                        response = requests.post(f"{PRISM_BACKEND_URL}/start_modeling_pipeline", json=payload)
                        response.raise_for_status()
                        result = response.json()
                        
                        st.session_state.modeling["generated_code"] = result.get("generated_code")
                        st.session_state.modeling["requirements_txt"] = result.get("requirements_txt")
                        st.session_state.modeling["readme_md"] = result.get("readme_md")
                        st.session_state.modeling["step_log"] = result.get("step_log", [])
                        st.session_state.modeling["download_path"] = result.get("download_path")
                        
                        status.update(label="Code Generation Complete!", state="complete")
                        st.rerun()
                    except requests.RequestException as e:
                        status.update(label="Generation Failed", state="error")
                        st.error(f"Error: {e.response.json()['detail'] if e.response else e}")

    if st.session_state.modeling.get("generated_code"):
        with st.container(border=True):
            st.subheader("2. Review and Execute Pipeline")
            
            with st.expander("View Agent Steps for Generation"):
                st.markdown("\n".join(f"- {step}" for step in st.session_state.modeling.get("step_log", [])))
            
            code_tab, req_tab, readme_tab = st.tabs(["pipeline.py", "requirements.txt", "README.md"])
            with code_tab:
                st.code(st.session_state.modeling.get("generated_code", ""), language="python")
            with req_tab:
                st.code(st.session_state.modeling.get("requirements_txt", ""), language="text")
            with readme_tab:
                st.markdown(st.session_state.modeling.get("readme_md", ""))

            col1, col2 = st.columns(2)
            with col1:
                download_path = st.session_state.modeling.get("download_path")
                if download_path and Path(download_path).exists():
                    with open(download_path, "rb") as fp:
                        st.download_button(
                            label="Download Project as .zip", data=fp,
                            file_name=f"{st.session_state.session_id}_pipeline.zip",
                            mime="application/zip", use_container_width=True
                        )
            with col2:
                if st.button("🚀 Proceed to Execute & Train Model", use_container_width=True):
                    with st.status("Executing Pipeline...", expanded=True) as status:
                        try:
                            st.write("Sandbox environment is installing dependencies...")
                            st.write("Running the code...")
                            payload = {"session_id": st.session_state.session_id}
                            response = requests.post(f"{PRISM_BACKEND_URL}/execute_modeling_pipeline", json=payload)
                            response.raise_for_status()
                            result = response.json()
                            st.session_state.modeling["execution_results"] = result
                            status.update(label="Execution Complete!", state="complete")
                            st.rerun()
                        except requests.RequestException as e:
                            status.update(label="Execution Failed", state="error")
                            st.error(f"Error: {e.response.json()['detail'] if e.response else e}")
    
    if st.session_state.modeling.get("execution_results"):
        with st.container(border=True):
            st.subheader("3. View Results and Artifacts")
            results = st.session_state.modeling["execution_results"]
            
            st.text_area("Execution Log", results.get("execution_log", ""), height=300)
            
            if results.get("artifacts"):
                st.success("Model and metrics saved successfully!")
                for name, path in results["artifacts"].items():
                    if Path(path).exists():
                        with open(path, "rb") as fp:
                            st.download_button(f"Download {name}", data=fp, file_name=name)
            else:
                st.error("Execution finished, but no artifacts were found. Check the log for details.")

with autorag_tab:
    st.header("AutoRAG: Knowledge Base Chat")
    st.info("This feature connects to a separate AutoRAG backend. Please ensure it is running on port 8000.")
    
    # --- AutoRAG Main Application Router ---
    if st.session_state.get("editing_rag_id") is not None:
        render_edit_page()
    elif st.session_state.get("selected_rag_id") is not None:
        render_chat_page()
    else:
        render_management_page()

# --- Save state at the end of every script run ---
if st.session_state.get("sources"):
    state_to_save = {
        "sources": st.session_state.sources,
        "active_source_name": st.session_state.active_source_name,
        "modeling": st.session_state.modeling
    }
    session_manager.save_state(st.session_state.session_id, state_to_save)