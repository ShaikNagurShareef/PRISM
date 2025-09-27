import shutil
import chromadb
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any

from src.config.settings import settings
from src.database.models import Base, RAGInstance, ChatSession, ChatMessage, PipelineLog, Document
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Setup Engine and Session
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

VECTOR_STORE_DIR = Path("./vector_stores") # Make sure this is defined

def init_db():
    """Initializes the database and creates all tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

# Dependency function for FastAPI to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DBService:
    """Service layer for all database operations."""

    def __init__(self, db: Session):
        self.db = db

    # --- RAG Instance Management ---
    def create_rag_instance(self, name: str, description: str, system_prompt: str, config: Dict[str, Any]) -> RAGInstance:
        try:
            new_rag = RAGInstance(
                name=name,
                description=description,
                system_prompt=system_prompt,
                config_json=config
            )
            self.db.add(new_rag)
            self.db.commit()
            self.db.refresh(new_rag)
            logger.info(f"Created new RAG instance: {name} (ID: {new_rag.id})")
            return new_rag
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating RAG instance: {e}")
            raise

    def delete_rag_instance(self, rag_id: int) -> bool:
        """Deletes a RAG instance and all its associated data from the DB and filesystem."""
        rag_instance = self.get_rag_instance(rag_id)
        if not rag_instance:
            return False
        
        try:
            # 1. Delete the ChromaDB collection
            try:
                client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
                collection_name = f"rag_{rag_id}"
                client.delete_collection(name=collection_name)
                logger.info(f"Deleted ChromaDB collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not delete ChromaDB collection for RAG ID {rag_id}. It might not exist. Error: {e}")

            # 2. Delete associated uploaded files
            for doc in rag_instance.documents:
                try:
                    file_path = Path(doc.storage_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {doc.storage_path}. Error: {e}")

            # 3. Delete the RAG instance from the database (cascades will handle the rest)
            self.db.delete(rag_instance)
            self.db.commit()
            logger.info(f"Successfully deleted RAG instance ID {rag_id} from the database.")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting RAG instance ID {rag_id}: {e}")
            raise

    def list_documents_for_rag(self, rag_id: int) -> List[Document]:
        """Lists all documents associated with a specific RAG instance."""
        return self.db.query(Document).filter(Document.rag_id == rag_id).order_by(Document.created_at.desc()).all()

    def get_latest_chat_session(self, rag_id: int) -> Optional[ChatSession]:
        """Finds the most recent chat session for a given RAG."""
        return self.db.query(ChatSession).filter(ChatSession.rag_id == rag_id).order_by(ChatSession.id.desc()).first()

    def get_rag_instance(self, rag_id: int) -> Optional[RAGInstance]:
        return self.db.query(RAGInstance).filter(RAGInstance.id == rag_id).first()

    def list_rag_instances(self) -> List[RAGInstance]:
        return self.db.query(RAGInstance).all()

    # --- Chat History Management ---
    def create_chat_session(self, rag_id: int) -> ChatSession:
        session = ChatSession(rag_id=rag_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_chat_message(self, session_id: int, role: str, content: str, metadata: Dict = {}) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=metadata
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_history(self, session_id: int) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()

    # --- Logging ---
    def log_pipeline_event(self, rag_id: int, step: str, status: str, details: Dict = {}):
        log_entry = PipelineLog(
            rag_id=rag_id,
            step=step,
            status=status,
            details_json=details
        )
        self.db.add(log_entry)
        # Note: We commit logs immediately to ensure they are saved even if the main transaction fails
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit log entry: {e}")
            self.db.rollback()
            
    # --- Document Tracking ---
    def create_document_entry(self, rag_id: int, file_name: str, storage_path: str) -> Document:
        doc = Document(rag_id=rag_id, file_name=file_name, storage_path=storage_path, status="PENDING")
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def update_document_status(self, doc_id: int, status: str, details: Dict = {}):
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = status
            if details:
                # Simple way to append details to the document entry if needed
                pass 
            self.db.commit()

    def check_document_exists(self, rag_id: int, content_hash: str) -> bool:
        """Checks if a document with the given hash already exists for the RAG."""
        doc = self.db.query(Document).filter_by(rag_id=rag_id, content_hash=content_hash).first()
        return doc is not None

    def create_document_entry(self, rag_id: int, file_name: str, storage_path: str, content_hash: str) -> Document:
        """Creates a new document record in the database, now including the hash."""
        doc = Document(
            rag_id=rag_id, 
            file_name=file_name, 
            storage_path=storage_path, 
            content_hash=content_hash, # <-- Add hash
            status="PENDING"
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def update_rag_instance(self, rag_id: int, updates: Dict[str, Any]) -> Optional[RAGInstance]:
        """Updates an existing RAG instance with new data."""
        rag_instance = self.get_rag_instance(rag_id)
        if not rag_instance:
            return None
        
        try:
            for key, value in updates.items():
                if value is not None: # Only update fields that are provided
                    setattr(rag_instance, key, value)
            
            self.db.commit()
            self.db.refresh(rag_instance)
            logger.info(f"Updated RAG instance ID {rag_id} with new data.")
            return rag_instance
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating RAG instance ID {rag_id}: {e}")
            raise