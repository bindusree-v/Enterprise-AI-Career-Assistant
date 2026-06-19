"""
File handling utilities: validation, storage, and cleanup.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def ensure_upload_dir() -> Path:
    """Ensure the upload directory exists and return its Path."""
    settings = get_settings()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file type and extension.
    Raises HTTPException on invalid file.
    """
    settings = get_settings()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    extension = Path(file.filename).suffix.lower().lstrip(".")
    if extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{extension}' not allowed. Supported: {settings.allowed_extensions_list}",
        )

    # Validate MIME type for PDF
    if file.content_type and "pdf" not in file.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid content type: {file.content_type}. Expected PDF.",
        )


async def save_upload_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    Asynchronously save uploaded file to disk.

    Returns:
        Tuple of (stored_filename, file_path, file_size_bytes)
    """
    settings = get_settings()
    upload_dir = ensure_upload_dir()

    # Generate unique filename to prevent collisions
    ext = Path(file.filename).suffix.lower()
    stored_filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_dir / stored_filename

    # Read and validate file size
    content = await file.read()
    file_size = len(content)

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size / 1024 / 1024:.1f}MB exceeds limit of {settings.max_file_size_mb}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Write to disk
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(
        "File saved",
        filename=stored_filename,
        original=file.filename,
        size_bytes=file_size,
        path=str(file_path),
    )

    return stored_filename, str(file_path), file_size


async def delete_file(file_path: str) -> bool:
    """Safely delete a file, returning True if successful."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info("File deleted", path=file_path)
            return True
        return False
    except OSError as e:
        logger.error("Failed to delete file", path=file_path, error=str(e))
        return False


def get_file_path(filename: str) -> Path:
    """Resolve stored filename to full path."""
    settings = get_settings()
    return Path(settings.upload_dir) / filename
