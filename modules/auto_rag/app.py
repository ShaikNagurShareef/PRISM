from pathlib import Path

import streamlit as st
import requests
import time
import json
from datetime import datetime

from pathlib import Path

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"

# --- Helper Functions for API Calls ---

def get_capabilities():
    """Fetches available model and store configurations from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/rags/capabilities")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching capabilities: {e}. Please ensure the backend API is running.")
        return None

def get_all_rags():
    """Fetches all created RAG instances from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/rags/")
        response.raise_for_status()
        return response.json().get("rags", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching RAGs: {e}")
        return []

def create_rag(payload):
    """Sends a request to the API to create a new RAG instance."""
    try:
        response = requests.post(f"{API_BASE_URL}/rags/", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try:
            error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError:
            error_detail = response.text
        st.error(f"Error creating RAG: {error_detail}")
        return None

def update_rag(rag_id, payload):
    """Sends a request to the API to update a RAG instance."""
    try:
        response = requests.put(f"{API_BASE_URL}/rags/{rag_id}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try:
            error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError:
            error_detail = response.text
        st.error(f"Error updating RAG: {error_detail}")
        return None

def upload_file(rag_id, file):
    """Uploads a single file to a specific RAG instance."""
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/rags/{rag_id}/documents", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "An unknown error occurred."
        try:
            error_detail = response.json().get('detail', str(e))
        except json.JSONDecodeError:
            error_detail = response.text
        st.error(f"Error uploading file '{file.name}': {error_detail}")
        return None

def post_query(rag_id, query, session_id):
    """Posts a query to a RAG instance and gets a response."""
    payload = {"query": query, "session_id": session_id}
    try:
        response = requests.post(f"{API_BASE_URL}/rags/{rag_id}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting response: {e}")
        return None

def delete_rag_instance(rag_id):
    """Sends a request to the API to delete a RAG instance."""
    try:
        response = requests.delete(f"{API_BASE_URL}/rags/{rag_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting RAG: {e}")
        return None

def get_documents(rag_id):
    """Fetches the list of ingested documents for a RAG instance."""
    try:
        response = requests.get(f"{API_BASE_URL}/rags/{rag_id}/documents")
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching documents: {e}")
        return []

def get_chat_history(rag_id):
    """Fetches the chat history for the most recent session of a RAG instance."""
    try:
        response = requests.get(f"{API_BASE_URL}/rags/{rag_id}/chat/history")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching chat history: {e}")
        return []
    
def export_rag(rag_id):
    """Calls the backend to get the zip file content."""
    try:
        response = requests.post(f"{API_BASE_URL}/rags/{rag_id}/export", timeout=300) # Increased timeout for large exports
        response.raise_for_status()
        return response.content # Return the raw bytes of the zip file
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to export RAG: {e}")
        return None
    
def build_rag_image(rag_id):
    """Triggers the backend agent to build a Docker image."""
    try:
        # Using POST as defined in the router
        response = requests.post(f"{API_BASE_URL}/rags/{rag_id}/export")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to trigger image build: {e}")
        return None

# --- Streamlit UI ---

st.set_page_config(page_title="AutoRAG", layout="wide", initial_sidebar_state="expanded")

# # --- NEW: Add Logo to the top of the page ---
# logo_path = Path("assets/autorag_logo.png")
# if logo_path.exists():
#     col1, col2, col3 = st.columns([1, 2, 1]) # Use columns to center the logo
#     with col1:
#         st.image(str(logo_path), width=300)
# else:
#     # Fallback if logo is not found
#     st.title("AutoRAG")

# Initialize session state variables
if 'selected_rag_id' not in st.session_state: st.session_state.selected_rag_id = None
if 'editing_rag_id' not in st.session_state: st.session_state.editing_rag_id = None
if 'session_ids' not in st.session_state: st.session_state.session_ids = {}
if 'chat_histories' not in st.session_state: st.session_state.chat_histories = {}

def handle_file_upload(rag_id):
    """Callback function to handle file uploads, preventing rerun loops."""
    uploader_key = f"uploader_{rag_id}"
    if uploader_key in st.session_state and st.session_state[uploader_key]:
        uploaded_files = st.session_state[uploader_key]
        progress_bar = st.sidebar.progress(0, text="Uploading files...")
        for i, file in enumerate(uploaded_files):
            with st.spinner(f"Uploading '{file.name}'..."):
                result = upload_file(rag_id, file)
                if result:
                    st.toast(f"✅ Successfully uploaded '{file.name}'", icon="🎉")
                else:
                    st.toast(f"❌ Failed to upload '{file.name}'", icon="🔥")
            progress_bar.progress((i + 1) / len(uploaded_files), text=f"Uploaded {i+1}/{len(uploaded_files)}")
        st.sidebar.success("All files processed! Ingestion is happening in the background.")

# --- Page Rendering Functions ---

def render_management_page():
    """Renders the main page for creating and listing RAG instances."""
    st.title("AutoRAG Management Dashboard")

    st.header("🚀 Create a New RAG Instance")
    with st.container(border=True):
        capabilities = get_capabilities()
        if not capabilities:
            st.warning("Could not load platform capabilities. Please ensure the backend is running.")
        else:
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
                        payload = {
                            "name": name, "description": description, "system_prompt": system_prompt,
                            "config": {
                                "llm_provider": llm_provider, "llm_model": llm_model,
                                "embedding_provider": embed_provider, "embedding_model": embed_model,
                                "vector_store": vector_store, "chunker": chunker_name
                            }
                        }
                        with st.spinner("Creating RAG instance..."):
                            result = create_rag(payload)
                            if result:
                                st.success(f"Successfully created RAG: {result['name']}"); time.sleep(1); st.rerun()

    st.divider()
    st.header("📚 Available RAG Instances")
    rag_list = get_all_rags()
    if not rag_list:
        st.info("No RAG instances found. Create one above to get started.")
    else:
        for rag in rag_list:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])
                with col1:
                    st.subheader(rag['name'])
                    st.caption(f"ID: {rag['id']}")
                    st.write(rag['description'] or "_No description provided._")
                    with st.expander("View Configuration"): st.json(rag['config'])
                with col2:
                    if st.button("💬 Chat", key=f"chat_{rag['id']}", use_container_width=True):
                        st.session_state.selected_rag_id = rag['id']; st.rerun()
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{rag['id']}", use_container_width=True):
                        st.session_state.editing_rag_id = rag['id']; st.rerun()
                with col4:
                    if st.button("📦 Build Image", key=f"build_{rag['id']}", use_container_width=True):
                        with st.spinner(f"Agent is building Docker image for '{rag['name']}'... This may take several minutes."):
                            # Use the new, robust helper function
                            result = build_rag_image(rag['id'])
                            
                            # Check if the result is valid and contains the 'message' key
                            if result and 'message' in result:
                                st.success("Agent finished!")
                                st.info("Agent's Final Message:")
                                st.code(result['message'], language='bash')
                            else:
                                # The helper function will have already shown an error toast
                                st.error("Agent failed to build the image. Check the backend logs for details.")
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_{rag['id']}", use_container_width=True, type="secondary"):
                        st.session_state[f"confirm_delete_{rag['id']}"] = True
                
                if st.session_state.get(f"confirm_delete_{rag['id']}", False):
                    st.warning(f"Are you sure you want to delete '{rag['name']}'?", icon="⚠️")
                    c1, c2, c3 = st.columns([1, 1, 4])
                    with c1:
                        if st.button("Yes, delete", key=f"confirm_yes_{rag['id']}", use_container_width=True, type="primary"):
                            with st.spinner(f"Deleting RAG '{rag['name']}'..."):
                                result = delete_rag_instance(rag['id'])
                                if result:
                                    st.success(result['message'])
                                    del st.session_state[f"confirm_delete_{rag['id']}"]
                                    time.sleep(2); st.rerun()
                    with c2:
                        if st.button("Cancel", key=f"confirm_no_{rag['id']}", use_container_width=True):
                            del st.session_state[f"confirm_delete_{rag['id']}"]; st.rerun()

def render_edit_page():
    st.title("✏️ Edit RAG Instance")
    rag_id = st.session_state.editing_rag_id
    rag_details = next((rag for rag in get_all_rags() if rag['id'] == rag_id), None)

    if not rag_details:
        st.error("Could not load RAG details."); time.sleep(2); st.rerun(); return

    if st.button("← Back to Management"):
        st.session_state.editing_rag_id = None; st.rerun()

    with st.container(border=True):
        capabilities = get_capabilities()
        if not capabilities:
            st.warning("Could not load platform capabilities."); return

        st.subheader("1. Core Components")
        st.info("Changing core components (Embedder, Chunker) will trigger a full re-indexing of all documents.")
        
        current_config = rag_details['config']
        llm_providers = list(capabilities["available_llms"].keys())
        embed_providers = list(capabilities["available_embedders"].keys())
        chunker_keys = list(capabilities["available_chunkers"].keys())

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
            vector_store = st.selectbox("Vector Store", list(capabilities["available_vector_stores"].keys()), disabled=True)
            st.caption("Changing the vector store is not currently supported.")
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
                    payload = {
                        "name": name, "description": description, "system_prompt": system_prompt,
                        "config": {
                            "llm_provider": llm_provider, "llm_model": llm_model,
                            "embedding_provider": embed_provider, "embedding_model": embed_model,
                            "vector_store": vector_store, "chunker": chunker_name
                        }
                    }
                    with st.spinner("Updating RAG instance..."):
                        result = update_rag(rag_id, payload)
                        if result:
                            st.success(f"Successfully updated RAG: {result['name']}. If core components were changed, re-indexing has begun.")
                            st.session_state.editing_rag_id = None
                            time.sleep(2); st.rerun()

def render_chat_page():
    rag_id = st.session_state.selected_rag_id
    rag_details = next((rag for rag in get_all_rags() if rag['id'] == rag_id), None)

    if not rag_details:
        st.error("Could not load RAG details."); time.sleep(2); st.rerun(); return

    st.title(f"💬 Chat with: {rag_details['name']}")
    if st.button("← Back to Management"):
        st.session_state.selected_rag_id = None; st.rerun()

    if rag_id not in st.session_state.chat_histories or not st.session_state.chat_histories[rag_id]:
        with st.spinner("Loading chat history..."):
            history = get_chat_history(rag_id)
            reconstructed_history = []
            for msg in history:
                sources = msg.get("metadata", {}).get("sources", [])
                reconstructed_history.append({"role": msg["role"], "content": msg["content"], "sources": sources})
            st.session_state.chat_histories[rag_id] = reconstructed_history
    
    if rag_id not in st.session_state.session_ids:
        st.session_state.session_ids[rag_id] = None

    with st.sidebar:
        st.header("Knowledge Base")
        st.info(f"Manage documents for '{rag_details['name']}'.")
        st.file_uploader("Upload new files", accept_multiple_files=True, key=f"uploader_{rag_id}", on_change=handle_file_upload, args=(rag_id,))
        
        st.divider()
        st.subheader("Ingested Documents")
        with st.spinner("Loading document list..."):
            documents = get_documents(rag_id)
        
        if not documents:
            st.caption("No documents have been ingested yet.")
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
            with st.spinner("Thinking..."):
                response = post_query(rag_id, prompt, st.session_state.session_ids[rag_id])

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

# --- Main Application Router ---
if st.session_state.editing_rag_id is not None:
    render_edit_page()
elif st.session_state.selected_rag_id is not None:
    render_chat_page()
else:
    render_management_page()