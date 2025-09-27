from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from .base_agent import BaseAgent
from src.service.llm_provider import BaseLLM
from src.utils.logger import get_logger

logger = get_logger(__name__)

REACT_PROMPT_TEMPLATE = """
        You are a helpful assistant. Use the provided context and tools to answer the user's query accurately.

        {system_prompt}

        TOOLS:
        ------
        You have access to the following tools:

        {tools}

        To use a tool, please use the following format:
        Thought: Do I need to use a tool? Yes
        Action: The action to take, should be one of [{tool_names}]
        Action Input: The input to the action
        Observation: The result of the action

        When you have a response for the user, or if you do not need to use a tool, you MUST use the format:
        Thought: Do I need to use a tool? No
        Final Answer: [your response here]

        Begin!

        Previous conversation history:
        {chat_history}

        New input: {input}
        {agent_scratchpad}
        """

class ReActAgent(BaseAgent):
    """A ReAct agent that uses tools to answer questions."""
    def __init__(self, llm: BaseLLM, tools: List[BaseTool], system_prompt: str):
        self.tools = tools
        self.system_prompt = system_prompt
        self.agent_executor = self._create_agent_executor(llm)

    def _create_agent_executor(self, llm: BaseLLM) -> AgentExecutor:
        """
        Creates the LangChain AgentExecutor by mapping our custom LLM
        providers to LangChain's own LLM wrappers.
        """
        provider_name = llm.__class__.__name__
        
        if provider_name == "OpenAI_LLM":
            # The .api_key attribute is available on the OpenAI client instance
            lc_llm = ChatOpenAI(model=llm.model_name, temperature=0.1, api_key=str(llm.client.api_key))
        elif provider_name == "Google_LLM":
            # The API key is stored differently in the Google client
            lc_llm = ChatGoogleGenerativeAI(model=llm.model_name, temperature=0.1, google_api_key=llm.client._client._api_key)
        elif provider_name == "Groq_LLM":
            lc_llm = ChatGroq(model_name=llm.model_name, temperature=0.1, groq_api_key=str(llm.client.api_key))
        else:
            raise ValueError(f"Unsupported LLM provider for ReAct Agent: {provider_name}")

        prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE).partial(system_prompt=self.system_prompt)
        agent = create_react_agent(llm=lc_llm, tools=self.tools, prompt=prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the format instructions.",
            max_iterations=5
        )

    def invoke(self, user_input: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"ReActAgent invoked with input: '{user_input}'")
        try:
            # Format history for LangChain agent
            formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
    
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": formatted_history
            })
            
            answer = response.get('output', "I couldn't find an answer.")
            
            # Extract sources from the retrieval tool
            retrieval_tool = next((tool for tool in self.tools if hasattr(tool, 'last_retrieved_sources')), None)
            sources = retrieval_tool.last_retrieved_sources if retrieval_tool else []
            
            return {"answer": answer, "sources": sources}

        except Exception as e:
            logger.error(f"ReActAgent execution failed: {e}", exc_info=True)
            return {"answer": "An error occurred while processing your request.", "sources": []}
