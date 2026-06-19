"""
SQLAlchemy async database models.
Tracks resume metadata, analysis results, and chat sessions.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import StaticPool

from app.config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Resume(Base):
    """Stores uploaded resume file info and extracted profile."""

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chroma_collection_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis", back_populates="resume", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="resume", cascade="all, delete-orphan"
    )


class Analysis(Base):
    """Stores AI analysis results (ATS, skill gap, interview, career, jobs)."""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), nullable=False
    )
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="analyses")


class ChatSession(Base):
    """Groups chat messages into a named conversation per resume."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    resume: Mapped["Resume"] = relationship(
        "Resume", back_populates="chat_sessions"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Individual message stored in a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # NOTE: "metadata" is reserved by SQLAlchemy DeclarativeBase — use extra_data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )


# ─── Engine & Session Factory ─────────────────────────────────────────────────

_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """Return the singleton async engine (creates it on first call)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        kwargs: dict = {"echo": settings.debug}
        if "sqlite" in settings.database_url:
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = StaticPool
        _engine = create_async_engine(settings.database_url, **kwargs)
    return _engine


async def init_db() -> None:
    """Create all tables on application startup."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency: yield a managed async DB session per request."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
