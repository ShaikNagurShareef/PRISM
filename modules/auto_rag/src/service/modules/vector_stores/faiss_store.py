import pickle
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from .base import BaseVectorStore
from src.service.modules.embedders.base import BaseEmbedder
from src.utils.logger import get_logger

logger = get_logger(__name__)
VECTOR_STORE_DIR = Path("./vector_stores")
VECTOR_STORE_DIR.mkdir(exist_ok=True)

class FAISSStore(BaseVectorStore):
    def __init__(self, rag_id: int, embedder: BaseEmbedder):
        super().__init__(rag_id)
        if not embedder:
            raise ValueError("FAISSStore requires an initialized embedding model instance.")
        
        self.embedder = embedder
        self.index_path = VECTOR_STORE_DIR / f"rag_{self.rag_id}.faiss"
        
        if self.index_path.exists():
            try:
                self.store = FAISS.load_local(
                    folder_path=str(VECTOR_STORE_DIR),
                    index_name=f"rag_{self.rag_id}",
                    embeddings=self.embedder,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"FAISS index for RAG ID {rag_id} loaded from disk.")
            except Exception as e:
                logger.error(f"Failed to load FAISS index for RAG ID {rag_id}. Error: {e}")
                self.store = None
        else:
            self.store = None
            logger.info(f"No FAISS index found for RAG ID {rag_id}. A new one will be created on first upsert.")

    def upsert(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Upserts documents with pre-calculated embeddings into the FAISS index.
        """
        if not chunks:
            logger.warning("Upsert called with no chunks to add.")
            return

        # --- THIS IS THE CORE FIX ---
        # We must combine the text content with its pre-calculated embedding
        # into a list of (text, embedding) tuples.
        text_embeddings = list(zip([chunk['text'] for chunk in chunks], embeddings))
        metadatas = [chunk['metadata'] for chunk in chunks]

        try:
            if self.store is None:
                # Create a new index from the pre-calculated embeddings
                self.store = FAISS.from_embeddings(
                    text_embeddings=text_embeddings,
                    embedding=self.embedder,
                    metadatas=metadatas
                )
            else:
                # Add to the existing index using pre-calculated embeddings
                self.store.add_embeddings(
                    text_embeddings=text_embeddings,
                    metadatas=metadatas
                )
            
            # Persist the updated index to disk
            self.store.save_local(
                folder_path=str(VECTOR_STORE_DIR),
                index_name=f"rag_{self.rag_id}"
            )
            logger.info(f"Successfully upserted {len(chunks)} chunks and saved FAISS index for RAG ID {self.rag_id}.")
        except Exception as e:
            logger.error(f"Failed to upsert to FAISS: {e}", exc_info=True)
            raise

    def query(self, query_embedding: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if self.store is None:
            logger.warning(f"Query attempted on non-existent FAISS index for RAG ID {self.rag_id}.")
            return []
        
        if filters:
            logger.warning("FAISS does not support metadata filtering. The 'filters' argument will be ignored.")

        try:
            results = self.store.similarity_search_by_vector_with_relevance_scores(
                embedding=query_embedding,
                k=top_k
            )
            
            retrieved_chunks = []
            for doc, score in results:
                retrieved_chunks.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Failed to query FAISS: {e}")
            return []

    def as_retriever(self, **kwargs):
        """Returns a LangChain compatible retriever instance."""
        if self.store is None:
            from langchain_core.retrievers import BaseRetriever
            class DummyRetriever(BaseRetriever):
                def _get_relevant_documents(self, query, *, run_manager): return []
            return DummyRetriever()
        return self.store.as_retriever(**kwargs)