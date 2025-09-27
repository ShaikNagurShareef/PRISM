from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from .base_agent import BaseAgent
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

EXPORT_AGENT_PROMPT_TEMPLATE = """
Your mission is to create a self-contained, deployable Docker image for a specific AutoRAG instance.

You have access to the following tools:
{tools}

To use a tool, please use the following format:
Thought: Do I need to use a tool? Yes
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action, as a JSON blob.
Observation: The result of the action

When you have a response for the user, you MUST use the format:
Thought: Do I need to use a tool? No
Final Answer: [your final response to the user]

Here is the critical information for the RAG instance you need to package:
- RAG ID: {rag_id}
- RAG Name: {rag_name}
- Required Python Packages: {packages}
- Required Environment Variables for API keys: {env_vars}
- Desired Image Tag: {image_tag}

The build context and necessary files have already been prepared for you.

Follow these steps precisely:
1.  **Construct the Dockerfile content.** Based on the information provided, create the full text for a valid Dockerfile. It must set `AUTORAG_MODE="standalone"` and `AUTORAG_ID="{rag_id}"`.
2.  **Write the Dockerfile.** Use the `dockerfile_writer` tool. The *only* input it needs is the `content` of the Dockerfile you just constructed.
3.  **Build the image.** Once the Dockerfile is written, use the `docker_image_builder` tool. The *only* input it needs is the `image_tag` provided above.
4.  **Final Answer.** If the build is successful, your final answer should be the success message from the `docker_image_builder` tool.

Begin!

User's Request: {input}
{agent_scratchpad}
"""

class ExportAgent(BaseAgent):
    def __init__(self, tools: List[BaseTool]):
        self.agent_executor = self._create_agent_executor(tools)

    def _create_agent_executor(self, tools: List[BaseTool]) -> AgentExecutor:
        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
        prompt = PromptTemplate.from_template(EXPORT_AGENT_PROMPT_TEMPLATE)
        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def invoke(self, user_input: str = "", chat_history: List = None, **kwargs) -> Dict[str, Any]:
        logger.info(f"ExportAgent invoked for RAG ID: {kwargs.get('rag_id')}")
        try:
            # --- THIS IS THE CRITICAL FIX ---
            # The input dictionary for the agent MUST contain the 'input' key.
            # We will add it here. The other context is passed in kwargs.
            agent_inputs = kwargs.copy()
            agent_inputs["input"] = user_input or "Start the export process."

            response = self.agent_executor.invoke(agent_inputs)
            
            return {"answer": response.get('output', "Agent finished with no output."), "sources": []}
        except Exception as e:
            logger.error(f"ExportAgent execution failed: {e}", exc_info=True)
            return {"answer": f"An error occurred during the export process: {e}", "sources": []}