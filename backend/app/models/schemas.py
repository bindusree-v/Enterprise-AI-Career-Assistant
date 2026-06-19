"""
Pydantic request/response schemas for all API endpoints.
These define the contract between frontend and backend.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ────────────────────────────────────────────────────────────────────

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"


class AnalysisType(str, Enum):
    ATS = "ats"
    SKILL_GAP = "skill_gap"
    INTERVIEW = "interview"
    CAREER = "career"
    JOBS = "jobs"


# ─── Common Schemas ───────────────────────────────────────────────────────────

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ─── Resume Schemas ───────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    """Response after successful resume upload."""
    resume_id: str
    filename: str
    file_size: int
    message: str = "Resume uploaded successfully"


class StructuredProfile(BaseModel):
    """AI-extracted structured representation of a resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    years_of_experience: Optional[int] = None


class ExtractTextRequest(BaseModel):
    resume_id: str = Field(..., description="Resume ID returned from upload")


class ExtractTextResponse(BaseModel):
    resume_id: str
    text_length: int
    preview: str = Field(..., description="First 500 characters of extracted text")
    structured_profile: StructuredProfile


class GenerateEmbeddingsRequest(BaseModel):
    resume_id: str
    force_regenerate: bool = Field(default=False, description="Force re-embedding even if already stored")


class GenerateEmbeddingsResponse(BaseModel):
    resume_id: str
    chunks_count: int
    collection_name: str
    message: str


# ─── ATS Schemas ─────────────────────────────────────────────────────────────

class ATSRequest(BaseModel):
    resume_id: str
    job_description: str = Field(..., min_length=50, description="Full job description text")
    target_role: Optional[str] = Field(None, description="Specific role title (optional)")


class ATSKeyword(BaseModel):
    keyword: str
    found: bool
    importance: str  # high|medium|low
    context: Optional[str] = None


class ATSResponse(BaseModel):
    resume_id: str
    overall_score: float = Field(..., ge=0, le=100)
    keyword_match_score: float
    format_score: float
    content_score: float
    keywords_found: List[str]
    keywords_missing: List[str]
    keyword_details: List[ATSKeyword]
    recommendations: List[str]
    summary: str


# ─── Skill Gap Schemas ────────────────────────────────────────────────────────

class SkillGapRequest(BaseModel):
    resume_id: str
    target_role: str = Field(..., min_length=3, description="Target job role/title")
    job_description: Optional[str] = Field(None, description="Optional specific job description")
    experience_level: Optional[str] = Field(None, description="junior|mid|senior|lead")


class SkillResource(BaseModel):
    name: str
    url: Optional[str] = None
    type: str  # course|book|certification|project
    duration: Optional[str] = None
    cost: Optional[str] = None  # free|paid|freemium


class SkillGap(BaseModel):
    skill: str
    current_level: str  # none|beginner|intermediate|advanced
    required_level: str
    priority: str  # high|medium|low
    learning_resources: List[SkillResource]


class SkillGapResponse(BaseModel):
    resume_id: str
    target_role: str
    current_skills: List[str]
    required_skills: List[str]
    skill_gaps: List[SkillGap]
    strengths: List[str]
    roadmap: List[str]
    estimated_time_to_ready: str
    certifications_recommended: List[str]


# ─── Interview Schemas ────────────────────────────────────────────────────────

class InterviewRequest(BaseModel):
    resume_id: str
    target_role: str
    job_description: Optional[str] = None
    question_types: List[QuestionType] = Field(
        default=[QuestionType.TECHNICAL, QuestionType.BEHAVIORAL]
    )
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    num_questions: int = Field(default=10, ge=1, le=30)


class InterviewQuestion(BaseModel):
    id: int
    question: str
    type: QuestionType
    difficulty: DifficultyLevel
    topic: str
    hint: Optional[str] = None
    sample_answer: Optional[str] = None
    evaluation_criteria: List[str] = Field(default_factory=list)


class InterviewResponse(BaseModel):
    resume_id: str
    target_role: str
    questions: List[InterviewQuestion]
    preparation_tips: List[str]
    common_pitfalls: List[str]


# ─── Career Advisor Schemas ───────────────────────────────────────────────────

class CareerSuggestionsRequest(BaseModel):
    resume_id: str
    current_role: Optional[str] = None
    career_goals: Optional[str] = Field(None, description="User's stated career goals")
    industry_preference: Optional[str] = None
    location_preference: Optional[str] = None


class CareerPath(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    average_salary: Optional[str] = None
    growth_potential: str  # high|medium|low
    time_to_achieve: str
    steps: List[str]


class CareerSuggestionsResponse(BaseModel):
    resume_id: str
    current_level: str
    career_paths: List[CareerPath]
    industry_trends: List[str]
    growth_opportunities: List[str]
    action_plan: List[str]
    networking_tips: List[str]


# ─── Job Recommendation Schemas ───────────────────────────────────────────────

class JobRecommendationRequest(BaseModel):
    resume_id: str
    target_role: Optional[str] = None
    location: Optional[str] = None
    remote_preference: Optional[str] = None  # remote|hybrid|onsite|any
    experience_level: Optional[str] = None


class JobMatch(BaseModel):
    title: str
    company: str
    location: str
    match_percentage: float = Field(..., ge=0, le=100)
    matching_skills: List[str]
    missing_skills: List[str]
    salary_range: Optional[str] = None
    job_type: str  # full-time|part-time|contract|freelance
    remote: bool
    why_good_fit: str
    apply_url: Optional[str] = None


class JobRecommendationResponse(BaseModel):
    resume_id: str
    total_matches: int
    jobs: List[JobMatch]
    search_strategy: List[str]


# ─── Chat Schemas ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    resume_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)


# ─── Analyze Resume Schema ────────────────────────────────────────────────────

class AnalyzeResumeRequest(BaseModel):
    resume_id: str
    target_role: Optional[str] = None


class AnalyzeResumeResponse(BaseModel):
    resume_id: str
    profile_summary: str
    overall_quality_score: float
    strengths: List[str]
    improvements: List[str]
    formatting_feedback: List[str]
    content_feedback: List[str]
    recommended_sections: List[str]
