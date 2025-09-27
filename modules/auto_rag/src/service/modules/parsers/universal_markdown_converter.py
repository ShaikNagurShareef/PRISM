from unstructured.partition.auto import partition
from unstructured.documents.elements import Table
from markdownify import markdownify as md
from .base import BaseParser
from src.utils.logger import get_logger
from pathlib import Path
from typing import List, Dict, Any

logger = get_logger(__name__)

class UniversalMarkdownConverter(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses any document type (PDF, DOCX, etc.) using unstructured's "fast" strategy
        and converts the output into a single, clean Markdown string.
        """
        logger.info(f"Parsing document: {file_path} with UniversalMarkdownConverter (fast strategy)")
        
        try:
            # Use the "fast" strategy to avoid heavy ML models and dependencies
            elements = partition(filename=file_path, strategy="fast")
            
            markdown_parts = []
            for el in elements:
                # For tables, unstructured often provides an HTML representation
                if isinstance(el, Table) and el.metadata.text_as_html:
                    # Convert the HTML table to a Markdown table
                    markdown_table = md(el.metadata.text_as_html)
                    markdown_parts.append(markdown_table)
                # For other elements, just use their text representation
                else:
                    markdown_parts.append(el.text)
            
            # Join all parts into a single Markdown document
            full_markdown_content = "\n\n".join(markdown_parts)
            
            # Return a single element containing the entire document as Markdown
            return [{
                "type": "Markdown",
                "content": full_markdown_content,
                "metadata": {
                    "source": file_path,
                    "filename": Path(file_path).name
                }
            }]

        except Exception as e:
            logger.error(f"Failed to parse {file_path} with UniversalMarkdownConverter: {e}")
            raise