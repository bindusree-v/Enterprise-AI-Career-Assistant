"""
Resume service — orchestrates resume processing pipeline.
Uses get_llm() for provider-agnostic AI calls.
"""

import json
import profile
import profile
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.llm_factory import get_llm
from app.logging_config import get_logger
from app.models.database import Analysis, Resume
from app.models.schemas import AnalyzeResumeResponse, StructuredProfile
from app.services.pdf_service import PDFService
from app.vectorstore.chroma_store import ChromaVectorStore
from app.routers import resume
# from backend.app.routers import resume

logger = get_logger(__name__)

ANALYZE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a professional resume reviewer. Analyze this resume and return ONLY valid JSON:
{{
  "profile_summary": "2-3 sentence executive summary",
  "overall_quality_score": <0-100 float>,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"],
  "formatting_feedback": ["formatting observation"],
  "content_feedback": ["content quality observation"],
  "recommended_sections": ["section to add or improve"]
}}""",
    ),
    ("human", "Resume text:\n\n{resume_text}"),
])


class ResumeService:
    def __init__(self, db: AsyncSession, pdf_service: PDFService, vector_store: ChromaVectorStore):
        self.db = db
        self.pdf_service = pdf_service
        self.vector_store = vector_store

    async def get_resume(self, resume_id: str) -> Optional[Resume]:
        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))
        return result.scalar_one_or_none()

    async def get_resume_or_404(self, resume_id: str) -> Resume:
        resume = await self.get_resume(resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")
        return resume

    # async def save_extracted_text(self, resume_id: str, text: str, profile: StructuredProfile) -> Resume:
    #     resume = await self.get_resume_or_404(resume_id)
    #     resume.extracted_text = text
    #     resume.structured_profile = profile.model_dump()
    #     await self.db.commit()
    #     await self.db.refresh(resume)
    #     return resume

    async def save_extracted_text(self, resume_id: str, raw_text: str, profile):
        resume = await self.get_resume_or_404(resume_id)

    # ✅ SAVE RAW TEXT
        resume.extracted_text = raw_text

    # ✅ SAVE PROFILE
        resume.structured_profile = (
            profile.dict() if hasattr(profile, "dict") else profile
    )

    # ✅ COMMIT
        await self.db.commit()

    # ✅ REFRESH
        await self.db.refresh(resume)

        return resume

    async def save_embeddings_info(self, resume_id: str, collection_name: str) -> Resume:
        resume = await self.get_resume_or_404(resume_id)
        resume.chroma_collection_id = collection_name
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def save_analysis(
        self,
        resume_id: str,
        analysis_type: str,
        result: dict,
        score: Optional[float] = None,
        target_role: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Analysis:
        analysis = Analysis(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            analysis_type=analysis_type,
            target_role=target_role,
            job_description=job_description[:500] if job_description else None,
            result=result,
            score=score,
        )
        self.db.add(analysis)
        await self.db.commit()
        return analysis

    async def analyze_resume_quality(
        self, resume_id: str, target_role: Optional[str] = None
    ) -> AnalyzeResumeResponse:
        resume = await self.get_resume_or_404(resume_id)
        if not resume.extracted_text:
            raise ValueError("Text not extracted yet. Call /extract-text first.")

        llm = get_llm(temperature=0)
        chain = ANALYZE_PROMPT | llm | StrOutputParser()
        response = await chain.ainvoke({"resume_text": resume.extracted_text[:6000]})

        content = response.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        result = AnalyzeResumeResponse(
            resume_id=resume_id,
            profile_summary=data.get("profile_summary", ""),
            overall_quality_score=float(data.get("overall_quality_score", 0)),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
            formatting_feedback=data.get("formatting_feedback", []),
            content_feedback=data.get("content_feedback", []),
            recommended_sections=data.get("recommended_sections", []),
        )

        await self.save_analysis(
            resume_id=resume_id,
            analysis_type="analyze",
            result=result.model_dump(),
            score=result.overall_quality_score,
            target_role=target_role,
        )

        logger.info("Resume analysis complete", resume_id=resume_id, score=result.overall_quality_score)
        return result
