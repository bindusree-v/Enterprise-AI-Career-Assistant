"""
Chat endpoint — multi-turn conversational AI over resume context.
POST /chat
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.logging_config import get_logger
from app.models.database import ChatMessage as DBMessage
from app.models.database import ChatSession, get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.rag.pipeline import get_rag_pipeline
from app.services.resume_service import ResumeService
from app.services.pdf_service import PDFService
from app.vectorstore.chroma_store import get_chroma_store

router = APIRouter(prefix="/api", tags=["Chat"])
logger = get_logger(__name__)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with CareerGPT",
    description="Multi-turn conversational AI assistant using resume as context.",
)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Conversational AI endpoint with RAG over the uploaded resume.

    - Retrieves relevant resume chunks via semantic search
    - Maintains conversation history within the session
    - Provides career-specific responses with source attribution
    - Returns suggested follow-up actions

    Flow:
    1. Validate resume exists and has embeddings
    2. Create or resume a chat session
    3. Retrieve relevant context from ChromaDB
    4. Generate response with conversation history
    5. Persist message pair to database
    """
    service = ResumeService(db, PDFService(), get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)

    if not resume.chroma_collection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume embeddings not found. Call /generate-embeddings first.",
        )

    # Create or retrieve session
    session_id = request.session_id
    if session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            session_id = None  # Invalid session, create new

    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            resume_id=request.resume_id,
            title=request.message[:50],  # Use first message as title
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Build conversation history for the pipeline
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]

    # Run RAG pipeline
    rag = get_rag_pipeline()
    rag_result = await rag.generate(
        resume_id=request.resume_id,
        question=request.message,
        conversation_history=history,
        k=5,
    )

    # Persist user message
    user_msg = DBMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    # Persist assistant response
    assistant_msg = DBMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=rag_result["answer"],
        metadata={"sources": rag_result["sources"]},
    )
    db.add(assistant_msg)
    await db.commit()

    # Generate suggested follow-up actions based on response content
    suggested_actions = _generate_suggestions(request.message, rag_result["answer"])

    logger.info(
        "Chat response generated",
        session_id=session_id,
        resume_id=request.resume_id,
        sources=len(rag_result["sources"]),
    )

    return ChatResponse(
        session_id=session_id,
        message=rag_result["answer"],
        sources=rag_result["sources"],
        suggested_actions=suggested_actions,
    )


def _generate_suggestions(question: str, answer: str) -> list[str]:
    """Generate contextual follow-up action suggestions."""
    suggestions = []
    q_lower = question.lower()
    a_lower = answer.lower()

    if "skill" in q_lower or "learn" in q_lower:
        suggestions.append("Run a full skill gap analysis")
    if "interview" in q_lower or "question" in q_lower:
        suggestions.append("Generate interview questions for your target role")
    if "job" in q_lower or "apply" in q_lower or "position" in q_lower:
        suggestions.append("Get personalized job recommendations")
    if "resume" in q_lower or "improve" in q_lower:
        suggestions.append("Get ATS score against a job description")
    if "career" in q_lower or "path" in q_lower or "grow" in q_lower:
        suggestions.append("View career path suggestions")

    # Default suggestions if none matched
    if not suggestions:
        suggestions = [
            "Ask about improving your resume",
            "Get interview questions for your target role",
        ]

    return suggestions[:3]  # Max 3 suggestions
