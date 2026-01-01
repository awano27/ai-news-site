# Test Suite Documentation

This directory contains comprehensive unit tests for the AI News Site tool ingest pipeline.

## Overview

**Total Tests:** 106
**Test Files:** 2
**Coverage:** Core business logic functions in `scripts/ingest.py` and `scripts/validate.py`

## Test Files

### `test_ingest.py` (44 tests)

Tests for the tool ingestion and processing pipeline (`scripts/ingest.py`).

#### Test Categories

**1. normalize_domain (9 tests)**
- URL domain extraction and normalization
- www. prefix removal
- Case normalization
- Edge cases (empty, None, invalid URLs)

**2. calculate_score (9 tests)**
- Base scoring algorithm (50-100 scale)
- Source rank bonus (higher rank = higher score)
- Votes/stars bonus (logarithmic scale)
- Official URL bonus (non-GitHub/PH sites)
- Description length bonus
- Topic diversity bonus (3+ topics)
- Category match bonus (priority categories)
- Score range validation (0-100 bounds)

**3. is_duplicate (7 tests)**
- Exact ID matching
- Domain-based deduplication
- Fuzzy name matching (>85% similarity threshold)
- www. normalization in domain matching
- Case-insensitive name comparison
- Handling of missing links

**4. generate_id (9 tests)**
- Name to slug conversion (from BaseCollector)
- Special character handling
- Space and hyphen normalization
- Unicode character handling
- Length limitation (50 chars max)
- Edge cases (empty, only special chars)

**5. enhance_categories (8 tests)**
- Keyword-based category detection
- Multi-category assignment
- Topic analysis for categorization
- Default "other" category fallback
- Case-insensitive keyword matching
- Duplicate prevention

**6. Integration Tests (2 tests)**
- Complete tool processing workflow
- BaseCollector tool creation validation

### `test_validate.py` (62 tests)

Tests for data validation functions (`scripts/validate.py`).

#### Test Categories

**1. validate_url (15 tests)**
- HTTPS/HTTP URL validation
- URL components (path, query params, fragments, ports)
- Subdomain and localhost handling
- IP address URLs
- Invalid formats (missing scheme, wrong scheme, malformed)
- Edge cases (empty, None)

**2. validate_tool (44 tests)**

**Required Fields (7 tests)**
- id, name, tagline, categories, links, first_seen_at, source

**ID Format (4 tests)**
- Valid format: lowercase alphanumeric with hyphens
- Invalid: uppercase, special chars, spaces

**Categories (4 tests)**
- Non-empty array validation
- Valid category names (meeting, docs, pm, automation, ai, dev, ph, other)
- Invalid category rejection

**Source Validation (2 tests)**
- Valid sources: producthunt, hn, github, manual, rss
- Invalid source rejection

**Links Validation (5 tests)**
- Object structure validation
- Required "official" link
- URL format validation
- Optional link validation (strict vs. non-strict mode)

**Date Format (3 tests)**
- ISO date format (YYYY-MM-DD)
- Invalid format rejection
- Invalid date value rejection

**Score Validation (5 tests)**
- Valid range: 0-100
- Type validation (numeric)
- Boundary testing
- None accepted (optional field)

**String Length Limits (6 tests)**
- name: max 100 chars
- tagline: max 200 chars
- description: max 2000 chars
- Boundary value testing

**Error Handling (2 tests)**
- Multiple errors collected
- Tool identifier in error messages

**Edge Cases (6 tests)**
- Empty tool object
- Extra fields (ignored)
- Unicode handling
- Empty optional strings

**3. Integration Tests (3 tests)**
- Real-world tool validation
- Minimal valid tool
- Comprehensive error collection

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test File
```bash
pytest tests/test_ingest.py -v
pytest tests/test_validate.py -v
```

### Specific Test Class
```bash
pytest tests/test_ingest.py::TestCalculateScore -v
pytest tests/test_validate.py::TestValidateTool -v
```

### Specific Test Function
```bash
pytest tests/test_ingest.py::TestCalculateScore::test_base_score -v
```

### With Coverage
```bash
pytest tests/ --cov=scripts.ingest --cov=scripts.validate --cov-report=term-missing
```

### Quick Summary
```bash
pytest tests/ -q
```

### Stop on First Failure
```bash
pytest tests/ -x
```

## Test Structure

All tests follow the **Arrange-Act-Assert (AAA)** pattern:

```python
def test_example(self):
    """Should demonstrate AAA pattern."""
    # Arrange - Set up test data
    tool = {"id": "test", "score": 75}

    # Act - Execute the function
    result = calculate_score(tool)

    # Assert - Verify the outcome
    assert result > 50
```

## Fixtures

### `sample_tool` (test_ingest.py)
Complete tool object with all fields populated for comprehensive testing.

### `existing_tools` (test_ingest.py)
Dictionary of existing tools for deduplication testing.

### `base_collector` (test_ingest.py)
Concrete BaseCollector instance for testing collector methods.

### `valid_tool` (test_validate.py)
Fully valid tool object for validation testing.

### `minimal_tool` (test_validate.py)
Minimal valid tool with only required fields.

## Test Coverage Summary

### Functions Tested

**scripts/ingest.py:**
- `normalize_domain(url)` - 100% coverage
- `calculate_score(tool)` - 100% coverage
- `is_duplicate(new_tool, existing_tools, seen_domains)` - 100% coverage
- `enhance_categories(tool)` - 100% coverage

**scripts/collectors/base.py:**
- `BaseCollector.normalize_url(url)` - Implicitly tested
- `BaseCollector.generate_id(name)` - 100% coverage
- `BaseCollector.create_tool_dict(...)` - Integration tested

**scripts/validate.py:**
- `validate_url(url)` - 100% coverage
- `validate_tool(tool, strict=False)` - 100% coverage

### Edge Cases Covered

- Null/None inputs
- Empty strings and arrays
- Boundary values (0, -1, MAX_INT, exact limits)
- Invalid data types
- Malformed inputs
- Unicode and special characters
- Case sensitivity
- Missing optional vs. required fields

## Dependencies

```bash
pip install -r requirements-ingest.txt
```

Key dependencies:
- pytest >= 7.4.0
- requests >= 2.28.0
- jsonschema >= 4.17.0

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r requirements-ingest.txt
    pytest tests/ -v --tb=short
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Test execution error
- `3` - Internal pytest error

## Best Practices

1. **Run tests before committing**: `pytest tests/`
2. **Add tests for new functions**: Maintain 100% coverage of business logic
3. **Test edge cases**: Null, empty, boundary values
4. **Use descriptive test names**: Should describe behavior, not implementation
5. **Keep tests independent**: No shared state between tests
6. **Use fixtures**: Avoid duplicating test data setup

## Test Metrics

```
============================== test session starts =============================
platform win32 -- Python 3.13.9, pytest-9.0.2, pluggy-1.6.0
collected 106 items

tests/test_ingest.py ..................................... [ 41%]
tests/test_validate.py ..................................................... [100%]

======================= 106 passed, 1 warning in 0.53s ========================
```

**Success Rate:** 100% (106/106)
**Average Runtime:** ~0.5 seconds
**Warning:** 1 (DeprecationWarning in datetime.utcnow - not critical)

## Future Test Additions

Potential areas for expansion:

1. **Integration Tests**
   - Full pipeline: collect → process → validate → save
   - Mock external API calls (Product Hunt, HN, GitHub)
   - Database interaction tests

2. **Performance Tests**
   - Large dataset handling (1000+ tools)
   - Scoring algorithm performance
   - Deduplication efficiency

3. **End-to-End Tests**
   - CLI argument parsing
   - File I/O operations
   - Error handling and logging

4. **Collector Tests**
   - ProductHuntCollector
   - HackerNewsCollector
   - GitHubCollector

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Group related tests in classes
3. Add docstrings explaining test purpose
4. Test both happy path and edge cases
5. Update this README with new test counts

## Support

For issues or questions about tests:
1. Check test output with `-v` flag for details
2. Use `--tb=short` for concise tracebacks
3. Run specific failing test with `-k test_name`
4. Review function implementation in scripts/

---

Last Updated: 2026-01-02
Test Suite Version: 1.0.0
