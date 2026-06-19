"""
PDF text extraction service using PyPDF and pdfplumber.

Profile parsing is done locally with regex — NO OpenAI call here.
OpenAI is only used in the analysis agents (ATS, skill-gap, etc.)
so quota is spent on actual AI analysis, not basic text parsing.
"""

import json
import re
from pathlib import Path
from typing import List, Optional

import pdfplumber
import pypdf

from app.config import get_settings
from app.logging_config import get_logger
from app.models.schemas import StructuredProfile
from app.utils.text_utils import clean_text, extract_email, extract_phone

logger = get_logger(__name__)


# ─── Local regex-based profile parser ────────────────────────────────────────

# Common section header patterns
_SECTION_HEADERS = re.compile(
    r"^(SUMMARY|OBJECTIVE|PROFILE|SKILLS|TECHNICAL SKILLS|EXPERIENCE|WORK EXPERIENCE|"
    r"EMPLOYMENT|EDUCATION|PROJECTS|CERTIFICATIONS|CERTIFICATES|LANGUAGES|"
    r"ACHIEVEMENTS|AWARDS|PUBLICATIONS|VOLUNTEER)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Technology / skill keywords for auto-detection
_TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust",
    "kotlin", "swift", "php", "scala", "r", "matlab", "sql", "nosql",
    "react", "angular", "vue", "next.js", "node.js", "django", "flask", "fastapi",
    "spring", "express", "rails", "laravel", "asp.net",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "git", "ci/cd", "jenkins", "github actions", "linux", "bash",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "html", "css", "rest", "graphql", "microservices", "kafka",
}

_SOFT_KEYWORDS = {
    "leadership", "communication", "teamwork", "problem solving", "critical thinking",
    "project management", "agile", "scrum", "mentoring", "collaboration",
    "time management", "analytical", "creative", "detail-oriented",
}


def _extract_name(text: str) -> Optional[str]:
    """Heuristic: first non-empty line that looks like a name."""
    for line in text.splitlines()[:8]:
        line = line.strip()
        if 3 < len(line) < 60 and not re.search(r"[@|/\\0-9]", line):
            # Likely a name if it's mostly letters and spaces
            if re.match(r"^[A-Za-z\s\.\-\']+$", line):
                return line
    return None


def _extract_location(text: str) -> Optional[str]:
    """Look for city, state / city, country patterns."""
    pattern = re.search(
        r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*(?:[A-Z]{2}|[A-Z][a-z]+))\b", text
    )
    return pattern.group(1) if pattern else None


def _extract_skills(text: str) -> tuple[List[str], List[str], List[str]]:
    """
    Extract all skills, split into technical and soft.
    Returns (all_skills, technical_skills, soft_skills).
    """
    text_lower = text.lower()
    technical = [kw for kw in _TECH_KEYWORDS if kw in text_lower]
    soft = [kw for kw in _SOFT_KEYWORDS if kw in text_lower]

    # Also grab skills from SKILLS section if present
    skills_section = re.search(
        r"(?:SKILLS|TECHNICAL SKILLS)[:\s]*\n(.*?)(?=\n[A-Z]{2,}|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    section_skills: List[str] = []
    if skills_section:
        raw = skills_section.group(1)
        # Split by common delimiters
        items = re.split(r"[,|•·\n\t]+", raw)
        section_skills = [s.strip() for s in items if 2 < len(s.strip()) < 40]

    all_skills = list(dict.fromkeys(technical + [s.title() for s in section_skills[:20]]))
    return all_skills, [t.title() for t in technical], [s.title() for s in soft]


def _extract_experience(text: str) -> List[dict]:
    """Parse work experience blocks heuristically."""
    experience = []
    # Look for date patterns that signal job entries
    job_blocks = re.findall(
        r"([A-Z][^\n]{3,60})\n([^\n]{3,60})\n.*?(\d{4}\s*[-–]\s*(?:\d{4}|Present|Current))",
        text, re.IGNORECASE
    )
    for block in job_blocks[:6]:
        title, company, duration = block
        title = title.strip()
        company = company.strip()
        # Skip if title looks like a section header
        if re.match(r"^(EXPERIENCE|EDUCATION|SKILLS|PROJECTS)", title, re.IGNORECASE):
            continue
        experience.append({
            "title": title[:80],
            "company": company[:80],
            "duration": duration.strip(),
            "years": None,
            "responsibilities": [],
            "technologies": [],
        })
    return experience


def _extract_education(text: str) -> List[dict]:
    """Extract education entries."""
    education = []
    degree_pattern = re.findall(
        r"(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?B\.?A\.?|Ph\.?D\.?|Bachelor|Master|Doctor)"
        r"[^\n]{0,80}\n?([^\n]{5,60})\n?.*?(\d{4})",
        text, re.IGNORECASE
    )
    for match in degree_pattern[:3]:
        degree_prefix, institution, year = match
        education.append({
            "degree": degree_prefix.strip(),
            "institution": institution.strip()[:80],
            "year": int(year),
            "gpa": None,
        })
    return education


def _extract_certifications(text: str) -> List[str]:
    """Find certification mentions."""
    certs = []
    cert_patterns = [
        r"(AWS\s+(?:Certified|Solutions|Developer|DevOps)[^\n,]{0,50})",
        r"(Google\s+(?:Cloud|Professional)[^\n,]{0,50})",
        r"(Microsoft\s+(?:Azure|Certified)[^\n,]{0,50})",
        r"(PMP|PMI[^\n,]{0,30})",
        r"(CKA|CKAD|CKS)",
        r"(Certified\s+\w+[^\n,]{0,50})",
    ]
    for pattern in cert_patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        certs.extend([f.strip() for f in found])
    return list(dict.fromkeys(certs))[:8]


def _estimate_years_experience(text: str) -> Optional[int]:
    """Estimate total years of experience from date ranges."""
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
    if len(years) >= 2:
        year_ints = sorted(set(int(y) for y in years))
        if len(year_ints) >= 2:
            return min(year_ints[-1] - year_ints[0], 30)
    return None


def _extract_summary(text: str) -> Optional[str]:
    """Extract summary/objective section."""
    match = re.search(
        r"(?:SUMMARY|OBJECTIVE|PROFILE)[:\s]*\n(.*?)(?=\n[A-Z]{2,}|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if match:
        summary = match.group(1).strip()
        # Clean it up — take first 3 sentences
        sentences = re.split(r"(?<=[.!?])\s+", summary)
        return " ".join(sentences[:3])[:500]
    return None


class PDFService:
    """Handles PDF text extraction and local structured data parsing."""

    def __init__(self):
        self.settings = get_settings()

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF using a two-strategy approach:
        1. PyPDF  — fast, handles most PDFs
        2. pdfplumber — fallback for complex layouts
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        text = self._extract_with_pypdf(file_path)

        if len(text.strip()) < 100:
            logger.info("PyPDF extraction too short, falling back to pdfplumber", path=file_path)
            text = self._extract_with_pdfplumber(file_path)

        if not text.strip():
            raise ValueError(
                "Could not extract text from PDF. "
                "File may be scanned/image-based or password-protected."
            )

        cleaned = clean_text(text)
        logger.info("Text extracted", file=path.name, chars=len(cleaned))
        return cleaned

    def _extract_with_pypdf(self, file_path: str) -> str:
        text_parts = []
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
        except Exception as e:
            logger.warning("PyPDF extraction failed", error=str(e))
        return "\n".join(text_parts)

    def _extract_with_pdfplumber(self, file_path: str) -> str:
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text_parts.append(
                        page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                    )
        except Exception as e:
            logger.warning("pdfplumber extraction failed", error=str(e))
        return "\n".join(text_parts)

    async def extract_structured_profile(self, raw_text: str) -> StructuredProfile:
        """
        Build a structured profile from raw resume text using LOCAL parsing only.
        Zero OpenAI calls — fast, free, works offline.
        OpenAI is reserved for the actual analysis endpoints.
        """
        try:
            all_skills, technical_skills, soft_skills = _extract_skills(raw_text)

            profile = StructuredProfile(
                name=_extract_name(raw_text),
                email=extract_email(raw_text),
                phone=extract_phone(raw_text),
                location=_extract_location(raw_text),
                summary=_extract_summary(raw_text),
                skills=all_skills,
                technical_skills=technical_skills,
                soft_skills=soft_skills,
                experience=_extract_experience(raw_text),
                education=_extract_education(raw_text),
                certifications=_extract_certifications(raw_text),
                languages=[],
                projects=[],
                years_of_experience=_estimate_years_experience(raw_text),
            )

            logger.info(
                "Profile parsed locally (no API call)",
                name=profile.name,
                skills=len(profile.skills),
                experience=len(profile.experience),
            )
            return profile

        except Exception as e:
            logger.error("Local profile parsing failed, returning minimal profile", error=str(e))
            return StructuredProfile(
                email=extract_email(raw_text),
                phone=extract_phone(raw_text),
            )
