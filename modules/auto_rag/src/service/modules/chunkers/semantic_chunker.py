from typing import List, Dict, Any
from langchain_experimental.text_splitter import SemanticChunker as LangChainSemanticChunker
from .base import BaseChunker
from src.service.modules.embedders.base import BaseEmbedder # Import our base embedder
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SemanticChunker(BaseChunker):
    def __init__(self, embedder: BaseEmbedder, breakpoint_threshold_type="percentile"):
        """
        Initializes the SemanticChunker with a pre-configured embedding model instance.
        
        Args:
            embedder: An instance of a class that inherits from BaseEmbedder.
        """
        if not embedder:
            raise ValueError("SemanticChunker requires an initialized embedding model instance.")
        
        # The SemanticChunker from LangChain expects an object that conforms to its Embeddings interface.
        # Our BaseEmbedder is already designed to be compatible.
        self.text_splitter = LangChainSemanticChunker(
            embedder, 
            breakpoint_threshold_type=breakpoint_threshold_type
        )
        logger.info(f"Initialized SemanticChunker with embedder: {embedder.__class__.__name__}")

    def chunk(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Chunking {len(elements)} elements with SemanticChunker")
        all_chunks = []
        
        full_text = "\n\n".join([el.get("content", "") for el in elements])
        
        source_metadata = {}
        if elements:
            source_metadata = elements[0].get("metadata", {})

        semantic_chunks = self.text_splitter.create_documents([full_text])
        
        for i, chunk in enumerate(semantic_chunks):
            chunk_metadata = source_metadata.copy()
            chunk_metadata['element_type'] = 'semantic_chunk'
            chunk_metadata['chunk_index'] = i
            
            all_chunks.append({
                "text": chunk.page_content,
                "metadata": chunk_metadata
            })
            
        logger.info(f"Created {len(all_chunks)} semantic chunks in total.")
        return all_chunks