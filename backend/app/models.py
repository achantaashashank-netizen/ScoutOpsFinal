from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Index, ARRAY, REAL
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
    embedding = Column(ARRAY(REAL), nullable=True)  # all-MiniLM-L6-v2 produces 384-dim vectors (stored as array)
    text_searchable = Column(TSVECTOR, nullable=True)  # PostgreSQL full-text search

    player = relationship("Player", back_populates="notes")

    # Indexes for RAG performance
    __table_args__ = (
        Index('idx_note_text_search', 'text_searchable', postgresql_using='gin'),
    )
