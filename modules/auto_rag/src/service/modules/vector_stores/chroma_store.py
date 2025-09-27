import chromadb
import json
from typing import List, Dict, Any
from pathlib import Path
from .base import BaseVectorStore # Corrected relative import
from src.utils.logger import get_logger

logger = get_logger(__name__)
VECTOR_STORE_DIR = Path("./vector_stores")
VECTOR_STORE_DIR.mkdir(exist_ok=True)

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitizes a metadata dictionary to ensure all values are
    ChromaDB-compatible (str, int, float, bool). Converts complex types
    like dicts, lists, and tuples into JSON strings.
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            sanitized[key] = value
        elif isinstance(value, (dict, list, tuple)):
            # Convert complex types to a JSON string representation
            try:
                sanitized[key] = json.dumps(value)
            except TypeError:
                # Fallback for non-serializable objects
                sanitized[key] = str(value)
        else:
            # For any other unsupported type, convert to a simple string
            sanitized[key] = str(value)
    return sanitized

class ChromaStore(BaseVectorStore):
    def __init__(self, rag_id: int):
        super().__init__(rag_id)
        self.client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        self.collection_name = f"rag_{self.rag_id}"
        try:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"Chroma collection '{self.collection_name}' loaded/created.")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma collection for RAG ID {rag_id}: {e}")
            raise

    def upsert(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks:
            logger.warning("Upsert called with no chunks to add.")
            return

        documents = [chunk['text'] for chunk in chunks]
        
        # --- THIS IS THE FIX ---
        # Sanitize the metadata for each chunk before upserting
        sanitized_metadatas = [sanitize_metadata(chunk['metadata']) for chunk in chunks]
        
        # Generate unique IDs for each chunk to prevent collisions
        # A simple counter is fine for a single ingestion, but a more robust
        # strategy like hashing the content might be better for production.
        start_id = self.collection.count()
        ids = [f"chunk_{self.rag_id}_{start_id + i}" for i in range(len(documents))]

        try:
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=sanitized_metadatas, # Use the sanitized metadata
                ids=ids
            )
            logger.info(f"Successfully upserted {len(documents)} chunks to Chroma collection '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"Failed to upsert to Chroma: {e}", exc_info=True)
            raise

    def query(self, query_embedding: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            retrieved_chunks = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    retrieved_chunks.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i],
                        "score": results['distances'][0][i]
                    })
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Failed to query Chroma: {e}")
            return []