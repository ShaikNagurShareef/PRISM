from typing import List
from sentence_transformers import SentenceTransformer
from .base import BaseEmbedder
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HuggingFaceEmbedder(BaseEmbedder):
    def __init__(self, model_name: str):
        self.model_name = model_name
        try:
            # This will download the model from Hugging Face Hub the first time it's used
            self.model = SentenceTransformer(model_name)
            logger.info(f"Initialized local HuggingFaceEmbedder with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {self.model_name}: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            # The .tolist() is important to convert numpy arrays to standard lists
            return self.model.encode(texts, show_progress_bar=False).tolist()
        except Exception as e:
            logger.error(f"Failed to get embeddings with SentenceTransformer for model {self.model_name}: {e}")
            raise