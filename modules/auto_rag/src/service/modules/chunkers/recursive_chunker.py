from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from markdownify import markdownify as md
from .base import BaseChunker # Corrected relative import
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def chunk(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Chunking {len(elements)} elements with RecursiveChunker")
        all_chunks = []
        for element in elements:
            content = element.get("content", "")
            metadata = element.get("metadata", {})
            element_type = element.get("type", "Unknown")

            # Special handling for images
            if element_type == "Image":
                # For an image element, create a single chunk describing it
                image_path = metadata.get("image_path", "")
                # The content is the caption, if it exists
                image_description = f"This is an image with the following caption: {content}"
                metadata['element_type'] = "Image"
                all_chunks.append({
                    "text": image_description,
                    "metadata": metadata
                })
                continue # Move to the next element

            # Handle tables by converting their HTML to clean Markdown
            if element_type == "Table" and metadata.get("text_as_html"):
                content = md(metadata["text_as_html"])

            # Default behavior: split text-based elements
            text_chunks = self.text_splitter.split_text(content)
            
            for text_chunk in text_chunks:
                chunk_metadata = metadata.copy()
                chunk_metadata['element_type'] = element_type
                
                all_chunks.append({
                    "text": text_chunk,
                    "metadata": chunk_metadata
                })
                
        logger.info(f"Created {len(all_chunks)} chunks in total.")
        return all_chunks