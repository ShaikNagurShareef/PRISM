from typing import List, Dict, Any
from pathlib import Path
from .base import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MarkdownParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a Markdown document by simply reading its content.
        Returns a list containing a single dictionary representing the whole document.
        """
        logger.info(f"Parsing document: {file_path} using MarkdownParser")
        try:
            p = Path(file_path)
            content = p.read_text(encoding='utf-8')
            
            # We return a single "element" which is the entire document content.
            # The chunker will handle splitting it up.
            return [{
                "type": "Markdown",
                "content": content,
                "metadata": {
                    "source": file_path,
                    "filename": p.name
                }
            }]
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with MarkdownParser: {e}")
            raise