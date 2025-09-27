from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from src.core.workflow import IngestionWorkflow
from src.database.dbservice import DBService, SessionLocal
from src.utils.logger import get_logger



logger = get_logger(__name__)
executor = ThreadPoolExecutor(max_workers=4) # Adjust worker count as needed

def run_ingestion_in_background(rag_id: int, doc_id: int, file_path: str):
    """
    Wrapper function to run the ingestion workflow in a separate thread.
    It creates its own database session to ensure thread safety.
    """
    logger.info(f"Submitting ingestion job for doc_id: {doc_id} to background executor.")
    
    def task():
        db_session: Session = SessionLocal()
        try:
            db_service = DBService(db_session)
            workflow = IngestionWorkflow(
                db_service=db_service,
                rag_id=rag_id,
                doc_id=doc_id,
                file_path=file_path
            )
            workflow.run()
        except Exception as e:
            logger.error(f"Background ingestion task failed for doc_id {doc_id}: {e}", exc_info=True)
        finally:
            db_session.close()
            logger.info(f"Background ingestion task finished for doc_id: {doc_id}.")

    executor.submit(task)

# from src.celery_worker import process_document

# def run_ingestion_in_background(rag_id: int, doc_id: int, file_path: str):
#     process_document.delay(rag_id, doc_id, file_path)