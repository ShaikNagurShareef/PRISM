from celery import Celery
from sqlalchemy.orm import Session
from src.core.workflow import IngestionWorkflow
from src.database.dbservice import DBService, SessionLocal

celery_app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

@celery_app.task
def process_document(rag_id: int, doc_id: int, file_path: str):
    db_session: Session = SessionLocal()
    try:
        db_service = DBService(db_session)
        workflow = IngestionWorkflow(db_service, rag_id, doc_id, file_path)
        workflow.run()
    finally:
        db_session.close()