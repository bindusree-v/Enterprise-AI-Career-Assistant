"""
AI Analysis endpoints:
- POST /ats-score
- POST /skill-gap-analysis
- POST /interview-questions
- POST /career-suggestions
- POST /job-recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.ats_agent import ATSAgent
from app.agents.career_advisor_agent import CareerAdvisorAgent
from app.agents.interview_agent import InterviewAgent
from app.agents.job_matching_agent import JobMatchingAgent
from app.agents.skill_gap_agent import SkillGapAgent
from app.logging_config import get_logger
from app.models.database import get_db
from app.models.schemas import (
    ATSRequest,
    ATSResponse,
    CareerSuggestionsRequest,
    CareerSuggestionsResponse,
    InterviewRequest,
    InterviewResponse,
    JobRecommendationRequest,
    JobRecommendationResponse,
    SkillGapRequest,
    SkillGapResponse,
)
from app.services.resume_service import ResumeService
from app.services.pdf_service import PDFService
from app.vectorstore.chroma_store import get_chroma_store

router = APIRouter(prefix="/api", tags=["Analysis"])
logger = get_logger(__name__)


def _check_embeddings_ready(resume, resume_id: str):
    """Raise 400 if embeddings haven't been generated yet."""
    if not resume.chroma_collection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Embeddings not generated for resume {resume_id}. "
                "Call /generate-embeddings first."
            ),
        )


@router.post(
    "/ats-score",
    response_model=ATSResponse,
    summary="ATS Compatibility Score",
    description="Analyze resume against a job description for ATS compatibility.",
)
async def ats_score(
    request: ATSRequest,
    db: AsyncSession = Depends(get_db),
) -> ATSResponse:
    """
    Perform ATS (Applicant Tracking System) analysis.

    - Scores resume-to-JD keyword match (0-100)
    - Identifies missing high-priority keywords
    - Analyzes formatting for ATS compatibility
    - Returns actionable optimization recommendations
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)
    _check_embeddings_ready(resume, request.resume_id)

    agent = ATSAgent()
    result = await agent.analyze(
        resume_id=request.resume_id,
        job_description=request.job_description,
        target_role=request.target_role or "the target role",
    )

    # Persist analysis
    await service.save_analysis(
        resume_id=request.resume_id,
        analysis_type="ats",
        result=result.model_dump(),
        score=result.overall_score,
        target_role=request.target_role,
        job_description=request.job_description,
    )

    return result


@router.post(
    "/skill-gap-analysis",
    response_model=SkillGapResponse,
    summary="Skill Gap Analysis",
    description="Compare resume skills against target role requirements and generate a learning roadmap.",
)
async def skill_gap_analysis(
    request: SkillGapRequest,
    db: AsyncSession = Depends(get_db),
) -> SkillGapResponse:
    """
    Analyze skill gaps for a target role.

    - Compares current skills against role requirements
    - Prioritizes gaps by importance (high/medium/low)
    - Recommends specific courses, certifications, and resources
    - Provides estimated time-to-ready timeline
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)
    _check_embeddings_ready(resume, request.resume_id)

    agent = SkillGapAgent()
    result = await agent.analyze(
        resume_id=request.resume_id,
        target_role=request.target_role,
        job_description=request.job_description,
        experience_level=request.experience_level,
    )

    await service.save_analysis(
        resume_id=request.resume_id,
        analysis_type="skill_gap",
        result=result.model_dump(),
        target_role=request.target_role,
        job_description=request.job_description,
    )

    return result


@router.post(
    "/interview-questions",
    response_model=InterviewResponse,
    summary="Generate Interview Questions",
    description="Generate personalized interview questions based on resume and target role.",
)
async def interview_questions(
    request: InterviewRequest,
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    """
    Generate personalized interview preparation questions.

    - Technical, behavioral, and situational question types
    - Questions reference specific resume experiences
    - Includes sample answers and evaluation criteria
    - Configurable difficulty level and question count
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)
    _check_embeddings_ready(resume, request.resume_id)

    agent = InterviewAgent()
    result = await agent.generate_questions(
        resume_id=request.resume_id,
        target_role=request.target_role,
        question_types=request.question_types,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        job_description=request.job_description,
    )

    await service.save_analysis(
        resume_id=request.resume_id,
        analysis_type="interview",
        result=result.model_dump(),
        target_role=request.target_role,
        job_description=request.job_description,
    )

    return result


@router.post(
    "/career-suggestions",
    response_model=CareerSuggestionsResponse,
    summary="Career Path Suggestions",
    description="Get AI-powered career path recommendations based on profile and goals.",
)
async def career_suggestions(
    request: CareerSuggestionsRequest,
    db: AsyncSession = Depends(get_db),
) -> CareerSuggestionsResponse:
    """
    Generate personalized career path recommendations.

    - Multiple career path options with timelines
    - Industry trend analysis relevant to the profile
    - Concrete action plan with milestones
    - Networking and visibility strategies
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)
    _check_embeddings_ready(resume, request.resume_id)

    agent = CareerAdvisorAgent()
    result = await agent.advise(
        resume_id=request.resume_id,
        current_role=request.current_role,
        career_goals=request.career_goals,
        industry_preference=request.industry_preference,
        location_preference=request.location_preference,
    )

    await service.save_analysis(
        resume_id=request.resume_id,
        analysis_type="career",
        result=result.model_dump(),
        target_role=request.current_role,
    )

    return result


@router.post(
    "/job-recommendations",
    response_model=JobRecommendationResponse,
    summary="Job Recommendations",
    description="Get AI-curated job recommendations with match scores and reasoning.",
)
async def job_recommendations(
    request: JobRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> JobRecommendationResponse:
    """
    Generate personalized job recommendations.

    - Matches profile against relevant job types
    - Calculates honest match percentages
    - Explains why each role is a good fit
    - Includes job search strategy tips
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)
    _check_embeddings_ready(resume, request.resume_id)

    agent = JobMatchingAgent()
    result = await agent.recommend_jobs(
        resume_id=request.resume_id,
        target_role=request.target_role,
        location=request.location,
        remote_preference=request.remote_preference,
        experience_level=request.experience_level,
    )

    await service.save_analysis(
        resume_id=request.resume_id,
        analysis_type="jobs",
        result=result.model_dump(),
        target_role=request.target_role,
    )

    return result
