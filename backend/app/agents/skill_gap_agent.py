"""
Agent 2: Skill Gap Analyzer
Compares resume skills against target role requirements,
generates learning roadmaps and certification recommendations.
"""

import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import BaseAgent
from app.models.schemas import SkillGap, SkillGapResponse, SkillResource


SKILL_GAP_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior technical recruiter and career development expert.
Analyze the skill gap between the candidate's current skills and the requirements
for their target role. Provide a detailed, actionable development roadmap.

Return ONLY valid JSON:
{{
  "current_skills": ["skill1", "skill2"],
  "required_skills": ["skill1", "skill3", "skill4"],
  "skill_gaps": [
    {{
      "skill": "Kubernetes",
      "current_level": "none",
      "required_level": "intermediate",
      "priority": "high",
      "learning_resources": [
        {{
          "name": "Kubernetes Official Documentation",
          "url": "https://kubernetes.io/docs/",
          "type": "documentation",
          "duration": "2-3 weeks",
          "cost": "free"
        }},
        {{
          "name": "CKA Certification",
          "url": "https://www.cncf.io/certification/cka/",
          "type": "certification",
          "duration": "3 months",
          "cost": "paid"
        }}
      ]
    }}
  ],
  "strengths": ["List of strong areas that match the role"],
  "roadmap": [
    "Week 1-2: Start with Python fundamentals refresher",
    "Month 1: Complete Docker fundamentals course"
  ],
  "estimated_time_to_ready": "3-6 months",
  "certifications_recommended": ["AWS Solutions Architect", "PMP"]
}}

Priority levels: high (required for role), medium (strongly preferred), low (nice to have)
Levels: none, beginner, intermediate, advanced, expert""",
    ),
    (
        "human",
        """Target Role: {target_role}
Experience Level: {experience_level}
{job_description_section}

Resume/Current Skills Context:
{resume_context}

Identify all skill gaps and create a practical learning roadmap.""",
    ),
])


class SkillGapAgent(BaseAgent):
    """Identifies skill gaps and generates personalized learning roadmaps."""

    def __init__(self):
        super().__init__(agent_name="SkillGapAgent", temperature=0.1)

    async def analyze(
        self,
        resume_id: str,
        target_role: str,
        job_description: Optional[str] = None,
        experience_level: str = "mid",
    ) -> SkillGapResponse:
        """
        Analyze skill gaps for the target role.

        Args:
            resume_id: Resume identifier
            target_role: Desired job role
            job_description: Optional specific job posting
            experience_level: junior|mid|senior|lead

        Returns:
            SkillGapResponse with gaps, roadmap, and recommendations
        """
        self.log_invocation(resume_id, target_role=target_role)

        # Retrieve skills-focused resume content
        docs = await self.retrieve_context(
            resume_id,
            f"skills technologies programming languages frameworks tools certifications",
            k=6,
        )
        resume_context = self.format_context(docs)

        # Optionally include job description context
        jd_section = ""
        if job_description:
            jd_section = f"\nJob Description:\n{job_description[:2000]}"

        chain = SKILL_GAP_PROMPT | self.llm
        response = await chain.ainvoke({
            "target_role": target_role,
            "experience_level": experience_level or "mid",
            "job_description_section": jd_section,
            "resume_context": resume_context,
        })

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        # Build SkillGap objects with nested SkillResource
        skill_gaps = []
        for gap_data in data.get("skill_gaps", []):
            resources = [
                SkillResource(**r) for r in gap_data.get("learning_resources", [])
            ]
            skill_gaps.append(
                SkillGap(
                    skill=gap_data["skill"],
                    current_level=gap_data.get("current_level", "none"),
                    required_level=gap_data.get("required_level", "intermediate"),
                    priority=gap_data.get("priority", "medium"),
                    learning_resources=resources,
                )
            )

        result = SkillGapResponse(
            resume_id=resume_id,
            target_role=target_role,
            current_skills=data.get("current_skills", []),
            required_skills=data.get("required_skills", []),
            skill_gaps=skill_gaps,
            strengths=data.get("strengths", []),
            roadmap=data.get("roadmap", []),
            estimated_time_to_ready=data.get("estimated_time_to_ready", "Unknown"),
            certifications_recommended=data.get("certifications_recommended", []),
        )

        self.log_result(
            resume_id,
            gaps_count=len(result.skill_gaps),
            strengths_count=len(result.strengths),
        )
        return result
