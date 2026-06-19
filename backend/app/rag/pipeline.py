"""
Core RAG pipeline — retrieve from ChromaDB, augment prompt, generate with configured LLM.
Provider is driven by LLM_PROVIDER in .env (groq | openai | anthropic).
"""

from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.llm_factory import get_llm
from app.logging_config import get_logger
from app.vectorstore.chroma_store import get_chroma_store

logger = get_logger(__name__)


def format_docs(docs: List[Document]) -> str:
    if not docs:
        return "No relevant context found."
    return "\n\n---\n\n".join(
        f"[Chunk {i+1}]:\n{doc.page_content}" for i, doc in enumerate(docs)
    )


CHAT_RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are CareerGPT, an expert AI career assistant. You help users improve their careers,
optimize their resumes, prepare for interviews, and identify skill gaps.

Use the provided resume context to give personalized, specific advice.
Be actionable, encouraging, and professional.

Resume Context:
{context}

Guidelines:
- Reference specific details from the resume when relevant
- Provide concrete, actionable recommendations
- Be encouraging but honest about areas for improvement
- Format your response clearly with sections if needed""",
    ),
    ("human", "{question}"),
])


class RAGPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = get_chroma_store()
        self._llm: Optional[Any] = None

    @property
    def llm(self) -> Any:
        if self._llm is None:
            self._llm = get_llm(temperature=0.3)
        return self._llm

    async def retrieve(self, resume_id: str, query: str, k: int = 5) -> List[Document]:
        return await self.vector_store.similarity_search(resume_id, query, k=k)

    async def generate(
        self,
        resume_id: str,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        k: int = 5,
    ) -> Dict[str, Any]:
        docs = await self.retrieve(resume_id, question, k=k)
        context = format_docs(docs)

        messages = [("system", CHAT_RAG_PROMPT.messages[0].prompt.template)]

        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append((msg["role"], msg["content"]))

        messages.append(("human", question))

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | self.llm | StrOutputParser()
        response = await chain.ainvoke({"context": context, "question": question})

        sources = list({str(doc.metadata.get("chunk_index", "")) for doc in docs})
        sources_str = [f"Resume chunk {s}" for s in sources if s]

        logger.info(
            "RAG response generated",
            resume_id=resume_id,
            provider=self.settings.llm_provider,
            model=self.settings.active_model,
        )

        return {"answer": response, "sources": sources_str, "context_used": len(docs)}


_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
