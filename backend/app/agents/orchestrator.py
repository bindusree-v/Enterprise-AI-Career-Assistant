"""
LangGraph Agent Orchestrator
Manages multi-agent workflows using a state machine approach.
Coordinates agents for complex, multi-step career analysis pipelines.
"""

from typing import Annotated, Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.ats_agent import ATSAgent
from app.agents.career_advisor_agent import CareerAdvisorAgent
from app.agents.interview_agent import InterviewAgent
from app.agents.job_matching_agent import JobMatchingAgent
from app.agents.skill_gap_agent import SkillGapAgent
from app.logging_config import get_logger
from app.models.schemas import DifficultyLevel, QuestionType

logger = get_logger(__name__)


# ─── State Definition ─────────────────────────────────────────────────────────

class CareerAnalysisState(TypedDict):
    """Shared state flowing through the LangGraph workflow."""
    resume_id: str
    target_role: Optional[str]
    job_description: Optional[str]
    experience_level: Optional[str]

    # Agent outputs (populated as workflow progresses)
    ats_result: Optional[Dict[str, Any]]
    skill_gap_result: Optional[Dict[str, Any]]
    interview_result: Optional[Dict[str, Any]]
    career_result: Optional[Dict[str, Any]]
    job_result: Optional[Dict[str, Any]]

    # Control flow
    errors: list
    completed_agents: list


# ─── Agent Node Functions ─────────────────────────────────────────────────────

async def run_ats_node(state: CareerAnalysisState) -> CareerAnalysisState:
    """LangGraph node: Run ATS analysis."""
    if not state.get("job_description"):
        logger.info("Skipping ATS node — no job description provided")
        return state

    try:
        agent = ATSAgent()
        result = await agent.analyze(
            resume_id=state["resume_id"],
            job_description=state["job_description"],
            target_role=state.get("target_role", "target role"),
        )
        state["ats_result"] = result.model_dump()
        state["completed_agents"] = state.get("completed_agents", []) + ["ats"]
    except Exception as e:
        logger.error("ATS agent failed", error=str(e))
        state["errors"] = state.get("errors", []) + [f"ATS: {str(e)}"]

    return state


async def run_skill_gap_node(state: CareerAnalysisState) -> CareerAnalysisState:
    """LangGraph node: Run skill gap analysis."""
    if not state.get("target_role"):
        logger.info("Skipping skill gap node — no target role provided")
        return state

    try:
        agent = SkillGapAgent()
        result = await agent.analyze(
            resume_id=state["resume_id"],
            target_role=state["target_role"],
            job_description=state.get("job_description"),
            experience_level=state.get("experience_level", "mid"),
        )
        state["skill_gap_result"] = result.model_dump()
        state["completed_agents"] = state.get("completed_agents", []) + ["skill_gap"]
    except Exception as e:
        logger.error("Skill gap agent failed", error=str(e))
        state["errors"] = state.get("errors", []) + [f"SkillGap: {str(e)}"]

    return state


async def run_career_advisor_node(state: CareerAnalysisState) -> CareerAnalysisState:
    """LangGraph node: Run career advisor."""
    try:
        agent = CareerAdvisorAgent()
        result = await agent.advise(
            resume_id=state["resume_id"],
            current_role=state.get("target_role"),
        )
        state["career_result"] = result.model_dump()
        state["completed_agents"] = state.get("completed_agents", []) + ["career"]
    except Exception as e:
        logger.error("Career advisor agent failed", error=str(e))
        state["errors"] = state.get("errors", []) + [f"Career: {str(e)}"]

    return state


async def run_job_matching_node(state: CareerAnalysisState) -> CareerAnalysisState:
    """LangGraph node: Run job matching."""
    try:
        agent = JobMatchingAgent()
        result = await agent.recommend_jobs(
            resume_id=state["resume_id"],
            target_role=state.get("target_role"),
            experience_level=state.get("experience_level"),
        )
        state["job_result"] = result.model_dump()
        state["completed_agents"] = state.get("completed_agents", []) + ["jobs"]
    except Exception as e:
        logger.error("Job matching agent failed", error=str(e))
        state["errors"] = state.get("errors", []) + [f"JobMatch: {str(e)}"]

    return state


async def run_interview_node(state: CareerAnalysisState) -> CareerAnalysisState:
    """LangGraph node: Generate interview questions."""
    if not state.get("target_role"):
        return state

    try:
        agent = InterviewAgent()
        result = await agent.generate_questions(
            resume_id=state["resume_id"],
            target_role=state["target_role"],
            question_types=[QuestionType.TECHNICAL, QuestionType.BEHAVIORAL],
            difficulty=DifficultyLevel.MEDIUM,
            num_questions=5,  # Smaller set in full pipeline
            job_description=state.get("job_description"),
        )
        state["interview_result"] = result.model_dump()
        state["completed_agents"] = state.get("completed_agents", []) + ["interview"]
    except Exception as e:
        logger.error("Interview agent failed", error=str(e))
        state["errors"] = state.get("errors", []) + [f"Interview: {str(e)}"]

    return state


# ─── Graph Construction ───────────────────────────────────────────────────────

def build_career_analysis_graph() -> StateGraph:
    """
    Build the LangGraph workflow for full career analysis.

    Workflow topology:
    START → ATS → Skill Gap → Career Advisor → Job Matching → Interview → END

    Agents run sequentially so later agents can reference earlier results.
    For production scale, ATS/SkillGap/CareerAdvisor could run in parallel.
    """
    workflow = StateGraph(CareerAnalysisState)

    # Add agent nodes
    workflow.add_node("ats_analysis", run_ats_node)
    workflow.add_node("skill_gap_analysis", run_skill_gap_node)
    workflow.add_node("career_advisor", run_career_advisor_node)
    workflow.add_node("job_matching", run_job_matching_node)
    workflow.add_node("interview_prep", run_interview_node)

    # Define edges (sequential flow)
    workflow.set_entry_point("ats_analysis")
    workflow.add_edge("ats_analysis", "skill_gap_analysis")
    workflow.add_edge("skill_gap_analysis", "career_advisor")
    workflow.add_edge("career_advisor", "job_matching")
    workflow.add_edge("job_matching", "interview_prep")
    workflow.add_edge("interview_prep", END)

    return workflow.compile()


# ─── Orchestrator Class ───────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    High-level interface for running multi-agent career analysis pipelines.
    Wraps the LangGraph workflow.
    """

    def __init__(self):
        self.graph = build_career_analysis_graph()

    async def run_full_analysis(
        self,
        resume_id: str,
        target_role: Optional[str] = None,
        job_description: Optional[str] = None,
        experience_level: Optional[str] = None,
    ) -> CareerAnalysisState:
        """
        Run the complete multi-agent career analysis pipeline.

        Returns the final state with all agent results populated.
        """
        initial_state: CareerAnalysisState = {
            "resume_id": resume_id,
            "target_role": target_role,
            "job_description": job_description,
            "experience_level": experience_level,
            "ats_result": None,
            "skill_gap_result": None,
            "interview_result": None,
            "career_result": None,
            "job_result": None,
            "errors": [],
            "completed_agents": [],
        }

        logger.info(
            "Starting full career analysis pipeline",
            resume_id=resume_id,
            target_role=target_role,
        )

        final_state = await self.graph.ainvoke(initial_state)

        logger.info(
            "Career analysis pipeline completed",
            resume_id=resume_id,
            completed=final_state.get("completed_agents", []),
            errors=final_state.get("errors", []),
        )

        return final_state


# Singleton
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Dependency injection: return singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
