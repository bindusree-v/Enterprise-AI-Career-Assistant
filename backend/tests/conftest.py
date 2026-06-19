"""
Pytest fixtures and test configuration.

All production dependencies (LangChain, ChromaDB, etc.) are installed.
We mock only AI API calls (OpenAI/embeddings) so tests run fast and offline.
"""

import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# ── Env vars before any app import ──────────────────────────────────────────
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-padding!!")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/chroma-test")
os.environ.setdefault("UPLOAD_DIR", "/tmp/uploads-test")

import pytest                                                     # noqa: E402
import pytest_asyncio                                             # noqa: E402
from httpx import ASGITransport, AsyncClient                     # noqa: E402
from sqlalchemy.ext.asyncio import (                             # noqa: E402
    AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.pool import StaticPool                           # noqa: E402

from app.models.database import Base, get_db                     # noqa: E402
from main import create_app                                      # noqa: E402

pytest_plugins = ("pytest_asyncio",)


# ── Database fixtures ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def test_db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(test_db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ── HTTP client fixture ───────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_db():
        yield test_db_session

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Data fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_pdf_content() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"trailer<</Size 2/Root 1 0 R>>\nstartxref\n60\n%%EOF"
    )


@pytest.fixture()
def sample_resume_text() -> str:
    return (
        "John Doe\nSenior Software Engineer\njohn@example.com\n\n"
        "SKILLS\nPython, FastAPI, Docker, PostgreSQL, AWS\n\n"
        "EXPERIENCE\nSenior Engineer | TechCorp | 2020-Present\n"
        "  - Built REST APIs serving 2M daily users\n"
        "  - Led team of 5 engineers\n\n"
        "EDUCATION\nBS Computer Science | MIT | 2018\n"
    )
