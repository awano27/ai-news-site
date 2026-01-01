#!/usr/bin/env python3
"""
Unit tests for scripts/ingest.py

Tests cover:
- normalize_domain function
- calculate_score function
- is_duplicate function
- generate_id function (from BaseCollector)
- enhance_categories function

Usage:
    pytest tests/test_ingest.py -v
"""

import sys
from pathlib import Path
from datetime import date

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest import (
    normalize_domain,
    calculate_score,
    is_duplicate,
    enhance_categories
)
from scripts.collectors.base import BaseCollector


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_tool():
    """Create a sample tool for testing."""
    return {
        "id": "test-tool",
        "name": "Test Tool",
        "tagline": "A test tool for testing",
        "description": "This is a longer description for testing purposes that is over 50 characters",
        "categories": ["ai", "dev"],
        "links": {
            "official": "https://example.com/test"
        },
        "source": "producthunt",
        "source_rank": 3,
        "source_votes": 150,
        "topics": ["ai", "automation", "productivity"],
        "first_seen_at": "2025-01-01",
        "published": False
    }


@pytest.fixture
def existing_tools():
    """Create a dict of existing tools for deduplication testing."""
    return {
        "existing-tool": {
            "id": "existing-tool",
            "name": "Existing Tool",
            "links": {"official": "https://example.com"}
        },
        "similar-name": {
            "id": "similar-name",
            "name": "AI Productivity Suite",
            "links": {"official": "https://different.com"}
        }
    }


@pytest.fixture
def base_collector():
    """Create a concrete instance of BaseCollector for testing."""
    class TestCollector(BaseCollector):
        @property
        def source_name(self):
            return "test"

        def collect(self, target_date=None):
            return []

    return TestCollector()


# ============================================================================
# normalize_domain Tests
# ============================================================================

class TestNormalizeDomain:
    """Test URL domain normalization."""

    def test_basic_url(self):
        """Should extract domain from basic URL."""
        url = "https://example.com/path/to/page"
        assert normalize_domain(url) == "example.com"

    def test_removes_www_prefix(self):
        """Should remove www. prefix from domain."""
        url = "https://www.example.com/path"
        assert normalize_domain(url) == "example.com"

    def test_lowercase_domain(self):
        """Should convert domain to lowercase."""
        url = "https://EXAMPLE.COM/path"
        assert normalize_domain(url) == "example.com"

    def test_http_scheme(self):
        """Should handle http:// URLs."""
        url = "http://example.com"
        assert normalize_domain(url) == "example.com"

    def test_with_port(self):
        """Should handle URLs with port numbers."""
        url = "https://example.com:8080/path"
        assert normalize_domain(url) == "example.com:8080"

    def test_subdomain_preserved(self):
        """Should preserve subdomains (except www)."""
        url = "https://api.example.com/v1"
        assert normalize_domain(url) == "api.example.com"

    def test_empty_string(self):
        """Should return empty string for empty input."""
        assert normalize_domain("") == ""

    def test_invalid_url(self):
        """Should return empty string for invalid URL."""
        assert normalize_domain("not-a-url") == ""

    def test_none_input(self):
        """Should handle None input gracefully."""
        assert normalize_domain(None) == ""


# ============================================================================
# calculate_score Tests
# ============================================================================

class TestCalculateScore:
    """Test tool scoring algorithm."""

    def test_base_score(self):
        """Should return at least base score of 50."""
        tool = {"id": "test", "categories": []}
        score = calculate_score(tool)
        assert score >= 50.0

    def test_source_rank_bonus(self):
        """Should add bonus for high source rank (low number)."""
        tool_rank1 = {"source_rank": 1, "categories": []}
        tool_rank10 = {"source_rank": 10, "categories": []}

        score1 = calculate_score(tool_rank1)
        score10 = calculate_score(tool_rank10)

        assert score1 > score10

    def test_votes_bonus(self):
        """Should add bonus for votes (logarithmic scale)."""
        tool_high_votes = {"source_votes": 1000, "categories": []}
        tool_low_votes = {"source_votes": 10, "categories": []}

        score_high = calculate_score(tool_high_votes)
        score_low = calculate_score(tool_low_votes)

        assert score_high > score_low

    def test_official_url_bonus(self):
        """Should add bonus for non-GitHub/PH official URL."""
        tool_with_url = {
            "links": {"official": "https://myproduct.com"},
            "categories": []
        }
        tool_github = {
            "links": {"official": "https://github.com/user/repo"},
            "categories": []
        }

        score_with_url = calculate_score(tool_with_url)
        score_github = calculate_score(tool_github)

        assert score_with_url > score_github

    def test_description_bonus(self):
        """Should add bonus for having description over 50 chars."""
        tool_with_desc = {
            "description": "This is a long description that is definitely over 50 characters in length",
            "categories": []
        }
        tool_short_desc = {
            "description": "Short",
            "categories": []
        }

        score_with_desc = calculate_score(tool_with_desc)
        score_short = calculate_score(tool_short_desc)

        assert score_with_desc > score_short

    def test_topic_diversity_bonus(self):
        """Should add bonus for having 3+ topics."""
        tool_many_topics = {
            "topics": ["ai", "automation", "productivity", "dev"],
            "categories": []
        }
        tool_few_topics = {
            "topics": ["ai"],
            "categories": []
        }

        score_many = calculate_score(tool_many_topics)
        score_few = calculate_score(tool_few_topics)

        assert score_many > score_few

    def test_category_match_bonus(self):
        """Should add bonus for priority categories."""
        tool_priority = {"categories": ["ai", "automation"]}
        tool_other = {"categories": ["other"]}

        score_priority = calculate_score(tool_priority)
        score_other = calculate_score(tool_other)

        assert score_priority > score_other

    def test_score_range(self):
        """Score should always be between 0 and 100."""
        # Minimal tool
        minimal = {"categories": []}
        assert 0 <= calculate_score(minimal) <= 100

        # Maxed out tool
        maxed = {
            "source_rank": 1,
            "source_votes": 10000,
            "links": {"official": "https://myproduct.com"},
            "description": "A" * 100,
            "topics": ["a", "b", "c", "d", "e"],
            "categories": ["ai", "automation", "meeting"]
        }
        assert 0 <= calculate_score(maxed) <= 100

    def test_complete_tool_scoring(self, sample_tool):
        """Should calculate score correctly for complete tool."""
        score = calculate_score(sample_tool)

        assert isinstance(score, float)
        assert 50 < score <= 100  # Should be above base
        assert score == round(score, 1)  # Check precision


# ============================================================================
# is_duplicate Tests
# ============================================================================

class TestIsDuplicate:
    """Test duplicate detection logic."""

    def test_exact_id_match(self, existing_tools):
        """Should detect exact ID match as duplicate."""
        new_tool = {"id": "existing-tool", "name": "Different Name"}
        seen_domains = set()

        assert is_duplicate(new_tool, existing_tools, seen_domains) is True

    def test_domain_match(self, existing_tools):
        """Should detect same domain as duplicate."""
        new_tool = {
            "id": "new-tool",
            "name": "New Tool",
            "links": {"official": "https://example.com/different-path"}
        }
        seen_domains = {"example.com"}

        assert is_duplicate(new_tool, existing_tools, seen_domains) is True

    def test_fuzzy_name_match(self, existing_tools):
        """Should detect very similar names as duplicates."""
        new_tool = {
            "id": "new-id",
            "name": "AI Productivity Suit",  # Typo of "Suite" -> high similarity
            "links": {"official": "https://unique.com"}
        }
        seen_domains = set()

        # Name similarity: "AI Productivity Suite" vs "AI Productivity Suit" > 0.85
        assert is_duplicate(new_tool, existing_tools, seen_domains) is True

    def test_different_tool_not_duplicate(self, existing_tools):
        """Should not mark completely different tool as duplicate."""
        new_tool = {
            "id": "completely-different",
            "name": "Totally Different Product",
            "links": {"official": "https://totally-different.com"}
        }
        seen_domains = set()

        assert is_duplicate(new_tool, existing_tools, seen_domains) is False

    def test_www_domain_normalization(self, existing_tools):
        """Should detect duplicates even with www. prefix."""
        new_tool = {
            "id": "new-tool",
            "name": "New Tool",
            "links": {"official": "https://www.example.com"}
        }
        # Seen domains has normalized version
        seen_domains = {"example.com"}

        assert is_duplicate(new_tool, existing_tools, seen_domains) is True

    def test_missing_official_link(self, existing_tools):
        """Should handle tools without official link."""
        new_tool = {
            "id": "new-tool",
            "name": "New Tool",
            "links": {}
        }
        seen_domains = set()

        # Should not crash, but won't match on domain
        result = is_duplicate(new_tool, existing_tools, seen_domains)
        assert isinstance(result, bool)

    def test_case_insensitive_name_matching(self, existing_tools):
        """Should match names case-insensitively."""
        new_tool = {
            "id": "new-id",
            "name": "EXISTING TOOL",  # Same as "Existing Tool" but uppercase
            "links": {"official": "https://unique.com"}
        }
        seen_domains = set()

        assert is_duplicate(new_tool, existing_tools, seen_domains) is True


# ============================================================================
# generate_id Tests (from BaseCollector)
# ============================================================================

class TestGenerateId:
    """Test ID generation from names."""

    def test_basic_name(self, base_collector):
        """Should convert simple name to slug."""
        assert base_collector.generate_id("Test Tool") == "test-tool"

    def test_special_characters(self, base_collector):
        """Should replace special characters with hyphens."""
        assert base_collector.generate_id("AI @ Work!") == "ai-work"

    def test_multiple_spaces(self, base_collector):
        """Should collapse multiple spaces into single hyphen."""
        assert base_collector.generate_id("Multi   Space   Tool") == "multi-space-tool"

    def test_unicode_characters(self, base_collector):
        """Should handle unicode characters."""
        assert base_collector.generate_id("Café ☕ Tool") == "caf-tool"

    def test_leading_trailing_hyphens(self, base_collector):
        """Should remove leading/trailing hyphens."""
        assert base_collector.generate_id("--Test Tool--") == "test-tool"

    def test_numbers_preserved(self, base_collector):
        """Should preserve numbers in slug."""
        assert base_collector.generate_id("GPT-4 Tool") == "gpt-4-tool"

    def test_length_limit(self, base_collector):
        """Should limit slug to 50 characters."""
        long_name = "A" * 100
        result = base_collector.generate_id(long_name)

        assert len(result) <= 50
        assert not result.endswith("-")  # Should trim trailing hyphen

    def test_empty_string(self, base_collector):
        """Should handle empty string."""
        assert base_collector.generate_id("") == ""

    def test_only_special_chars(self, base_collector):
        """Should handle names with only special characters."""
        assert base_collector.generate_id("!@#$%^&*()") == ""


# ============================================================================
# enhance_categories Tests
# ============================================================================

class TestEnhanceCategories:
    """Test category enhancement logic."""

    def test_existing_categories_preserved(self):
        """Should keep existing categories."""
        tool = {
            "name": "Test",
            "tagline": "A test tool",
            "description": "Testing",
            "topics": [],
            "categories": ["dev"]
        }

        result = enhance_categories(tool)
        assert "dev" in result

    def test_ai_keywords_detected(self):
        """Should detect AI-related keywords."""
        tool = {
            "name": "GPT Assistant",
            "tagline": "Machine learning powered",
            "description": "Uses LLM technology",
            "topics": [],
            "categories": []
        }

        result = enhance_categories(tool)
        assert "ai" in result

    def test_meeting_keywords_detected(self):
        """Should detect meeting-related keywords."""
        tool = {
            "name": "Video Conferencing Tool",
            "tagline": "Transcribe your meetings",
            "description": "Record and transcribe Zoom calls",
            "topics": [],
            "categories": []
        }

        result = enhance_categories(tool)
        assert "meeting" in result

    def test_multiple_categories_added(self):
        """Should add multiple matching categories."""
        tool = {
            "name": "AI Meeting Assistant",
            "tagline": "Automate meeting notes",
            "description": "Uses GPT to transcribe and summarize video calls",
            "topics": ["automation", "productivity"],
            "categories": []
        }

        result = enhance_categories(tool)
        # Should match ai, meeting, and automation
        assert "ai" in result
        assert "meeting" in result
        assert "automation" in result

    def test_topics_analyzed(self):
        """Should analyze topics for category keywords."""
        tool = {
            "name": "Tool",
            "tagline": "A tool",
            "description": "Testing",
            "topics": ["documentation", "knowledge-base"],
            "categories": []
        }

        result = enhance_categories(tool)
        assert "docs" in result

    def test_default_other_category(self):
        """Should add 'other' if no categories match."""
        tool = {
            "name": "Random Tool",
            "tagline": "Something random",
            "description": "No specific category",
            "topics": [],
            "categories": []
        }

        result = enhance_categories(tool)
        assert "other" in result
        assert len(result) == 1

    def test_case_insensitive_matching(self):
        """Should match keywords case-insensitively."""
        tool = {
            "name": "MEETING TOOL",
            "tagline": "VIDEO CONFERENCE",
            "description": "ZOOM INTEGRATION",
            "topics": [],
            "categories": []
        }

        result = enhance_categories(tool)
        assert "meeting" in result

    def test_no_duplicate_categories(self):
        """Should not add duplicate categories."""
        tool = {
            "name": "AI AI AI",
            "tagline": "artificial intelligence",
            "description": "machine learning GPT",
            "topics": ["ai", "ml"],
            "categories": ["ai"]
        }

        result = enhance_categories(tool)
        assert result.count("ai") == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test integration of multiple functions together."""

    def test_complete_tool_processing(self, sample_tool):
        """Should process a complete tool through all functions."""
        # Calculate score
        score = calculate_score(sample_tool)
        assert 50 < score <= 100

        # Enhance categories
        enhanced_categories = enhance_categories(sample_tool)
        assert len(enhanced_categories) > 0
        assert "ai" in enhanced_categories

        # Check not duplicate against empty set
        existing = {}
        seen = set()
        assert is_duplicate(sample_tool, existing, seen) is False

    def test_collector_creates_valid_tool(self, base_collector):
        """Should create valid tool dict from BaseCollector."""
        tool = base_collector.create_tool_dict(
            name="Test Product",
            tagline="A great test product",
            official_url="https://test-product.com",
            categories=["ai", "dev"],
            source_rank=5,
            source_votes=100,
            description="A longer description for testing",
            topics=["ai", "testing", "automation"]
        )

        # Verify structure
        assert "id" in tool
        assert tool["name"] == "Test Product"
        assert tool["source"] == "test"
        assert tool["published"] is False

        # Verify ID generation
        assert tool["id"] == "test-product"

        # Should be scorable
        score = calculate_score(tool)
        assert score > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
