"""
Health check, system status, and LLM provider endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings
from app.models.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Basic health check")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/detailed", summary="Detailed system status")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.active_model,
        "services": {"database": db_status, "api": "ok"},
    }


@router.get("/providers", summary="All supported LLM providers")
async def get_providers():
    """
    Lists all 6 LLM providers with tier, signup URL, and configuration status.
    Switch provider: change LLM_PROVIDER in backend/.env and restart backend.
    """
    s = get_settings()

    def ok(key: str, placeholder: str) -> bool:
        return bool(key) and key != placeholder and not key.startswith("your_")

    return {
        "active_provider": s.llm_provider,
        "active_model": s.active_model,
        "switch_instructions": "Edit LLM_PROVIDER= in backend/.env, then restart the backend",
        "providers": [
            {
                "id": "groq",
                "name": "Groq — Llama 3.3 70B",
                "tier": "FREE",
                "url": "https://console.groq.com",
                "env_key": "GROQ_API_KEY",
                "model": s.groq_model,
                "configured": ok(s.groq_api_key, "your_groq_api_key_here"),
                "active": s.llm_provider == "groq",
            },
            {
                "id": "gemini",
                "name": "Google Gemini 2.0 Flash",
                "tier": "FREE",
                "url": "https://aistudio.google.com/apikey",
                "env_key": "GEMINI_API_KEY",
                "model": s.gemini_model,
                "configured": ok(s.gemini_api_key, "your_gemini_api_key_here"),
                "active": s.llm_provider == "gemini",
            },
            {
                "id": "mistral",
                "name": "Mistral Large",
                "tier": "FREE",
                "url": "https://console.mistral.ai",
                "env_key": "MISTRAL_API_KEY",
                "model": s.mistral_model,
                "configured": ok(s.mistral_api_key, "your_mistral_api_key_here"),
                "active": s.llm_provider == "mistral",
            },
            {
                "id": "cohere",
                "name": "Cohere Command R+",
                "tier": "FREE",
                "url": "https://dashboard.cohere.com",
                "env_key": "COHERE_API_KEY",
                "model": s.cohere_model,
                "configured": ok(s.cohere_api_key, "your_cohere_api_key_here"),
                "active": s.llm_provider == "cohere",
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude 3.5 Sonnet",
                "tier": "PAID",
                "url": "https://console.anthropic.com",
                "env_key": "ANTHROPIC_API_KEY",
                "model": s.anthropic_model,
                "configured": ok(s.anthropic_api_key, "your_anthropic_api_key_here"),
                "active": s.llm_provider == "anthropic",
            },
            {
                "id": "openai",
                "name": "OpenAI GPT-4o  ⚠ last resort",
                "tier": "PAID",
                "url": "https://platform.openai.com/api-keys",
                "env_key": "OPENAI_API_KEY",
                "model": s.openai_model,
                "configured": ok(s.openai_api_key, "your_openai_api_key_here"),
                "active": s.llm_provider == "openai",
            },
        ],
    }
