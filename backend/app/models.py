from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    position = Column(String(50), nullable=True)
    team = Column(String(100), nullable=True, index=True)
    jersey_number = Column(Integer, nullable=True)
    height = Column(String(20), nullable=True)
    weight = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    notes = relationship("Note", back_populates="player", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    game_date = Column(String(50), nullable=True)
    is_important = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Week 2 RAG columns
    # NOTE: Embeddings are now stored in Qdrant vector DB, not PostgreSQL
    text_searchable = Column(TSVECTOR, nullable=True)  # PostgreSQL full-text search for keyword matching

    player = relationship("Player", back_populates="notes")

    # Indexes for RAG performance
    __table_args__ = (
        Index('idx_note_text_search', 'text_searchable', postgresql_using='gin'),
    )


# Week 3: AI Assistant models
class Conversation(Base):
    """Track chat conversations with the AI assistant"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    runs = relationship("Run", back_populates="conversation", cascade="all, delete-orphan", order_by="Run.created_at")


class Run(Base):
    """Track individual assistant runs within a conversation"""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="running")  # running, completed, failed
    assistant_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="runs")
    steps = relationship("RunStep", back_populates="run", cascade="all, delete-orphan", order_by="RunStep.step_number")


class RunStep(Base):
    """Track individual steps/actions during an assistant run"""
    __tablename__ = "run_steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)  # thinking, tool_call, response
    description = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(Text, nullable=True)  # JSON string
    tool_output = Column(Text, nullable=True)  # JSON string or text
    status = Column(String(50), nullable=False, default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("Run", back_populates="steps")
