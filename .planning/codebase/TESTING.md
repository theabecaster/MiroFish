# Testing Patterns

**Analysis Date:** 2026-03-24

## Test Framework

**Backend Runner:**
- pytest >= 8.0.0 (declared as dev dependency in `backend/pyproject.toml`)
- pytest-asyncio >= 0.23.0 (declared but no async tests found in codebase)
- Config: No `pytest.ini`, `setup.cfg`, or `conftest.py` found

**Frontend Runner:**
- No test framework configured
- No vitest, jest, or any testing library in `frontend/package.json`

**Run Commands:**
```bash
# Backend (not currently wired up via npm scripts)
cd backend && uv run pytest            # Would run pytest if tests existed

# Frontend
# No test commands available
```

## Test File Organization

**Location:**
- One test-like script found: `backend/scripts/test_profile_format.py`
- No `tests/` directory exists in either `backend/` or `frontend/`
- No test files co-located with source code

**Naming:**
- The single script uses `test_` prefix: `test_profile_format.py`
- It is a manual validation script, not a pytest test (uses `print()` assertions, not `assert`)

## Existing Test Analysis

**`backend/scripts/test_profile_format.py`:**
- Manual validation script for OASIS profile format generation
- Tests Twitter CSV and Reddit JSON output formats
- Uses `print()` for output verification instead of assertions
- Instantiates `OasisProfileGenerator` via `__new__` (bypasses `__init__`)
- Runs as `if __name__ == "__main__"` script, not discoverable by pytest
- Has no `assert` statements -- relies on visual inspection of printed output

```python
# Pattern used (NOT a proper test):
def test_profile_formats():
    print("=" * 60)
    # ... create test data, call methods, print results ...
    missing = set(required_twitter_fields) - set(rows[0].keys())
    if missing:
        print(f"\n   [错误] 缺少字段: {missing}")
    else:
        print(f"\n   [通过] 所有必需字段都存在")
```

## Test Structure

**No established test structure exists.** There are no:
- Test suites or test classes
- Setup/teardown patterns
- Shared fixtures
- conftest.py files
- Test configuration

## Mocking

**Framework:** Not applicable -- no tests use mocking.

**What Would Need Mocking:**
- `LLMClient` (calls OpenAI API) - `backend/app/utils/llm_client.py`
- `Zep` client (calls Zep Cloud API) - used in `backend/app/services/graph_builder.py`
- OASIS subprocess calls - `backend/app/services/simulation_runner.py`
- File system operations for project persistence - `backend/app/models/project.py`

## Fixtures and Factories

**Test Data:**
- No test fixtures or factories exist
- The manual script in `backend/scripts/test_profile_format.py` creates inline test data:

```python
test_profiles = [
    OasisAgentProfile(
        user_id=0,
        user_name="test_user_123",
        name="Test User",
        bio="A test user for validation",
        # ...
    ),
]
```

**Location:** No dedicated fixtures directory.

## Coverage

**Requirements:** None enforced. No coverage tool configured.

**No coverage tooling exists:**
- No `pytest-cov` in dependencies
- No `.coveragerc` or `[tool.coverage]` in `pyproject.toml`
- No coverage thresholds or CI gates

## Test Types

**Unit Tests:**
- None exist

**Integration Tests:**
- None exist

**E2E Tests:**
- None exist

**Manual Validation Scripts:**
- `backend/scripts/test_profile_format.py` - Profile format validation (run manually)

## CI/CD Test Integration

**CI Pipeline:** GitHub Actions at `.github/workflows/docker-image.yml`
- Only builds and pushes Docker images on tag pushes
- **No test step in CI** -- the pipeline does not run any tests
- No test gates prevent merging

```yaml
# Current CI does NOT include testing:
jobs:
  build-and-push:
    steps:
      - Checkout
      - Set up QEMU
      - Set up Docker Buildx
      - Log in to GHCR
      - Extract metadata
      - Build and push
```

## Test Gaps and Areas with No Coverage

**Critical: The entire codebase has zero automated test coverage.**

### High Priority Gaps

**LLM Client (`backend/app/utils/llm_client.py`):**
- JSON extraction logic (`_extract_json`) with brace-matching algorithm
- Think-tag stripping regex patterns
- Fallback behavior when `response_format` is unsupported
- This is the most recently modified code (recent bugfixes for thinking models) and highest risk

**API Route Handlers (`backend/app/api/`):**
- `graph.py` - File upload, ontology generation, graph build lifecycle
- `simulation.py` - Entity reading, simulation creation/control, interview
- `report.py` - Report generation, retrieval, conversation
- Input validation, error responses, status code correctness

**Data Models (`backend/app/models/`):**
- `project.py` - JSON persistence, `to_dict()`/`from_dict()` round-trip
- `task.py` - Thread-safe singleton, concurrent task updates

### Medium Priority Gaps

**Services (`backend/app/services/`):**
- `ontology_generator.py` - LLM prompt construction, ontology validation/post-processing
- `graph_builder.py` - Zep API orchestration, chunking, episode waiting
- `report_agent.py` - ReACT agent loop, tool calling, section generation
- `simulation_runner.py` - Subprocess management, IPC communication
- `oasis_profile_generator.py` - Profile format generation (partially covered by manual script)

**Utilities (`backend/app/utils/`):**
- `retry.py` - Retry decorator behavior, backoff timing, jitter
- `file_parser.py` - PDF/MD/TXT parsing, encoding detection fallback
- `zep_paging.py` - Pagination with retry, cursor handling

### Low Priority Gaps

**Frontend (`frontend/src/`):**
- All Vue components (7 components, 7 views)
- API client layer (`frontend/src/api/`)
- Router configuration
- Store logic

### Recommended Test Infrastructure Setup

To establish testing, create:

1. `backend/tests/conftest.py` - Shared fixtures (mock LLM client, mock Zep client, temp project dirs)
2. `backend/tests/test_llm_client.py` - Unit tests for JSON extraction and think-tag stripping
3. `backend/tests/test_models.py` - Round-trip serialization tests for Project and Task
4. `backend/tests/test_api_graph.py` - Integration tests for graph blueprint routes
5. Add `pytest` run step to `.github/workflows/docker-image.yml`
6. Add `npm run test` script and vitest to `frontend/package.json`

---

*Testing analysis: 2026-03-24*
