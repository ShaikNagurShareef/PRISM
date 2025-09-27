import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PyMuPDFParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a PDF document using PyMuPDF to extract text page by page.
        This is a lightweight and reliable alternative to unstructured for text.
        """
        logger.info(f"Parsing document: {file_path} with PyMuPDFParser")
        
        try:
            doc = fitz.open(file_path)
            elements = []
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():  # Only add pages that have text content
                    elements.append({
                        "type": "NarrativeText",
                        "content": text,
                        "metadata": {
                            "source": file_path,
                            "filename": Path(file_path).name,
                            "page_number": page_num + 1
                        }
                    })
            doc.close()
            return elements
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with PyMuPDFParser: {e}")
            raise