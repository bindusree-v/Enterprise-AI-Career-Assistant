"""
LLM Factory — returns the correct LangChain chat model based on LLM_PROVIDER in .env.

Priority order (recommended → last resort):
  1. groq       FREE  → https://console.groq.com
  2. gemini     FREE  → https://aistudio.google.com/apikey
  3. mistral    FREE  → https://console.mistral.ai
  4. cohere     FREE  → https://dashboard.cohere.com
  5. anthropic  PAID  → https://console.anthropic.com
  6. openai     PAID  → https://platform.openai.com/api-keys

To switch: change LLM_PROVIDER= in backend/.env and restart the backend.
"""

from typing import Any

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def get_llm(temperature: float = 0.1) -> Any:
    """Return the configured LangChain chat model. Imports are lazy."""
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()

    logger.info("Loading LLM", provider=provider, model=settings.active_model)

    # ── 1. GROQ — FREE ────────────────────────────────────────────────────────
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=settings.groq_model,
            temperature=temperature,
            api_key=settings.groq_api_key,
            max_retries=2,
        )

    # ── 2. GOOGLE GEMINI — FREE ───────────────────────────────────────────────
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=temperature,
            google_api_key=settings.gemini_api_key,
            max_retries=2,
        )

    # ── 3. MISTRAL — FREE ─────────────────────────────────────────────────────
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=settings.mistral_model,
            temperature=temperature,
            api_key=settings.mistral_api_key,
            max_retries=2,
        )

    # ── 4. COHERE — FREE ──────────────────────────────────────────────────────
    elif provider == "cohere":
        from langchain_cohere import ChatCohere
        return ChatCohere(
            model=settings.cohere_model,
            temperature=temperature,
            cohere_api_key=settings.cohere_api_key,
        )

    # ── 5. ANTHROPIC CLAUDE — PAID ────────────────────────────────────────────
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=temperature,
            api_key=settings.anthropic_api_key,
            max_retries=2,
        )

    # ── 6. OPENAI — PAID (last resort) ────────────────────────────────────────
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            max_retries=2,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER='{provider}'. "
            f"Valid options: groq | gemini | mistral | cohere | anthropic | openai"
        )
