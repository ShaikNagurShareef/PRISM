from abc import ABC, abstractmethod
from typing import Any, Dict, List
from openai import OpenAI
import google.generativeai as genai
from groq import Groq

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BaseLLM(ABC):
    """Abstract Base Class for all LLM providers."""
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.client = self._initialize_client(**kwargs)

    @abstractmethod
    def _initialize_client(self, **kwargs) -> Any:
        """Initializes the specific provider's client."""
        pass

    @abstractmethod
    def invoke(self, prompt: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Sends a request to the LLM and returns the response text."""
        pass

class OpenAI_LLM(BaseLLM):
    """LLM provider for OpenAI models."""
    def _initialize_client(self, **kwargs) -> OpenAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        return OpenAI(api_key=settings.OPENAI_API_KEY)

    def invoke(self, prompt: str, chat_history: List[Dict[str, str]] = None) -> str:
        messages = (chat_history or []) + [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                # temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return "Error: Could not get a response from OpenAI."

class Google_LLM(BaseLLM):
    """LLM provider for Google Gemini models."""
    def _initialize_client(self, **kwargs) -> genai.GenerativeModel:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in the environment.")
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel(self.model_name)

    def invoke(self, prompt: str, chat_history: List[Dict[str, str]] = None) -> str:
        history = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        chat = self.client.start_chat(history=history)
        try:
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Google Gemini API call failed: {e}")
            return "Error: Could not get a response from Google Gemini."

class Groq_LLM(BaseLLM):
    """LLM provider for Groq models."""
    def _initialize_client(self, **kwargs) -> Groq:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in the environment.")
        return Groq(api_key=settings.GROQ_API_KEY)

    def invoke(self, prompt: str, chat_history: List[Dict[str, str]] = None) -> str:
        messages = (chat_history or []) + [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return "Error: Could not get a response from Groq."