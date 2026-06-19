"""
Resume management endpoints:
- POST /upload-resume
- POST /extract-text
- POST /generate-embeddings
- POST /analyze-resume
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.database import Resume, get_db
from app.models.schemas import (
    AnalyzeResumeRequest,
    AnalyzeResumeResponse,
    ExtractTextRequest,
    ExtractTextResponse,
    GenerateEmbeddingsRequest,
    GenerateEmbeddingsResponse,
    ResumeUploadResponse,
    StructuredProfile,
)
from app.services.pdf_service import PDFService
from app.services.resume_service import ResumeService
from app.utils.file_utils import save_upload_file, validate_file
from app.utils.text_utils import truncate_text
from app.vectorstore.chroma_store import get_chroma_store
import uuid

router = APIRouter(prefix="/api", tags=["Resume"])
logger = get_logger(__name__)


def get_pdf_service() -> PDFService:
    return PDFService()


@router.post(
    "/upload-resume",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF resume",
    description="Accepts a PDF file, validates it, stores it, and creates a resume record.",
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF resume file"),
    db: AsyncSession = Depends(get_db),
) -> ResumeUploadResponse:
    """
    Upload a resume PDF.

    - Validates file type (PDF only) and size (≤10MB by default)
    - Stores file in data/uploads with a UUID filename
    - Creates a database record for tracking
    - Returns resume_id for use in subsequent API calls
    """
    validate_file(file)

    stored_filename, file_path, file_size = await save_upload_file(file)

    # Create database record
    resume = Resume(
        id=str(uuid.uuid4()),
        filename=stored_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    logger.info(
        "Resume uploaded",
        resume_id=resume.id,
        original=file.filename,
        size=file_size,
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=file.filename,
        file_size=file_size,
    )


@router.post(
    "/extract-text",
    response_model=ExtractTextResponse,
    summary="Extract text from uploaded resume",
    description="Extracts raw text from the PDF and generates a structured JSON profile using AI.",
)
async def extract_text(
    request: ExtractTextRequest,
    db: AsyncSession = Depends(get_db),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> ExtractTextResponse:
    """
    Extract and structure text from a previously uploaded resume.

    - Uses PyPDF with pdfplumber fallback for robust extraction
    - AI parses raw text into structured profile (name, skills, experience, etc.)
    - Stores results in database for subsequent analysis
    """
    service = ResumeService(db, pdf_service, get_chroma_store())
    resume = await service.get_resume_or_404(request.resume_id)

    # Extract raw text
    try:
        raw_text = pdf_service.extract_text(resume.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume file not found on disk for ID: {request.resume_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    # Extract structured profile via LLM
    profile = await pdf_service.extract_structured_profile(raw_text)

    # Persist to database
    await service.save_extracted_text(request.resume_id, raw_text, profile)

    logger.info(
        "Text extracted",
        resume_id=request.resume_id,
        chars=len(raw_text),
    )

    return ExtractTextResponse(
        resume_id=request.resume_id,
        text_length=len(raw_text),
        preview=truncate_text(raw_text, 500),
        structured_profile=profile,
    )


@router.post(
    "/generate-embeddings",
    response_model=GenerateEmbeddingsResponse,
    summary="Generate and store vector embeddings",
    description="Chunks resume text and stores embeddings in ChromaDB for semantic retrieval.",
)
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateEmbeddingsResponse:
    """
    Generate OpenAI embeddings for the resume and store in ChromaDB.

    - Uses RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
    - Creates a dedicated ChromaDB collection per resume
    - Required before any analysis endpoints will work
    """
    vector_store = get_chroma_store()
    service = ResumeService(db, PDFService(), vector_store)
    resume = await service.get_resume_or_404(request.resume_id)

    if not resume.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text not yet extracted. Call /extract-text first.",
        )

    # Skip if already embedded (unless forced)
    if not request.force_regenerate and vector_store.collection_exists(request.resume_id):
        collection_name = vector_store.get_collection_name(request.resume_id)
        return GenerateEmbeddingsResponse(
            resume_id=request.resume_id,
            chunks_count=-1,  # Unknown without querying collection
            collection_name=collection_name,
            message="Embeddings already exist. Use force_regenerate=true to re-embed.",
        )

    # Generate embeddings
    collection_name, chunks_count = await vector_store.embed_resume(
        resume_id=request.resume_id,
        text=resume.extracted_text,
        metadata={
            "filename": resume.original_filename,
            "resume_id": request.resume_id,
        },
    )

    # Save collection reference
    await service.save_embeddings_info(request.resume_id, collection_name)

    return GenerateEmbeddingsResponse(
        resume_id=request.resume_id,
        chunks_count=chunks_count,
        collection_name=collection_name,
        message=f"Successfully embedded {chunks_count} chunks into collection '{collection_name}'",
    )


@router.post(
    "/analyze-resume",
    response_model=AnalyzeResumeResponse,
    summary="Analyze resume quality",
    description="AI-powered general resume quality analysis with scoring and improvement recommendations.",
)
async def analyze_resume(
    request: AnalyzeResumeRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResumeResponse:
    """
    Perform comprehensive resume quality analysis.

    - Scores overall quality (0-100)
    - Identifies strengths and weaknesses
    - Provides formatting and content feedback
    - Recommends sections to add or improve
    """
    service = ResumeService(db, PDFService(), get_chroma_store())

    try:
        result = await service.analyze_resume_quality(
            resume_id=request.resume_id,
            target_role=request.target_role,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result
