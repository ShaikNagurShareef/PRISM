from pathlib import Path
import importlib
import shutil
import zipfile
import json 

from src.config.settings import settings
from src.database.dbservice import DBService
from src.utils.logger import get_logger
from src.utils.guardrails import content_filter
from src.utils.query_rewriter import rewrite_query # <-- Import the new rewriter

# --- Stable LangChain Imports ---
from langchain.retrievers import MultiQueryRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_openai import ChatOpenAI

# --- Parser Imports ---
from src.service.modules.parsers.unstructured_element_parser import UnstructuredElementParser
from src.service.modules.parsers.pymupdf_parser import PyMuPDFParser

# --- Other Project Component Imports ---
from src.service.llm_provider import OpenAI_LLM, Google_LLM, Groq_LLM
from src.service.modules.chunkers.recursive_chunker import RecursiveChunker
from src.service.modules.chunkers.semantic_chunker import SemanticChunker
from src.service.modules.embedders.base import BaseEmbedder
from src.data.models import QueryResponse, SourceCitation
from langchain_community.vectorstores import Chroma

from src.service.agents.export_agent import ExportAgent
from src.service.tools.system_tools import DockerfileWriterTool, DockerBuildTool

logger = get_logger(__name__)

def get_class_from_path(class_path: str):
    """Dynamically imports a class from a string path."""
    module_path, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def get_module_instance(module_type: str, config: dict, rag_id: int, embedder_instance: BaseEmbedder = None):
    """
    Dynamically instantiates modules based on the RAG configuration.
    """
    caps = settings.CAPABILITIES
    
    if module_type == "chunker":
        chunker_name = config.get('chunker', 'recursive')
        chunker_config = caps.available_chunkers[chunker_name]
        ChunkerClass = get_class_from_path(chunker_config.class_path)
        
        if ChunkerClass == SemanticChunker:
            if not embedder_instance:
                raise ValueError("SemanticChunker requires an embedder instance.")
            return ChunkerClass(embedder=embedder_instance)
        else:
            return ChunkerClass()
        
    elif module_type == "embedder":
        provider, model = config['embedding_provider'], config['embedding_model']
        model_config = caps.available_embedders[provider][model]
        EmbedderClass = get_class_from_path(model_config.class_path)
        return EmbedderClass(model_name=model_config.model_name)

    elif module_type == "vector_store":
        if config['vector_store'] == "chroma":
            from src.service.modules.vector_stores.chroma_store import ChromaStore
            return ChromaStore(rag_id=rag_id)
            
    elif module_type == "llm":
        provider = config['llm_provider']
        model_name = caps.available_llms[provider][config['llm_model']].model_name
        
        if provider == "openai": return OpenAI_LLM(model_name=model_name)
        elif provider == "google": return Google_LLM(model_name=model_name)
        elif provider == "groq": return Groq_LLM(model_name=model_name)
        
    raise ValueError(f"Unknown module type or configuration: {module_type}")

class IngestionWorkflow:
    def __init__(self, db_service: DBService, rag_id: int, doc_id: int, file_path: str):
        self.db_service = db_service; self.rag_id = rag_id; self.doc_id = doc_id; self.file_path = file_path
        self.rag_instance = self.db_service.get_rag_instance(self.rag_id)
        if not self.rag_instance: raise ValueError(f"RAG instance with ID {self.rag_id} not found.")
        self.config = self.rag_instance.config_json

    def run(self):
        logger.info(f"Starting ingestion workflow for doc_id: {self.doc_id}, rag_id: {self.rag_id}")
        self.db_service.update_document_status(self.doc_id, "PROCESSING")
        try:
            file_extension = Path(self.file_path).suffix.lower()
            
            if file_extension == ".pdf":
                logger.info(f"PDF file detected. Using reliable PyMuPDFParser.")
                parser = PyMuPDFParser()
            else:
                logger.info(f"Non-PDF file detected ({file_extension}). Using UnstructuredElementParser.")
                parser = UnstructuredElementParser()

            elements = parser.parse(self.file_path)
            
            embedder = get_module_instance("embedder", self.config, self.rag_id)
            chunker = get_module_instance("chunker", self.config, self.rag_id, embedder_instance=embedder)
            chunks = chunker.chunk(elements)
            
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = embedder.embed_documents(chunk_texts)
            
            vector_store = get_module_instance("vector_store", self.config, self.rag_id)
            vector_store.upsert(chunks, embeddings)
            
            self.db_service.update_document_status(self.doc_id, "COMPLETED")
            logger.info(f"Ingestion workflow completed successfully for doc_id: {self.doc_id}")
        except Exception as e:
            logger.error(f"Ingestion workflow failed for doc_id: {self.doc_id}. Error: {e}", exc_info=True)
            self.db_service.update_document_status(self.doc_id, "FAILED")

class QueryWorkflow:
    def __init__(self, db_service: DBService, rag_id: int, query: str, session_id: int = None):
        self.db_service = db_service; self.rag_id = rag_id; self.query = query; self.session_id = session_id
        self.rag_instance = self.db_service.get_rag_instance(self.rag_id)
        if not self.rag_instance: raise ValueError(f"RAG instance with ID {self.rag_id} not found.")
        self.config = self.rag_instance.config_json

    def _rerank_documents(self, query: str, documents: list) -> list:
        """Manually re-ranks documents using a cross-encoder."""
        if not documents:
            return []
        
        logger.info(f"Re-ranking {len(documents)} documents...")
        cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        pairs = [[query, doc.page_content] for doc in documents]
        scores = cross_encoder.score(pairs)
        
        scored_docs = sorted(list(zip(scores, documents)), key=lambda x: x[0], reverse=True)
        
        top_n = 5
        reranked_docs = [doc for score, doc in scored_docs[:top_n]]
        
        logger.info(f"Re-ranking complete. Selected top {len(reranked_docs)} documents.")
        return reranked_docs

    def run(self) -> QueryResponse:
        if content_filter(self.query):
            logger.warning(f"Harmful content detected in user query for RAG ID {self.rag_id}.")
            if self.session_id is None:
                session = self.db_service.create_chat_session(self.rag_id)
                self.session_id = session.id
            self.db_service.add_chat_message(self.session_id, "user", self.query)
            filtered_answer = "I cannot process this request as it violates the safety policy."
            self.db_service.add_chat_message(self.session_id, "assistant", filtered_answer)
            return QueryResponse(answer=filtered_answer, session_id=self.session_id, sources=[])

        if self.session_id is None:
            session = self.db_service.create_chat_session(self.rag_id)
            self.session_id = session.id
            chat_history = []
        else:
            chat_history = self.db_service.get_chat_history(self.session_id)
        
        simple_chat_history = [{"role": msg.role, "content": msg.content} for msg in chat_history]
        self.db_service.add_chat_message(self.session_id, "user", self.query)
        
        llm = get_module_instance("llm", self.config, self.rag_id)
        
        # --- STEP 1: Rewrite query for conversational context ---
        standalone_query = rewrite_query(self.query, simple_chat_history, llm)

        # --- STEP 2: Retrieve and Re-rank using the standalone query ---
        embedder = get_module_instance("embedder", self.config, self.rag_id)
        vector_store_wrapper = get_module_instance("vector_store", self.config, self.rag_id)
        
        lc_vector_store = Chroma(
            client=vector_store_wrapper.client,
            collection_name=vector_store_wrapper.collection_name,
            embedding_function=embedder
        )

        base_retriever = lc_vector_store.as_retriever(search_kwargs={'k': 20})
        query_gen_llm = ChatOpenAI(temperature=0, api_key=settings.OPENAI_API_KEY)
        multi_query_retriever = MultiQueryRetriever.from_llm(
            retriever=base_retriever, llm=query_gen_llm
        )
        initial_docs = multi_query_retriever.invoke(standalone_query)

        reranked_docs = self._rerank_documents(standalone_query, initial_docs)

        # --- STEP 3: Generate final answer ---
        final_context = "\n---\n".join([f"Source (File: {doc.metadata.get('filename', 'Unknown')}):\n{doc.page_content}" for doc in reranked_docs])
        
        system_prompt = self.rag_instance.system_prompt
        guardrail_prompt = """
            ---
            RULES:
            1. You MUST strictly use ONLY the provided context to answer the user's question.
            2. If the answer is not found in the context, you MUST state that you do not have enough information to answer. Do NOT use any external knowledge or make assumptions.
            3. You MUST refuse to answer any questions that are not related to the provided context.
            4. Your answer must be concise and directly address the user's question.
            5. You must not engage in harmful, unethical, or inappropriate conversation.
            """
        
        # The final prompt uses the original query for a natural feel, but the full history for context
        full_prompt = f"{system_prompt}\n{guardrail_prompt}\n\nContext:\n{final_context}\n\nUser Question: {self.query}"
        
        provider_history = [{"role": msg["role"], "content": msg["content"]} for msg in simple_chat_history]
        
        answer = llm.invoke(full_prompt, chat_history=provider_history)

        if content_filter(answer):
            logger.warning(f"Harmful content detected in LLM response for RAG ID {self.rag_id}.")
            answer = "The generated response was filtered due to safety concerns."
            reranked_docs = []

        citations = [SourceCitation(
            document_name=doc.metadata.get('filename', 'Unknown'),
            page_number=doc.metadata.get('page_number'),
            content_snippet=doc.page_content[:250] + "..."
        ) for doc in reranked_docs]
        
        self.db_service.add_chat_message(self.session_id, "assistant", answer, metadata={"sources": [c.model_dump() for c in citations]})
        
        return QueryResponse(answer=answer, session_id=self.session_id, sources=citations)
    
class ExportWorkflow:
    """
    Manages the process of exporting a RAG instance by preparing a build
    context and invoking an autonomous ExportAgent to perform the build.
    """
    def __init__(self, db_service: DBService, rag_id: int):
        self.db_service = db_service
        self.rag_id = rag_id
        self.rag_instance = self.db_service.get_rag_instance(rag_id)
        if not self.rag_instance:
            raise ValueError(f"RAG instance with ID {rag_id} not found.")
        
        self.build_dir = Path(f"./export_build_context_{self.rag_id}")

    def _cleanup(self):
        if self.build_dir.exists(): shutil.rmtree(self.build_dir)

    def _prepare_build_context(self):
        """Creates a directory with all necessary files for the Docker build."""
        self._cleanup()
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.copytree("src", self.build_dir / "src")
        shutil.copy("requirements.txt", self.build_dir / "requirements.txt")
        shutil.copy("autorag_data.db", self.build_dir / "autorag_data.db")
        
        source_kb_path = Path(f"./vector_stores/rag_{self.rag_id}")
        if source_kb_path.exists():
            shutil.copytree(source_kb_path, self.build_dir / "vector_stores" / f"rag_{self.rag_id}")

    def _get_dynamic_dependencies(self):
        # ... (this method is unchanged) ...
        packages = [
            "fastapi", "uvicorn", "pydantic", "langchain", "langchain-openai",
            "langchain-google-genai", "langchain-groq", "chromadb==0.4.24",
            "sentence-transformers", "cross-encoders", "PyMuPDF", "unstructured[local-inference]"
        ]
        env_vars = {"OPENAI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"}
        return sorted(list(packages)), sorted(list(env_vars))

    def run(self) -> str:
        """Prepares context and invokes the ExportAgent to build the Docker image."""
        try:
            self._prepare_build_context()
            
            packages, env_vars = self._get_dynamic_dependencies()
            rag_name_safe = self.rag_instance.name.lower().replace(" ", "-").replace("_", "-")
            
            agent_context = {
                "rag_id": self.rag_id,
                "rag_name": self.rag_instance.name,
                "packages": ", ".join(packages),
                "env_vars": ", ".join(env_vars),
                "image_tag": f"{rag_name_safe}:latest"
            }
            
            # --- THIS IS THE FIX ---
            # Instantiate the tools with the build_path they need to operate on.
            tools = [
                DockerfileWriterTool(build_path=self.build_dir), 
                DockerBuildTool(build_path=self.build_dir)
            ]
            agent = ExportAgent(tools=tools)
            result = agent.invoke(**agent_context)
            
            return result['answer']
        finally:
            self._cleanup()