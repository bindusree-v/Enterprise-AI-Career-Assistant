"""
Agent 1: ATS (Applicant Tracking System) Analyzer
Scores resumes against job descriptions, identifies missing keywords,
and provides actionable optimization recommendations.
"""

import json
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import BaseAgent
from app.models.schemas import ATSKeyword, ATSResponse


ATS_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert ATS (Applicant Tracking System) analyst with deep knowledge of
how Fortune 500 companies screen resumes. Analyze the resume against the job description
and provide a comprehensive ATS compatibility assessment.

Return ONLY valid JSON — no markdown, no explanation:
{{
  "overall_score": <0-100 float>,
  "keyword_match_score": <0-100 float>,
  "format_score": <0-100 float>,
  "content_score": <0-100 float>,
  "keywords_found": ["keyword1", "keyword2"],
  "keywords_missing": ["missing1", "missing2"],
  "keyword_details": [
    {{
      "keyword": "Python",
      "found": true,
      "importance": "high",
      "context": "mentioned in skills and experience sections"
    }}
  ],
  "recommendations": [
    "Add quantified achievements (e.g., 'Increased performance by 40%')",
    "Include missing keywords: Docker, Kubernetes"
  ],
  "summary": "2-3 sentence overall assessment"
}}

Scoring criteria:
- keyword_match_score: % of important JD keywords found in resume
- format_score: ATS-friendly formatting (no tables, proper sections, etc.)
- content_score: Relevance and quality of experience/achievements
- overall_score: Weighted average (keywords 50%, content 35%, format 15%)""",
    ),
    (
        "human",
        """Job Description:
{job_description}

Resume Content:
{resume_context}

Target Role: {target_role}

Analyze the ATS compatibility thoroughly.""",
    ),
])


class ATSAgent(BaseAgent):
    """Analyzes resume-to-job-description ATS compatibility."""

    def __init__(self):
        super().__init__(agent_name="ATSAgent", temperature=0.0)

    async def analyze(
        self,
        resume_id: str,
        job_description: str,
        target_role: str = "the target role",
    ) -> ATSResponse:
        """
        Perform full ATS analysis of resume against job description.

        Args:
            resume_id: Resume identifier for vector retrieval
            job_description: Full text of the job posting
            target_role: Human-readable role title

        Returns:
            ATSResponse with score breakdown and recommendations
        """
        self.log_invocation(resume_id, target_role=target_role)

        # Retrieve relevant resume content
        docs = await self.retrieve_context(
            resume_id,
            f"skills experience qualifications {target_role}",
            k=6,
        )
        resume_context = self.format_context(docs)

        # Run ATS analysis via LLM
        chain = ATS_ANALYSIS_PROMPT | self.llm
        response = await chain.ainvoke({
            "job_description": job_description[:3000],  # Truncate to avoid token limits
            "resume_context": resume_context,
            "target_role": target_role,
        })

        # Parse response
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        result = ATSResponse(
            resume_id=resume_id,
            overall_score=min(100, max(0, float(data.get("overall_score", 0)))),
            keyword_match_score=float(data.get("keyword_match_score", 0)),
            format_score=float(data.get("format_score", 0)),
            content_score=float(data.get("content_score", 0)),
            keywords_found=data.get("keywords_found", []),
            keywords_missing=data.get("keywords_missing", []),
            keyword_details=[
                ATSKeyword(**kw) for kw in data.get("keyword_details", [])
            ],
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", ""),
        )

        self.log_result(
            resume_id,
            score=result.overall_score,
            keywords_found=len(result.keywords_found),
            keywords_missing=len(result.keywords_missing),
        )
        return result
