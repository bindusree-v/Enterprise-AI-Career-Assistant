"""
CareerGPT — Enterprise AI Career Assistant
FastAPI Application Entry Point

Startup sequence:
1. Configure structured logging
2. Initialize database tables
3. Register routers with rate limiting
4. Configure CORS, middleware, and error handlers
5. Expose OpenAPI documentation
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.models.database import init_db
from app.routers import analysis, chat, health, resume

# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown tasks."""
    configure_logging()
    logger = get_logger("startup")

    settings = get_settings()
    logger.info(
        "Starting CareerGPT",
        version=settings.app_version,
        env=settings.app_env,
        host=settings.host,
        port=settings.port,
    )

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Ensure storage directories exist
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    logger.info("Storage directories ready")

    yield  # Application runs here

    logger.info("CareerGPT shutting down")


# ─── Application Factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CareerGPT — AI Career Assistant",
        description="""
## 🚀 CareerGPT Enterprise API

AI-powered career assistant platform featuring:

- **Resume Processing** — PDF upload, text extraction, structured parsing
- **ATS Analysis** — Score resumes against job descriptions
- **Skill Gap Analysis** — Identify gaps with learning roadmaps
- **Interview Prep** — Personalized question generation
- **Career Guidance** — Strategic career path recommendations
- **Job Matching** — AI-curated job recommendations
- **RAG Chatbot** — Context-aware career conversation

### Typical Workflow
1. `POST /api/upload-resume` — Upload PDF
2. `POST /api/extract-text` — Extract & structure resume data
3. `POST /api/generate-embeddings` — Create vector embeddings
4. Use any analysis endpoint with the `resume_id`
        """,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ─── Rate Limiting ─────────────────────────────────────────────────────────
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ─── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Global Exception Handlers ─────────────────────────────────────────────
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger = get_logger("exception_handler")
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "Contact support",
            },
        )

    # ─── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(resume.router)
    app.include_router(analysis.router)
    app.include_router(chat.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
