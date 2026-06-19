"""
Agent 4: Career Advisor
Provides personalized career path recommendations, growth opportunities,
and industry trend analysis based on the candidate's profile.
"""

import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import BaseAgent
from app.models.schemas import CareerPath, CareerSuggestionsResponse


CAREER_ADVISOR_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a seasoned executive career coach who has helped thousands of professionals
advance their careers. You have deep knowledge of industry trends, compensation benchmarks,
and career progression paths across technology, business, and other sectors.

Analyze the candidate's profile and provide strategic career guidance tailored to their
background, skills, and stated goals.

Return ONLY valid JSON:
{{
  "current_level": "Mid-level Software Engineer",
  "career_paths": [
    {{
      "title": "Senior Software Engineer → Staff Engineer",
      "description": "Technical leadership path focusing on system design and mentoring",
      "required_skills": ["System Design", "Distributed Systems", "Mentoring"],
      "average_salary": "$150,000 - $200,000",
      "growth_potential": "high",
      "time_to_achieve": "2-3 years",
      "steps": [
        "Lead a cross-functional project in current role",
        "Contribute to architectural decisions",
        "Mentor 2-3 junior engineers"
      ]
    }}
  ],
  "industry_trends": [
    "AI/ML integration is becoming standard in most engineering roles",
    "Remote-first companies offer 20-30% salary premium in competitive markets"
  ],
  "growth_opportunities": [
    "Your Python + ML background positions you well for the AI boom",
    "Consider contributing to open source projects for visibility"
  ],
  "action_plan": [
    "This month: Schedule a career conversation with your manager",
    "Q1: Complete AWS certification",
    "Q2: Present a technical deep-dive to your team"
  ],
  "networking_tips": [
    "Join local Python meetup groups",
    "Contribute to open source ML libraries on GitHub"
  ]
}}""",
    ),
    (
        "human",
        """Candidate Profile Context:
{resume_context}

Current Role: {current_role}
Career Goals: {career_goals}
Industry Preference: {industry_preference}
Location Preference: {location_preference}

Provide strategic, personalized career advice.""",
    ),
])


class CareerAdvisorAgent(BaseAgent):
    """Provides strategic career path recommendations and growth strategies."""

    def __init__(self):
        super().__init__(agent_name="CareerAdvisorAgent", temperature=0.3)

    async def advise(
        self,
        resume_id: str,
        current_role: Optional[str] = None,
        career_goals: Optional[str] = None,
        industry_preference: Optional[str] = None,
        location_preference: Optional[str] = None,
    ) -> CareerSuggestionsResponse:
        """
        Generate personalized career path recommendations.

        Args:
            resume_id: Resume identifier
            current_role: User's current job title
            career_goals: User's stated career aspirations
            industry_preference: Preferred industry/sector
            location_preference: Preferred location

        Returns:
            CareerSuggestionsResponse with paths, trends, and action plan
        """
        self.log_invocation(resume_id, current_role=current_role)

        # Retrieve broad resume context (experience, education, achievements)
        docs = await self.retrieve_context(
            resume_id,
            "career experience skills achievements education professional background",
            k=7,
        )
        resume_context = self.format_context(docs)

        chain = CAREER_ADVISOR_PROMPT | self.llm
        response = await chain.ainvoke({
            "resume_context": resume_context,
            "current_role": current_role or "Not specified",
            "career_goals": career_goals or "Not specified — provide general recommendations",
            "industry_preference": industry_preference or "Open to any industry",
            "location_preference": location_preference or "Flexible",
        })

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        career_paths = [CareerPath(**p) for p in data.get("career_paths", [])]

        result = CareerSuggestionsResponse(
            resume_id=resume_id,
            current_level=data.get("current_level", "Professional"),
            career_paths=career_paths,
            industry_trends=data.get("industry_trends", []),
            growth_opportunities=data.get("growth_opportunities", []),
            action_plan=data.get("action_plan", []),
            networking_tips=data.get("networking_tips", []),
        )

        self.log_result(resume_id, paths_count=len(result.career_paths))
        return result
