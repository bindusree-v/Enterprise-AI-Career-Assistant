"""
Agent 3: Interview Coach
Generates personalized interview questions based on the resume,
target role, and specified difficulty level. Includes sample answers
and evaluation criteria.
"""

import json
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import BaseAgent
from app.models.schemas import (
    DifficultyLevel,
    InterviewQuestion,
    InterviewResponse,
    QuestionType,
)


INTERVIEW_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior technical interviewer and career coach at a top tech company.
Generate personalized interview questions based on the candidate's actual experience
and the target role requirements. Questions should be highly specific to their background.

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "id": 1,
      "question": "You mentioned using React in your XYZ project. How did you handle state management for complex nested components?",
      "type": "technical",
      "difficulty": "medium",
      "topic": "React State Management",
      "hint": "Consider discussing useState, useReducer, Context API, or Redux",
      "sample_answer": "A strong answer would cover...",
      "evaluation_criteria": ["Demonstrates understanding of React state", "Mentions tradeoffs between approaches"]
    }}
  ],
  "preparation_tips": [
    "Review your XYZ project architecture in detail",
    "Practice the STAR method for behavioral questions"
  ],
  "common_pitfalls": [
    "Don't just list technologies — explain how you used them",
    "Quantify your achievements with metrics"
  ]
}}

Question types: technical, behavioral, situational
Difficulty levels: easy, medium, hard""",
    ),
    (
        "human",
        """Target Role: {target_role}
Difficulty Level: {difficulty}
Question Types Requested: {question_types}
Number of Questions: {num_questions}
{job_description_section}

Candidate's Resume Context:
{resume_context}

Generate {num_questions} highly personalized interview questions.""",
    ),
])


class InterviewAgent(BaseAgent):
    """Generates role-specific, personalized interview questions."""

    def __init__(self):
        super().__init__(agent_name="InterviewAgent", temperature=0.4)

    async def generate_questions(
        self,
        resume_id: str,
        target_role: str,
        question_types: List[QuestionType],
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        num_questions: int = 10,
        job_description: Optional[str] = None,
    ) -> InterviewResponse:
        """
        Generate personalized interview questions.

        Args:
            resume_id: Resume identifier for context retrieval
            target_role: Target job role
            question_types: List of desired question types
            difficulty: Overall difficulty level
            num_questions: How many questions to generate
            job_description: Optional job posting for more targeted questions

        Returns:
            InterviewResponse with questions, tips, and pitfalls
        """
        self.log_invocation(
            resume_id,
            target_role=target_role,
            difficulty=difficulty,
            num_questions=num_questions,
        )

        # Retrieve experience and project context
        docs = await self.retrieve_context(
            resume_id,
            f"work experience projects achievements responsibilities {target_role}",
            k=7,
        )
        resume_context = self.format_context(docs)

        jd_section = ""
        if job_description:
            jd_section = f"\nJob Description:\n{job_description[:2000]}"

        types_str = ", ".join([qt.value for qt in question_types])

        chain = INTERVIEW_PROMPT | self.llm
        response = await chain.ainvoke({
            "target_role": target_role,
            "difficulty": difficulty.value,
            "question_types": types_str,
            "num_questions": num_questions,
            "job_description_section": jd_section,
            "resume_context": resume_context,
        })

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())

        questions = [
            InterviewQuestion(**q) for q in data.get("questions", [])
        ]

        result = InterviewResponse(
            resume_id=resume_id,
            target_role=target_role,
            questions=questions,
            preparation_tips=data.get("preparation_tips", []),
            common_pitfalls=data.get("common_pitfalls", []),
        )

        self.log_result(resume_id, questions_count=len(result.questions))
        return result
