#!/usr/bin/env python3
"""
Unit tests for scripts/validate.py

Tests cover:
- validate_url function
- validate_tool function

Usage:
    pytest tests/test_validate.py -v
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate import validate_url, validate_tool


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_tool():
    """Create a valid tool for testing."""
    return {
        "id": "test-tool",
        "name": "Test Tool",
        "tagline": "A test tool for testing purposes",
        "description": "This is a comprehensive description of the test tool",
        "categories": ["ai", "dev"],
        "links": {
            "official": "https://example.com/test",
            "github": "https://github.com/user/test-tool"
        },
        "source": "producthunt",
        "first_seen_at": "2025-01-01",
        "published": False,
        "score": 75.5,
        "topics": ["ai", "automation"]
    }


@pytest.fixture
def minimal_tool():
    """Create a minimal valid tool with only required fields."""
    return {
        "id": "minimal-tool",
        "name": "Minimal Tool",
        "tagline": "Minimal test tool",
        "categories": ["other"],
        "links": {
            "official": "https://minimal.com"
        },
        "source": "github",
        "first_seen_at": "2025-01-01"
    }


# ============================================================================
# validate_url Tests
# ============================================================================

class TestValidateUrl:
    """Test URL validation logic."""

    def test_valid_https_url(self):
        """Should accept valid HTTPS URL."""
        assert validate_url("https://example.com") is True

    def test_valid_http_url(self):
        """Should accept valid HTTP URL."""
        assert validate_url("http://example.com") is True

    def test_url_with_path(self):
        """Should accept URL with path."""
        assert validate_url("https://example.com/path/to/page") is True

    def test_url_with_query_params(self):
        """Should accept URL with query parameters."""
        assert validate_url("https://example.com?param=value&other=data") is True

    def test_url_with_fragment(self):
        """Should accept URL with fragment."""
        assert validate_url("https://example.com/page#section") is True

    def test_url_with_port(self):
        """Should accept URL with port number."""
        assert validate_url("https://example.com:8080/api") is True

    def test_subdomain_url(self):
        """Should accept URL with subdomain."""
        assert validate_url("https://api.example.com/v1") is True

    def test_empty_string(self):
        """Should reject empty string."""
        assert validate_url("") is False

    def test_none_input(self):
        """Should reject None input."""
        assert validate_url(None) is False

    def test_missing_scheme(self):
        """Should reject URL without http(s) scheme."""
        assert validate_url("example.com") is False

    def test_ftp_scheme(self):
        """Should reject non-HTTP schemes."""
        assert validate_url("ftp://example.com") is False

    def test_malformed_url(self):
        """Should reject malformed URLs."""
        assert validate_url("https://") is False
        assert validate_url("http://") is False

    def test_invalid_characters(self):
        """Should reject URLs with truly invalid characters."""
        # Note: urlparse is permissive, so we test truly malformed URLs
        assert validate_url("https://") is False  # No domain
        assert validate_url("ht!tp://example.com") is False  # Invalid scheme

    def test_localhost(self):
        """Should accept localhost URLs."""
        assert validate_url("http://localhost:3000") is True

    def test_ip_address(self):
        """Should accept IP address URLs."""
        assert validate_url("http://192.168.1.1") is True


# ============================================================================
# validate_tool Tests
# ============================================================================

class TestValidateTool:
    """Test tool validation logic."""

    def test_valid_tool(self, valid_tool):
        """Should return no errors for valid tool."""
        errors = validate_tool(valid_tool)
        assert errors == []

    def test_minimal_valid_tool(self, minimal_tool):
        """Should accept minimal tool with only required fields."""
        errors = validate_tool(minimal_tool)
        assert errors == []

    # ========================================================================
    # Required Fields Tests
    # ========================================================================

    def test_missing_id(self, valid_tool):
        """Should error when id is missing."""
        del valid_tool["id"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: id" in e for e in errors)

    def test_missing_name(self, valid_tool):
        """Should error when name is missing."""
        del valid_tool["name"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: name" in e for e in errors)

    def test_missing_tagline(self, valid_tool):
        """Should error when tagline is missing."""
        del valid_tool["tagline"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: tagline" in e for e in errors)

    def test_missing_categories(self, valid_tool):
        """Should error when categories is missing."""
        del valid_tool["categories"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: categories" in e for e in errors)

    def test_missing_links(self, valid_tool):
        """Should error when links is missing."""
        del valid_tool["links"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: links" in e for e in errors)

    def test_missing_first_seen_at(self, valid_tool):
        """Should error when first_seen_at is missing."""
        del valid_tool["first_seen_at"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: first_seen_at" in e for e in errors)

    def test_missing_source(self, valid_tool):
        """Should error when source is missing."""
        del valid_tool["source"]
        errors = validate_tool(valid_tool)

        assert len(errors) > 0
        assert any("Missing required field: source" in e for e in errors)

    # ========================================================================
    # ID Format Tests
    # ========================================================================

    def test_valid_id_format(self, valid_tool):
        """Should accept valid ID format."""
        valid_tool["id"] = "valid-tool-123"
        errors = validate_tool(valid_tool)

        assert not any("Invalid ID format" in e for e in errors)

    def test_invalid_id_uppercase(self, valid_tool):
        """Should reject ID with uppercase letters."""
        valid_tool["id"] = "Invalid-Tool"
        errors = validate_tool(valid_tool)

        assert any("Invalid ID format" in e for e in errors)

    def test_invalid_id_special_chars(self, valid_tool):
        """Should reject ID with special characters."""
        valid_tool["id"] = "tool_with_underscore"
        errors = validate_tool(valid_tool)

        assert any("Invalid ID format" in e for e in errors)

    def test_invalid_id_spaces(self, valid_tool):
        """Should reject ID with spaces."""
        valid_tool["id"] = "tool with spaces"
        errors = validate_tool(valid_tool)

        assert any("Invalid ID format" in e for e in errors)

    # ========================================================================
    # Categories Tests
    # ========================================================================

    def test_empty_categories_array(self, valid_tool):
        """Should error when categories is empty array."""
        valid_tool["categories"] = []
        errors = validate_tool(valid_tool)

        assert any("Categories must be non-empty array" in e for e in errors)

    def test_categories_not_array(self, valid_tool):
        """Should error when categories is not an array."""
        valid_tool["categories"] = "ai"
        errors = validate_tool(valid_tool)

        assert any("Categories must be non-empty array" in e for e in errors)

    def test_invalid_category(self, valid_tool):
        """Should error for invalid category name."""
        valid_tool["categories"] = ["ai", "invalid-category"]
        errors = validate_tool(valid_tool)

        assert any("Invalid category: invalid-category" in e for e in errors)

    def test_all_valid_categories(self, valid_tool):
        """Should accept all valid categories."""
        valid_categories = ["meeting", "docs", "pm", "automation", "ai", "dev", "ph", "other"]

        for category in valid_categories:
            valid_tool["categories"] = [category]
            errors = validate_tool(valid_tool)
            assert not any("Invalid category" in e for e in errors), f"Failed for {category}"

    # ========================================================================
    # Source Tests
    # ========================================================================

    def test_valid_sources(self, valid_tool):
        """Should accept all valid source values."""
        valid_sources = ["producthunt", "hn", "github", "manual", "rss"]

        for source in valid_sources:
            valid_tool["source"] = source
            errors = validate_tool(valid_tool)
            assert not any("Invalid source" in e for e in errors), f"Failed for {source}"

    def test_invalid_source(self, valid_tool):
        """Should error for invalid source."""
        valid_tool["source"] = "invalid-source"
        errors = validate_tool(valid_tool)

        assert any("Invalid source: invalid-source" in e for e in errors)

    # ========================================================================
    # Links Tests
    # ========================================================================

    def test_links_not_object(self, valid_tool):
        """Should error when links is not an object."""
        valid_tool["links"] = "https://example.com"
        errors = validate_tool(valid_tool)

        assert any("Links must be an object" in e for e in errors)

    def test_missing_official_link(self, valid_tool):
        """Should error when official link is missing."""
        valid_tool["links"] = {"github": "https://github.com/user/repo"}
        errors = validate_tool(valid_tool)

        assert any("Missing official link" in e for e in errors)

    def test_invalid_official_url(self, valid_tool):
        """Should error for invalid official URL."""
        valid_tool["links"]["official"] = "not-a-url"
        errors = validate_tool(valid_tool)

        assert any("Invalid official URL" in e for e in errors)

    def test_optional_urls_not_validated_by_default(self, valid_tool):
        """Should not error for invalid optional URLs in non-strict mode."""
        valid_tool["links"]["github"] = "invalid-url"
        errors = validate_tool(valid_tool, strict=False)

        # Should not have error in non-strict mode
        assert not any("Invalid github URL" in e for e in errors)

    def test_optional_urls_validated_in_strict(self, valid_tool):
        """Should error for invalid optional URLs in strict mode."""
        valid_tool["links"]["producthunt"] = "not-a-url"
        errors = validate_tool(valid_tool, strict=True)

        assert any("Invalid producthunt URL" in e for e in errors)

    # ========================================================================
    # Date Format Tests
    # ========================================================================

    def test_valid_date_format(self, valid_tool):
        """Should accept valid ISO date format."""
        valid_tool["first_seen_at"] = "2025-01-15"
        errors = validate_tool(valid_tool)

        assert not any("Invalid date format" in e for e in errors)

    def test_invalid_date_format(self, valid_tool):
        """Should error for invalid date format."""
        valid_tool["first_seen_at"] = "01/15/2025"
        errors = validate_tool(valid_tool)

        assert any("Invalid date format" in e for e in errors)

    def test_invalid_date_value(self, valid_tool):
        """Should error for invalid date value."""
        valid_tool["first_seen_at"] = "2025-13-45"
        errors = validate_tool(valid_tool)

        assert any("Invalid date format" in e for e in errors)

    # ========================================================================
    # Score Tests
    # ========================================================================

    def test_valid_score_range(self, valid_tool):
        """Should accept score in valid range 0-100."""
        for score in [0, 50, 100, 75.5]:
            valid_tool["score"] = score
            errors = validate_tool(valid_tool)
            assert not any("Score must be 0-100" in e for e in errors), f"Failed for {score}"

    def test_negative_score(self, valid_tool):
        """Should error for negative score."""
        valid_tool["score"] = -10
        errors = validate_tool(valid_tool)

        assert any("Score must be 0-100" in e for e in errors)

    def test_score_over_100(self, valid_tool):
        """Should error for score over 100."""
        valid_tool["score"] = 150
        errors = validate_tool(valid_tool)

        assert any("Score must be 0-100" in e for e in errors)

    def test_score_wrong_type(self, valid_tool):
        """Should error for non-numeric score."""
        valid_tool["score"] = "high"
        errors = validate_tool(valid_tool)

        assert any("Score must be 0-100" in e for e in errors)

    def test_score_none_accepted(self, valid_tool):
        """Should accept None score (optional field)."""
        valid_tool["score"] = None
        errors = validate_tool(valid_tool)

        # Should not error - score is optional
        assert not any("Score" in e for e in errors)

    # ========================================================================
    # String Length Tests
    # ========================================================================

    def test_name_too_long(self, valid_tool):
        """Should error for name over 100 characters."""
        valid_tool["name"] = "A" * 101
        errors = validate_tool(valid_tool)

        assert any("Name too long" in e for e in errors)

    def test_name_exactly_100_chars(self, valid_tool):
        """Should accept name exactly 100 characters."""
        valid_tool["name"] = "A" * 100
        errors = validate_tool(valid_tool)

        assert not any("Name too long" in e for e in errors)

    def test_tagline_too_long(self, valid_tool):
        """Should error for tagline over 200 characters."""
        valid_tool["tagline"] = "A" * 201
        errors = validate_tool(valid_tool)

        assert any("Tagline too long" in e for e in errors)

    def test_tagline_exactly_200_chars(self, valid_tool):
        """Should accept tagline exactly 200 characters."""
        valid_tool["tagline"] = "A" * 200
        errors = validate_tool(valid_tool)

        assert not any("Tagline too long" in e for e in errors)

    def test_description_too_long(self, valid_tool):
        """Should error for description over 2000 characters."""
        valid_tool["description"] = "A" * 2001
        errors = validate_tool(valid_tool)

        assert any("Description too long" in e for e in errors)

    def test_description_exactly_2000_chars(self, valid_tool):
        """Should accept description exactly 2000 characters."""
        valid_tool["description"] = "A" * 2000
        errors = validate_tool(valid_tool)

        assert not any("Description too long" in e for e in errors)

    # ========================================================================
    # Multiple Errors Tests
    # ========================================================================

    def test_multiple_errors_reported(self, valid_tool):
        """Should report all errors, not just the first."""
        del valid_tool["id"]
        del valid_tool["name"]
        valid_tool["score"] = 200

        errors = validate_tool(valid_tool)

        assert len(errors) >= 3
        assert any("Missing required field: id" in e for e in errors)
        assert any("Missing required field: name" in e for e in errors)
        assert any("Score must be 0-100" in e for e in errors)

    def test_error_includes_tool_identifier(self, valid_tool):
        """Should include tool identifier in error messages."""
        del valid_tool["id"]
        errors = validate_tool(valid_tool)

        # Should use name as identifier when id is missing
        assert any("Test Tool" in e for e in errors)

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_tool(self):
        """Should error for completely empty tool."""
        errors = validate_tool({})

        assert len(errors) > 0
        # Should have errors for all required fields
        assert any("Missing required field" in e for e in errors)

    def test_tool_with_extra_fields(self, valid_tool):
        """Should not error for extra fields beyond schema."""
        valid_tool["custom_field"] = "some value"
        valid_tool["another_field"] = 123

        errors = validate_tool(valid_tool)

        # Extra fields should be ignored
        assert errors == []

    def test_unicode_in_strings(self, valid_tool):
        """Should handle Unicode characters in strings."""
        valid_tool["name"] = "日本語ツール"
        valid_tool["tagline"] = "これはテストです"
        valid_tool["description"] = "説明文 with émojis 🚀"

        errors = validate_tool(valid_tool)

        # Should not error on Unicode
        assert errors == []

    def test_empty_strings_allowed(self, valid_tool):
        """Should handle empty strings in optional fields."""
        valid_tool["description"] = ""

        errors = validate_tool(valid_tool)

        # Empty optional string is OK
        assert not any("description" in e.lower() for e in errors)


# ============================================================================
# Integration Tests
# ============================================================================

class TestValidationIntegration:
    """Test validation integration scenarios."""

    def test_validate_real_world_tool(self):
        """Should validate a realistic tool example."""
        tool = {
            "id": "claude-ai",
            "name": "Claude AI",
            "tagline": "AI assistant by Anthropic",
            "description": "Claude is a next-generation AI assistant for your tasks",
            "categories": ["ai", "automation"],
            "links": {
                "official": "https://claude.ai",
                "github": "https://github.com/anthropics"
            },
            "source": "producthunt",
            "source_rank": 1,
            "source_votes": 523,
            "topics": ["ai", "llm", "chatbot"],
            "first_seen_at": "2025-01-01",
            "published": True,
            "score": 92.5
        }

        errors = validate_tool(tool)
        assert errors == []

    def test_validate_minimal_real_tool(self):
        """Should validate a minimal but realistic tool."""
        tool = {
            "id": "simple-tool",
            "name": "Simple Tool",
            "tagline": "Just a simple tool",
            "categories": ["other"],
            "links": {
                "official": "https://simple.com"
            },
            "source": "manual",
            "first_seen_at": "2025-01-01"
        }

        errors = validate_tool(tool)
        assert errors == []

    def test_collect_all_validation_errors(self):
        """Should collect comprehensive validation errors."""
        bad_tool = {
            "id": "Bad Tool ID",  # Invalid format
            "name": "A" * 101,    # Too long
            "tagline": "",        # Present but maybe concerning
            "categories": [],     # Empty
            "links": {
                "official": "not-a-url"  # Invalid
            },
            "source": "twitter",  # Invalid source
            "first_seen_at": "2025-99-99",  # Invalid date
            "score": 150          # Out of range
        }

        errors = validate_tool(bad_tool)

        # Should have multiple errors
        assert len(errors) >= 5
        error_text = " ".join(errors)

        assert "Invalid ID format" in error_text
        assert "Name too long" in error_text
        assert "Categories must be non-empty" in error_text
        assert "Invalid official URL" in error_text
        assert "Invalid source" in error_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
