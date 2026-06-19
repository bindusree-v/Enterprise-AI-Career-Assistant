"""
Agent 5: Job Matching Agent
Matches candidate profile against job opportunities,
calculates compatibility scores, and explains recommendation reasoning.
"""

import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import BaseAgent
from app.models.schemas import JobMatch, JobRecommendationResponse


JOB_MATCHING_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a specialized job matching AI with access to the current job market.
Based on the candidate's profile, generate realistic job recommendations that match
their skills, experience, and preferences. Be specific and realistic about companies
and roles that would genuinely consider this candidate.

Return ONLY valid JSON:
{{
  "jobs": [
    {{
      "title": "Senior Python Developer",
      "company": "TechCorp Inc.",
      "location": "San Francisco, CA",
      "match_percentage": 87.5,
      "matching_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
      "missing_skills": ["Kubernetes", "Go"],
      "salary_range": "$130,000 - $160,000",
      "job_type": "full-time",
      "remote": true,
      "why_good_fit": "Your 4 years of Python backend experience and FastAPI projects directly align with their tech stack. The remote-first culture matches your preference.",
      "apply_url": null
    }}
  ],
  "search_strategy": [
    "Focus on companies using Python/FastAPI stack on LinkedIn",
    "Target Series B/C startups that are scaling engineering teams",
    "Use AngelList for remote-first opportunities"
  ]
}}

Generate 5-8 diverse, realistic job recommendations across different company sizes and types.
Match percentage should reflect genuine skill overlap (be honest, not inflated).""",
    ),
    (
        "human",
        """Candidate Profile Context:
{resume_context}

Target Role: {target_role}
Location Preference: {location}
Remote Preference: {remote_preference}
Experience Level: {experience_level}

Generate highly relevant job recommendations with honest match scores.""",
    ),
])


class JobMatchingAgent(BaseAgent):
    """Matches candidate profiles to relevant job opportunities."""

    def __init__(self):
        super().__init__(agent_name="JobMatchingAgent", temperature=0.2)

    async def recommend_jobs(
        self,
        resume_id: str,
        target_role: Optional[str] = None,
        location: Optional[str] = None,
        remote_preference: Optional[str] = None,
        experience_level: Optional[str] = None,
    ) -> JobRecommendationResponse:
        """
        Generate personalized job recommendations.

        Args:
            resume_id: Resume identifier
            target_role: Desired job title
            location: Preferred work location
            remote_preference: remote|hybrid|onsite|any
            experience_level: junior|mid|senior|lead

        Returns:
            JobRecommendationResponse with ranked job matches
        """
        self.log_invocation(
            resume_id, target_role=target_role, location=location
        )

        # Retrieve full profile context for matching
        docs = await self.retrieve_context(
            resume_id,
            f"skills experience education achievements {target_role or 'software engineer'}",
            k=8,
        )
        resume_context = self.format_context(docs)

        chain = JOB_MATCHING_PROMPT | self.llm
        response = await chain.ainvoke({
            "resume_context": resume_context,
            "target_role": target_role or "Relevant to my background",
            "location": location or "Open to any location",
            "remote_preference": remote_preference or "any",
            "experience_level": experience_level or "mid-level",
        })

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        jobs = [JobMatch(**job) for job in data.get("jobs", [])]

        # Sort by match percentage descending
        jobs.sort(key=lambda j: j.match_percentage, reverse=True)

        result = JobRecommendationResponse(
            resume_id=resume_id,
            total_matches=len(jobs),
            jobs=jobs,
            search_strategy=data.get("search_strategy", []),
        )

        self.log_result(
            resume_id,
            total_jobs=result.total_matches,
            top_match=jobs[0].match_percentage if jobs else 0,
        )
        return result
