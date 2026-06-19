"""
Application configuration — supports all 6 LLM providers:
  groq | gemini | mistral | cohere | anthropic | openai
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="CareerGPT")
    app_version: str = Field(default="1.0.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # LLM Provider
    llm_provider: str = Field(default="groq")

    # 1. Groq (FREE) — https://console.groq.com
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    # 2. Google Gemini (FREE) — https://aistudio.google.com/apikey
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")

    # 3. Mistral (FREE) — https://console.mistral.ai
    mistral_api_key: str = Field(default="")
    mistral_model: str = Field(default="mistral-large-latest")

    # 4. Cohere (FREE) — https://dashboard.cohere.com
    cohere_api_key: str = Field(default="")
    cohere_model: str = Field(default="command-r-plus")

    # 5. Anthropic (PAID) — https://console.anthropic.com
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")

    # 6. OpenAI (PAID — last resort) — https://platform.openai.com/api-keys
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # ChromaDB
    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8001)
    chroma_persist_dir: str = Field(default="./data/chroma")

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./data/careergpt.db")

    # File Storage
    upload_dir: str = Field(default="./data/uploads")
    max_file_size_mb: int = Field(default=10)
    allowed_extensions: str = Field(default="pdf")

    # Security
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=30)
    algorithm: str = Field(default="HS256")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in {"development", "staging", "production"}:
            raise ValueError("app_env must be development | staging | production")
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_model(self) -> str:
        return {
            "groq":      self.groq_model,
            "gemini":    self.gemini_model,
            "mistral":   self.mistral_model,
            "cohere":    self.cohere_model,
            "anthropic": self.anthropic_model,
            "openai":    self.openai_model,
        }.get(self.llm_provider, self.groq_model)

    @property
    def active_api_key(self) -> str:
        return {
            "groq":      self.groq_api_key,
            "gemini":    self.gemini_api_key,
            "mistral":   self.mistral_api_key,
            "cohere":    self.cohere_api_key,
            "anthropic": self.anthropic_api_key,
            "openai":    self.openai_api_key,
        }.get(self.llm_provider, "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
