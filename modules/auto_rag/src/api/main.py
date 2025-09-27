import os
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional

# --- Import project components ---
from src.api import routers as factory_routers
from src.core.workflow import QueryWorkflow
from src.database.dbservice import DBService, SessionLocal, init_db
from src.utils.logger import get_logger
from src.data.models import QueryRequest, QueryResponse, SourceCitation # Import necessary Pydantic models

logger = get_logger(__name__)

# --- NEW: Detect Run Mode from Environment Variables ---
# Defaults to "factory" mode if the environment variable is not set.
RUN_MODE = os.getenv("AUTORAG_MODE", "factory").lower()
# Defaults to 0 if the environment variable is not set.
STANDALONE_RAG_ID = int(os.getenv("AUTORAG_ID", "0"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info(f"AutoRAG application starting up in '{RUN_MODE}' mode...")
    # Only initialize the database (create tables) if running in factory mode.
    # In standalone mode, we assume the DB file is already present.
    if RUN_MODE == "factory":
        init_db()
    yield
    logger.info("AutoRAG application shutting down.")

app = FastAPI(
    title=f"AutoRAG ({RUN_MODE.capitalize()} Mode)",
    description="An automated platform for creating and managing RAG pipelines.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
# Allows the frontend (Streamlit or a custom web app) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for development flexibility
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods
    allow_headers=["*"], # Allows all headers
)

# --- NEW: Conditional Routing based on Run Mode ---
if RUN_MODE == "standalone" and STANDALONE_RAG_ID > 0:
    # --- Standalone RAG Mode ---
    # In this mode, we only expose a minimal, high-performance chat endpoint.
    
    standalone_router = APIRouter()

    @standalone_router.post("/chat", response_model=QueryResponse)
    async def chat(request: QueryRequest):
        """
        Main chat endpoint for the standalone RAG. All requests are routed
        to the pre-configured RAG ID.
        """
        db_session = SessionLocal()
        try:
            db_service = DBService(db_session)
            
            # Instantiate and run the full, powerful QueryWorkflow from our project
            workflow = QueryWorkflow(
                db_service=db_service,
                rag_id=STANDALONE_RAG_ID,
                query=request.query,
                session_id=request.session_id
            )
            response = workflow.run()
            
            # The response from the workflow already matches the Pydantic model
            return response
            
        except Exception as e:
            logger.error(f"Error in standalone chat endpoint for RAG ID {STANDALONE_RAG_ID}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db_session.close()

    @standalone_router.get("/")
    def health_check():
        rag_name = "Unknown"
        db_session = SessionLocal()
        try:
            rag_instance = DBService(db_session).get_rag_instance(STANDALONE_RAG_ID)
            if rag_instance:
                rag_name = rag_instance.name
        finally:
            db_session.close()
        
        return {"status": "ok", "mode": "standalone", "rag_id": STANDALONE_RAG_ID, "rag_name": rag_name}

    app.include_router(standalone_router)

else:
    # --- Factory Mode (our existing development/management application) ---
    # In this mode, we expose all the management routers.
    
    app.include_router(factory_routers.router)
    
    @app.get("/", tags=["Health Check"])
    def read_root():
        """Root endpoint for the factory health check."""
        return {"status": "ok", "mode": "factory"}