"""
Unit tests for utility functions.
"""

import pytest

from app.utils.text_utils import (
    clean_text,
    count_words,
    extract_email,
    extract_phone,
    normalize_skill_name,
    truncate_text,
)


class TestCleanText:
    def test_removes_extra_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_normalizes_newlines(self):
        result = clean_text("line1\n\n\n\nline2")
        assert result == "line1\n\nline2"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_removes_control_characters(self):
        assert clean_text("hello\x00world") == "helloworld"

    def test_fixes_ligatures(self):
        assert "\ufb01" not in clean_text("pro\ufb01le")


class TestExtractEmail:
    def test_simple_email(self):
        assert extract_email("Contact me at john@example.com for details") == "john@example.com"

    def test_no_email(self):
        assert extract_email("No email here") is None

    def test_email_with_plus(self):
        assert extract_email("john+work@company.org") == "john+work@company.org"


class TestExtractPhone:
    def test_us_phone(self):
        phone = extract_phone("Call me at (555) 123-4567")
        assert phone is not None
        assert "555" in phone

    def test_no_phone(self):
        assert extract_phone("No phone number") is None


class TestTruncateText:
    def test_short_text_unchanged(self):
        text = "Short text"
        assert truncate_text(text, 100) == text

    def test_long_text_truncated(self):
        text = "word " * 200
        result = truncate_text(text, 50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_truncates_at_word_boundary(self):
        text = "Hello World This Is A Test"
        result = truncate_text(text, 12)
        assert not result.startswith("...")


class TestCountWords:
    def test_simple_count(self):
        assert count_words("one two three") == 3

    def test_empty_string(self):
        assert count_words("") == 0

    def test_single_word(self):
        assert count_words("hello") == 1


class TestNormalizeSkillName:
    def test_js_alias(self):
        assert normalize_skill_name("JS") == "javascript"

    def test_k8s_alias(self):
        assert normalize_skill_name("k8s") == "kubernetes"

    def test_no_alias(self):
        assert normalize_skill_name("Python") == "python"

    def test_strips_whitespace(self):
        assert normalize_skill_name("  python  ") == "python"
