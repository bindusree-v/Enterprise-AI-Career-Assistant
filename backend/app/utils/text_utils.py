"""
Text cleaning and normalization utilities for resume processing.
"""

import re
import unicodedata
from typing import List


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted PDF text.

    Steps:
    1. Normalize unicode characters
    2. Remove null bytes and control characters
    3. Fix common PDF extraction artifacts
    4. Normalize whitespace
    """
    if not text:
        return ""

    # Normalize unicode (convert special chars to ASCII equivalents where possible)
    text = unicodedata.normalize("NFKD", text)

    # Remove null bytes and other control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Fix common PDF ligatures
    ligature_map = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb00": "ff",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
    }
    for lig, replacement in ligature_map.items():
        text = text.replace(lig, replacement)

    # Normalize multiple spaces to single space (but preserve newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize multiple newlines to at most two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Strip leading/trailing whitespace
    return text.strip()


def extract_email(text: str) -> str | None:
    """Extract first email address from text."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract first phone number from text."""
    patterns = [
        r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return None


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    pattern = r"https?://[^\s\)<>\"']+"
    return re.findall(pattern, text)


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to max_chars, ending at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def normalize_skill_name(skill: str) -> str:
    """Normalize skill names for comparison (lowercase, strip, common aliases)."""
    skill = skill.lower().strip()

    # Common aliases
    aliases = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "k8s": "kubernetes",
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "dl": "deep learning",
        "nlp": "natural language processing",
        "cv": "computer vision",
    }
    return aliases.get(skill, skill)
