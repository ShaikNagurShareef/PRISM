from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAgent(ABC):
    """Abstract Base Class for all agents."""
    @abstractmethod
    def invoke(self, user_input: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        The main method to run the agent.
        Should return a dictionary with at least an 'answer' and 'sources'.
        """
        pass