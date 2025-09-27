from typing import List
from litellm import embedding
from .base import BaseEmbedder
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LiteLLMEmbedder(BaseEmbedder):
    def __init__(self, model_name: str):
        self.model_name = model_name
        logger.info(f"Initialized LiteLLMEmbedder with model: {self.model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            response = embedding(model=self.model_name, input=texts)
            # The response object contains a 'data' attribute which is a list of embedding objects
            return [item['embedding'] for item in response.data]
        except Exception as e:
            logger.error(f"Failed to get embeddings with LiteLLM for model {self.model_name}: {e}")
            raise