from unstructured.partition.auto import partition
from .base import BaseParser
from src.utils.logger import get_logger
from typing import List, Dict, Any
from pathlib import Path

logger = get_logger(__name__)
IMAGE_OUTPUT_DIR = Path("./extracted_images")
IMAGE_OUTPUT_DIR.mkdir(exist_ok=True)

class UnstructuredElementParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses any document, extracts structured elements, and saves images.
        """
        logger.info(f"Parsing document: {file_path} with UnstructuredElementParser")
        
        # Define a unique directory for this document's images to avoid name collisions
        doc_stem = Path(file_path).stem
        doc_image_dir = IMAGE_OUTPUT_DIR / doc_stem
        doc_image_dir.mkdir(exist_ok=True)

        try:
            # Key flags to enable image extraction
            elements = partition(
                filename=file_path, 
                strategy="fast",
                extract_images_in_pdf=True,
                image_output_dir_path=str(doc_image_dir)
            )
            
            dict_elements = []
            for el in elements:
                element_dict = {
                    "type": el.category,
                    "content": str(el),
                    "metadata": el.metadata.to_dict()
                }
                # Capture the path if an image was extracted for this element
                if el.metadata.image_path:
                    element_dict["metadata"]["image_path"] = el.metadata.image_path
                dict_elements.append(element_dict)
            
            return dict_elements
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with UnstructuredElementParser: {e}")
            raise