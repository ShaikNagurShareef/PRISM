from typing import List, Dict, Any, Type
from langchain_core.tools import BaseTool
from pydantic import Field

from src.service.modules.vector_stores.base import BaseVectorStore
from src.service.modules.embedders.base import BaseEmbedder
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RetrievalTool(BaseTool):
    """A tool for performing semantic search over a vector store."""
    name: str = "semantic_retriever"
    description: str = (
        "Use this tool to find relevant information and context to answer a user's query. "
        "Provide a concise search query as input to this tool."
    )
    vector_store: BaseVectorStore
    embedder: BaseEmbedder
    last_retrieved_sources: List[Dict[str, Any]] = Field(default_factory=list, exclude=True)

    def _run(self, query: str) -> str:
        """Use the tool."""
        logger.info(f"RetrievalTool activated with query: '{query}'")
        try:
            query_embedding = self.embedder.embed_documents([query])[0]
            
            # We will implement metadata filtering later. For now, it's a direct query.
            results = self.vector_store.query(query_embedding=query_embedding, top_k=4)
            
            # Store the full sources to be used for citation later
            self.last_retrieved_sources = results

            if not results:
                return "No relevant information found in the knowledge base."

            # Format the results into a single string for the LLM
            context_str = ""
            for i, chunk in enumerate(results):
                source_name = chunk.get('metadata', {}).get('filename', 'Unknown')
                page_number = chunk.get('metadata', {}).get('page_number', 'N/A')
                content = chunk.get('text', '')
                
                context_str += f"Source {i+1} (File: {source_name}, Page: {page_number}):\n"
                context_str += f"Content: {content}\n---\n"
            
            logger.info(f"RetrievalTool returning context of length {len(context_str)}")
            return context_str

        except Exception as e:
            logger.error(f"Error during retrieval: {e}", exc_info=True)
            return "An error occurred while trying to retrieve information."

    async def _arun(self, query: str) -> str:
        # For simplicity, we'll just use the synchronous version for now.
        # In a production system, this should be a true async implementation.
        return self._run(query)