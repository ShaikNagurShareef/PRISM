from src.service.llm_provider import BaseLLM
from src.utils.logger import get_logger

logger = get_logger(__name__)

REWRITE_PROMPT_TEMPLATE = """
        Given the following conversation history and a follow-up user question, rephrase the follow-up question to be a standalone question that captures the full context of the conversation.

        If the follow-up question is already a standalone question, just return it as is.

        Chat History:
        {chat_history}

        Follow-up Question: {question}

        Standalone Question:
        """

def rewrite_query(query: str, chat_history: list, llm: BaseLLM) -> str:
    """
    Rewrites a user's query to be standalone based on chat history.
    """
    if not chat_history:
        return query

    # Format history for the prompt
    formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
    
    prompt = REWRITE_PROMPT_TEMPLATE.format(chat_history=formatted_history, question=query)
    
    logger.info("Rewriting query for conversational context...")
    
    # We don't need chat history for this specific, single-turn invoke call
    rewritten_query = llm.invoke(prompt)
    
    # Clean up the response, as LLMs can sometimes add extra text
    rewritten_query = rewritten_query.strip().replace("Standalone Question:", "").strip()
    
    logger.info(f"Original query: '{query}' | Rewritten query: '{rewritten_query}'")
    
    return rewritten_query