from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil

import hashlib
from fastapi import UploadFile, File

from typing import List, Dict, Any

from src.config.settings import settings
from src.database.dbservice import DBService, get_db
from src.data import models as data_models
from src.utils.logger import get_logger
from src.utils.job_manager import run_ingestion_in_background
from src.core.workflow import QueryWorkflow
from fastapi.responses import FileResponse
from src.core.workflow import ExportWorkflow

router = APIRouter(
    prefix="/rags",
    tags=["RAG Management"]
)
logger = get_logger(__name__)

# Create a directory to store uploaded files
UPLOAD_DIR = Path("./uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


def validate_rag_config(config: data_models.RAGConfigRequest):
    """Validates the user's RAG configuration against the platform's capabilities."""
    caps = settings.CAPABILITIES
    
    # Validate LLM
    llm_provider = config.llm_provider
    llm_model = config.llm_model
    if llm_provider not in caps.available_llms or llm_model not in caps.available_llms[llm_provider]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid LLM configuration: {llm_provider}/{llm_model}. Please check available models."
        )

    # Validate Embedding Model
    embed_provider = config.embedding_provider
    embed_model = config.embedding_model
    if embed_provider not in caps.available_embedders or embed_model not in caps.available_embedders[embed_provider]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Embedding configuration: {embed_provider}/{embed_model}. Please check available models."
        )

    # Validate Vector Store
    vector_store = config.vector_store
    if vector_store not in caps.available_vector_stores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Vector Store: {vector_store}. Please check available stores."
        )

@router.post("/", response_model=data_models.RAGInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_rag_instance(
    rag_request: data_models.RAGCreationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new, configurable RAG instance.
    """
    logger.info(f"Received request to create RAG instance: {rag_request.name}")
    
    validate_rag_config(rag_request.config)
    
    dbservice = DBService(db)
    # Using a placeholder class instance to access the model for querying
    RAGInstanceModel = dbservice.get_rag_instance(0).__class__ if dbservice.get_rag_instance(0) is not None else None
    if RAGInstanceModel:
        existing_rag = db.query(RAGInstanceModel).filter_by(name=rag_request.name).first()
        if existing_rag:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A RAG instance with the name '{rag_request.name}' already exists."
            )
        
    try:
        new_rag = dbservice.create_rag_instance(
            name=rag_request.name,
            description=rag_request.description,
            system_prompt=rag_request.system_prompt,
            config=rag_request.config.model_dump()
        )
        logger.info(f"Successfully created RAG instance '{new_rag.name}' with ID {new_rag.id}")
        
        return data_models.RAGInstanceResponse(
            id=new_rag.id,
            name=new_rag.name,
            description=new_rag.description,
            system_prompt=new_rag.system_prompt,
            config=new_rag.config_json
        )
    except Exception as e:
        logger.error(f"Failed to create RAG instance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the RAG instance."
        )

@router.get("/", response_model=data_models.RAGListResponse)
def list_all_rag_instances(db: Session = Depends(get_db)):
    """
    Retrieve a list of all created RAG instances.
    """
    dbservice = DBService(db)
    rags = dbservice.list_rag_instances()
    
    response_rags = [
        data_models.RAGInstanceResponse(
            id=rag.id,
            name=rag.name,
            description=rag.description,
            system_prompt=rag.system_prompt,
            config=rag.config_json
        ) for rag in rags
    ]
    return data_models.RAGListResponse(rags=response_rags)

# --- CRITICAL FIX: STATIC ROUTE BEFORE DYNAMIC ROUTE ---
# The static path "/capabilities" must be defined BEFORE the dynamic path "/{rag_id}"
# to prevent FastAPI from mistakenly interpreting "capabilities" as a rag_id.

@router.get("/capabilities", response_model=dict)
def get_platform_capabilities():
    """
    Retrieve the available models, vector stores, and other configurations
    supported by the platform.
    """
    logger.info("Request received for /rags/capabilities endpoint.")
    try:
        # .model_dump() correctly converts the Pydantic settings object to a dict
        return settings.CAPABILITIES.model_dump()
    except Exception as e:
        logger.error(f"Failed to retrieve or serialize capabilities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load or process platform capabilities."
        )

@router.get("/{rag_id}", response_model=data_models.RAGInstanceResponse)
def get_rag_instance_details(rag_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific RAG instance.
    """
    dbservice = DBService(db)
    rag = dbservice.get_rag_instance(rag_id)
    if not rag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")
    
    return data_models.RAGInstanceResponse(
        id=rag.id,
        name=rag.name,
        description=rag.description,
        system_prompt=rag.system_prompt,
        config=rag.config_json
    )

# --- NEW: Helper function to calculate file hash ---
def calculate_file_hash(file: UploadFile) -> str:
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    # Reset file pointer to the beginning
    file.file.seek(0)
    # Read the file in chunks to handle large files efficiently
    while chunk := file.file.read(8192):
        hasher.update(chunk)
    # Reset file pointer again so it can be saved correctly
    file.file.seek(0)
    return hasher.hexdigest()

# --- Find and REPLACE the upload_document_for_ingestion function ---
@router.post("/{rag_id}/documents", status_code=status.HTTP_202_ACCEPTED)
def upload_document_for_ingestion(
    rag_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for ingestion. Prevents duplicates based on content hash.
    """
    dbservice = DBService(db)
    rag = dbservice.get_rag_instance(rag_id)
    if not rag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")

    try:
        # 1. Calculate the hash of the uploaded file's content
        content_hash = calculate_file_hash(file)
        
        # 2. Check if this exact document already exists for this RAG
        if dbservice.check_document_exists(rag_id=rag_id, content_hash=content_hash):
            logger.warning(f"Duplicate document upload attempted for RAG ID {rag_id}: {file.filename}")
            # Use status 208 Already Reported for clarity
            raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail=f"This exact document ('{file.filename}') has already been ingested into this RAG.")

        # 3. If not a duplicate, proceed with saving and ingestion
        file_location = UPLOAD_DIR / f"{rag_id}_{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        logger.info(f"File '{file.filename}' uploaded and saved to '{file_location}' for RAG ID {rag_id}")

        doc_entry = dbservice.create_document_entry(
            rag_id=rag_id,
            file_name=file.filename,
            storage_path=str(file_location),
            content_hash=content_hash # Save the hash
        )

        run_ingestion_in_background(
            rag_id=rag_id,
            doc_id=doc_entry.id,
            file_path=str(file_location)
        )

        return {"message": "File uploaded successfully. Ingestion has started.", "document_id": doc_entry.id}

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to be handled by FastAPI
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to handle file upload for RAG ID {rag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process file upload.")

@router.post("/{rag_id}/chat", response_model=data_models.QueryResponse)
def chat_with_rag(rag_id: int, query_request: data_models.QueryRequest, db: Session = Depends(get_db)):
    """
    Interact with a RAG instance. This endpoint orchestrates the retrieval,
    reasoning, and generation process.
    """
    dbservice = DBService(db)
    if not dbservice.get_rag_instance(rag_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")

    try:
        workflow = QueryWorkflow(
            db_service=dbservice,
            rag_id=rag_id,
            query=query_request.query,
            session_id=query_request.session_id
        )
        response = workflow.run()
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint for RAG ID {rag_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    
# --- ADD a DELETE endpoint for RAGs ---
@router.delete("/{rag_id}", status_code=status.HTTP_200_OK)
def delete_rag(rag_id: int, db: Session = Depends(get_db)):
    """
    Delete a RAG instance, its vector store collection, and all associated data.
    """
    dbservice = DBService(db)
    if not dbservice.get_rag_instance(rag_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")
    
    try:
        dbservice.delete_rag_instance(rag_id)
        return {"message": f"RAG instance {rag_id} and all its data have been deleted."}
    except Exception as e:
        logger.error(f"Failed to delete RAG instance {rag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete RAG instance.")

# --- ADD an endpoint to list documents ---
@router.get("/{rag_id}/documents", response_model=data_models.DocumentListResponse)
def list_rag_documents(rag_id: int, db: Session = Depends(get_db)):
    """
    List all documents that have been ingested into a specific RAG's knowledge base.
    """
    dbservice = DBService(db)
    if not dbservice.get_rag_instance(rag_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")
    
    docs = dbservice.list_documents_for_rag(rag_id)
    return data_models.DocumentListResponse(documents=docs)

# --- ADD an endpoint to get chat history ---
@router.get("/{rag_id}/chat/history", response_model=List[Dict[str, Any]])
def get_rag_chat_history(rag_id: int, db: Session = Depends(get_db)):
    """
    Get the chat history of the most recent session for a RAG instance.
    """
    dbservice = DBService(db)
    latest_session = dbservice.get_latest_chat_session(rag_id)
    if not latest_session:
        return [] # Return an empty list if no chat history exists
    
    history = dbservice.get_chat_history(latest_session.id)
    return [{"role": msg.role, "content": msg.content, "metadata": msg.metadata_json} for msg in history]

@router.put("/{rag_id}", response_model=data_models.RAGInstanceResponse)
def update_rag(
    rag_id: int,
    update_request: data_models.RAGUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing RAG instance. If core components (embedder, chunker)
    are changed, this will trigger a full re-indexing of all documents.
    """
    dbservice = DBService(db)
    rag = dbservice.get_rag_instance(rag_id)
    if not rag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG instance with ID {rag_id} not found.")

    old_config = rag.config_json
    re_index_required = False

    update_data = update_request.model_dump(exclude_unset=True)
    
    # Check if the config is being updated
    if "config" in update_data and update_data["config"] is not None:
        new_config = update_data["config"]
        # Core components that trigger re-indexing
        core_components = ["embedding_provider", "embedding_model", "chunker"]
        for component in core_components:
            if old_config.get(component) != new_config.get(component):
                re_index_required = True
                break
        
        # Merge new config into old config to preserve any unchanged values
        merged_config = old_config.copy()
        merged_config.update(new_config)
        update_data["config_json"] = merged_config
        del update_data["config"] # Use config_json for the DB model
    
    # Update the RAG instance in the database
    updated_rag = dbservice.update_rag_instance(rag_id, update_data)

    if re_index_required:
        logger.info(f"Re-indexing required for RAG ID {rag_id} due to config change.")
        
        # 1. Delete the old vector store collection
        try:
            client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
            collection_name = f"rag_{rag_id}"
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted old ChromaDB collection '{collection_name}' for re-indexing.")
        except Exception as e:
            logger.warning(f"Could not delete ChromaDB collection for re-indexing. It might not exist. Error: {e}")

        # 2. Trigger background ingestion for all existing documents
        documents_to_reindex = dbservice.list_documents_for_rag(rag_id)
        for doc in documents_to_reindex:
            dbservice.update_document_status(doc.id, "PENDING")
            run_ingestion_in_background(
                rag_id=rag_id,
                doc_id=doc.id,
                file_path=doc.storage_path
            )
        logger.info(f"Queued {len(documents_to_reindex)} documents for re-indexing for RAG ID {rag_id}.")

    return data_models.RAGInstanceResponse(
        id=updated_rag.id,
        name=updated_rag.name,
        description=updated_rag.description,
        system_prompt=updated_rag.system_prompt,
        config=updated_rag.config_json
    )

@router.post("/{rag_id}/export", response_model=Dict[str, str])
def export_rag_as_docker_image(rag_id: int, db: Session = Depends(get_db)):
    """
    Triggers an autonomous agent to build a Docker image for the specified RAG.
    This is a long-running, asynchronous-style operation.
    """
    logger.info(f"Received request to build Docker image for RAG ID {rag_id}")
    try:
        # In a real production system, this would be a background job.
        # For now, we run it synchronously but it could take time.
        export_workflow = ExportWorkflow(db_service=DBService(db), rag_id=rag_id)
        result_message = export_workflow.run()
        
        return {"message": result_message}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export RAG ID {rag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during export.")

