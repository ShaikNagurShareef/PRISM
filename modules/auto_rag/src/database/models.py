from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json

from src.config.settings import settings

Base = declarative_base()

class RAGInstance(Base):
    __tablename__ = 'rag_instances'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(Text, nullable=False)
    config_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chat_sessions = relationship("ChatSession", back_populates="rag_instance", cascade="all, delete-orphan")
    logs = relationship("PipelineLog", back_populates="rag_instance", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="rag_instance", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    # --- ADDED ondelete="CASCADE" ---
    rag_id = Column(Integer, ForeignKey('rag_instances.id', ondelete="CASCADE"), nullable=False)
    
    rag_instance = relationship("RAGInstance", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    # --- ADDED ondelete="CASCADE" ---
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default={}) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

class PipelineLog(Base):
    __tablename__ = 'pipeline_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    # --- ADDED ondelete="CASCADE" ---
    rag_id = Column(Integer, ForeignKey('rag_instances.id', ondelete="CASCADE"), nullable=False)
    
    step = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details_json = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    rag_instance = relationship("RAGInstance", back_populates="logs")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    rag_id = Column(Integer, ForeignKey('rag_instances.id', ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String(64), nullable=False, index=True) # SHA256 hash
    
    rag_instance = relationship("RAGInstance", back_populates="documents")