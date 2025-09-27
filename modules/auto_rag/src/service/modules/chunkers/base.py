from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of document elements and splits them into smaller chunks.
        It should preserve and enrich the metadata.
        Returns a list of chunks, where each chunk is a dictionary.
        Example chunk: {'text': '...', 'metadata': {'page_number': 1, 'element_type': 'text'}}
        """
        pass