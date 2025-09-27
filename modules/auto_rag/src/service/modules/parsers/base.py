from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a document and extracts elements (text, tables, images).
        Returns a list of dictionaries, where each dict represents an element.
        Example element: {'type': 'text', 'content': '...', 'metadata': {'page_number': 1}}
        """
        pass