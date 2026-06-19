"""
Base agent — shared LLM, retrieval, and logging for all specialist agents.
Uses get_llm() so the provider (Groq/OpenAI/Anthropic) is config-driven.
"""

from typing import Any, List, Optional

from langchain_core.documents import Document

from app.config import get_settings
from app.llm_factory import get_llm
from app.logging_config import get_logger
from app.vectorstore.chroma_store import get_chroma_store

logger = get_logger(__name__)


class BaseAgent:
    def __init__(self, agent_name: str, temperature: float = 0.1):
        self.agent_name = agent_name
        self.settings = get_settings()
        self.vector_store = get_chroma_store()
        self.temperature = temperature
        self._llm: Optional[Any] = None

    @property
    def llm(self) -> Any:
        if self._llm is None:
            self._llm = get_llm(temperature=self.temperature)
        return self._llm

    async def retrieve_context(self, resume_id: str, query: str, k: int = 5) -> List[Document]:
        return await self.vector_store.similarity_search(resume_id, query, k=k)

    def format_context(self, docs: List[Document]) -> str:
        if not docs:
            return "No resume context available."
        return "\n\n".join(
            f"[Section {i+1}]: {doc.page_content}" for i, doc in enumerate(docs)
        )

    def log_invocation(self, resume_id: str, **kwargs: Any) -> None:
        logger.info(f"{self.agent_name} invoked", resume_id=resume_id, **kwargs)

    def log_result(self, resume_id: str, **kwargs: Any) -> None:
        logger.info(f"{self.agent_name} completed", resume_id=resume_id, **kwargs)
