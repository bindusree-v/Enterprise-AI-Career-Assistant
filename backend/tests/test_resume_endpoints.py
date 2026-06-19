"""
Tests for resume management endpoints.
Uses mocked PDF extraction and embeddings to avoid real API calls.
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import StructuredProfile


class TestUploadResume:
    """Tests for POST /api/upload-resume"""

    @pytest.mark.asyncio
    async def test_upload_valid_pdf(self, client, mock_pdf_content, tmp_path):
        """Valid PDF upload should return 201 with resume_id."""
        with patch("app.routers.resume.save_upload_file") as mock_save:
            mock_save.return_value = ("test-uuid.pdf", str(tmp_path / "test.pdf"), 1024)

            response = await client.post(
                "/api/upload-resume",
                files={"file": ("resume.pdf", mock_pdf_content, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert "resume_id" in data
        assert data["filename"] == "resume.pdf"
        assert data["file_size"] == 1024

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client):
        """Non-PDF uploads should return 415."""
        response = await client.post(
            "/api/upload-resume",
            files={"file": ("resume.docx", b"fake content", "application/docx")},
        )
        assert response.status_code == 415

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client, tmp_path):
        """Empty file should return 400."""
        with patch("app.routers.resume.save_upload_file") as mock_save:
            from fastapi import HTTPException, status
            mock_save.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
            response = await client.post(
                "/api/upload-resume",
                files={"file": ("empty.pdf", b"", "application/pdf")},
            )
        assert response.status_code == 400


class TestExtractText:
    """Tests for POST /api/extract-text"""

    @pytest.mark.asyncio
    async def test_extract_text_not_found(self, client):
        """Non-existent resume_id should return 400."""
        response = await client.post(
            "/api/extract-text",
            json={"resume_id": str(uuid.uuid4())},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_extract_text_success(self, client, test_db_session, sample_resume_text):
        """Valid resume should return extracted text and structured profile."""
        from app.models.database import Resume

        # Create resume record in DB
        resume = Resume(
            id=str(uuid.uuid4()),
            filename="test.pdf",
            original_filename="resume.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        test_db_session.add(resume)
        await test_db_session.commit()

        with patch("app.routers.resume.PDFService") as MockPDFService:
            mock_service = MockPDFService.return_value
            mock_service.extract_text.return_value = sample_resume_text
            mock_service.extract_structured_profile = AsyncMock(
                return_value=StructuredProfile(
                    name="John Doe",
                    email="john@example.com",
                    skills=["Python", "FastAPI"],
                )
            )

            response = await client.post(
                "/api/extract-text",
                json={"resume_id": resume.id},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == resume.id
        assert data["text_length"] > 0
        assert "structured_profile" in data


class TestGenerateEmbeddings:
    """Tests for POST /api/generate-embeddings"""

    @pytest.mark.asyncio
    async def test_generate_embeddings_no_text(self, client, test_db_session):
        """Should return 400 if text hasn't been extracted."""
        from app.models.database import Resume

        resume = Resume(
            id=str(uuid.uuid4()),
            filename="test.pdf",
            original_filename="resume.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        test_db_session.add(resume)
        await test_db_session.commit()

        response = await client.post(
            "/api/generate-embeddings",
            json={"resume_id": resume.id},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, client, test_db_session, sample_resume_text):
        """Successfully embedded resume should return chunk count."""
        from app.models.database import Resume

        resume = Resume(
            id=str(uuid.uuid4()),
            filename="test.pdf",
            original_filename="resume.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            extracted_text=sample_resume_text,
        )
        test_db_session.add(resume)
        await test_db_session.commit()

        with patch("app.routers.resume.get_chroma_store") as mock_store_fn:
            mock_store = MagicMock()
            mock_store.collection_exists.return_value = False
            mock_store.embed_resume = AsyncMock(return_value=("resume_test", 5))
            mock_store.get_collection_name.return_value = "resume_test"
            mock_store_fn.return_value = mock_store

            response = await client.post(
                "/api/generate-embeddings",
                json={"resume_id": resume.id},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["chunks_count"] == 5


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Basic health check should return 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_detailed(self, client):
        """Detailed health check should include service statuses."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "database" in data["services"]
