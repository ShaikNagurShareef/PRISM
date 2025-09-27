from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorStore(ABC):
    def __init__(self, rag_id: int):
        self.rag_id = rag_id

    @abstractmethod
    def upsert(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds or updates documents (chunks) and their embeddings into the store."""
        pass

    @abstractmethod
    def query(self, query_embedding: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Performs a similarity search and returns the top_k most relevant chunks."""
        pass