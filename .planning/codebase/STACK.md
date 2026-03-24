# Technology Stack

**Analysis Date:** 2026-03-24

## Languages

**Primary:**
- Python 3.11+ - Backend (Flask API, all services, simulation engine)
- JavaScript (ES Modules) - Frontend (Vue 3 SPA)

**Secondary:**
- HTML/CSS - Frontend templates within `.vue` single-file components

## Runtime

**Environment:**
- Python 3.11+ (specified in `backend/pyproject.toml` `requires-python = ">=3.11"`)
- Node.js >= 18.0.0 (specified in `package.json` `engines`)

**Package Managers:**
- **uv** (Python) - Astral's fast Python package manager. Lockfile: `backend/uv.lock` (present)
- **npm** (Node.js) - Lockfile: `frontend/package-lock.json` (present), root `package-lock.json` (present)

**Build System:**
- **hatchling** - Python build backend (`backend/pyproject.toml`)
- **Vite 7.2.4** - Frontend build tool (`frontend/package.json`)

## Frameworks

**Core:**
- **Flask >= 3.0.0** - Python web framework, application factory pattern in `backend/app/__init__.py`
- **Flask-CORS >= 6.0.0** - Cross-origin resource sharing
- **Vue 3.5.24** - Frontend reactive UI framework (`frontend/package.json`)
- **Vue Router 4.6.3** - Client-side routing (`frontend/src/router/index.js`)

**Visualization:**
- **D3 7.9.0** - Graph visualization library (`frontend/package.json`)

**HTTP Client:**
- **Axios 1.13.2** - Frontend HTTP client with retry logic (`frontend/src/api/index.js`)

**Build/Dev:**
- **Vite 7.2.4** - Frontend dev server and bundler (`frontend/vite.config.js`)
- **@vitejs/plugin-vue 6.0.1** - Vue 3 Vite plugin
- **concurrently 9.1.2** - Root-level dev dependency for running frontend + backend simultaneously

**Testing:**
- **pytest >= 8.0.0** - Python test framework (optional dev dependency in `backend/pyproject.toml`)
- **pytest-asyncio >= 0.23.0** - Async test support

## Key Dependencies

**Critical (Backend):**
- **openai >= 1.0.0** - OpenAI SDK used as universal LLM client (`backend/app/utils/llm_client.py`). Wraps any OpenAI-compatible API endpoint.
- **zep-cloud == 3.13.0** - Zep Cloud SDK for knowledge graph storage and retrieval (`backend/app/services/zep_tools.py`, `backend/app/services/graph_builder.py`)
- **camel-oasis == 0.2.5** - OASIS multi-agent social simulation framework (`backend/app/services/simulation_runner.py`)
- **camel-ai == 0.2.78** - CAMEL-AI agent framework, dependency of OASIS
- **pydantic >= 2.0.0** - Data validation (used by dependencies and potentially models)

**File Processing (Backend):**
- **PyMuPDF >= 1.24.0** - PDF text extraction (`backend/app/utils/file_parser.py`, imported as `fitz`)
- **charset-normalizer >= 3.0.0** - Character encoding detection for non-UTF-8 files
- **chardet >= 5.0.0** - Fallback encoding detection

**Infrastructure (Backend):**
- **python-dotenv >= 1.0.0** - Environment variable loading from `.env` files (`backend/app/config.py`)

## Configuration

**Environment:**
- Configuration loaded from project root `.env` file via `python-dotenv` in `backend/app/config.py`
- Centralized `Config` class at `backend/app/config.py` reads all env vars
- Frontend uses `VITE_API_BASE_URL` env var (optional, defaults to `http://localhost:5001`)

**Required env vars:**
- `LLM_API_KEY` - API key for LLM provider
- `LLM_BASE_URL` - LLM API endpoint (default: `https://api.openai.com/v1`)
- `LLM_MODEL_NAME` - Model identifier (default: `gpt-4o-mini`)
- `ZEP_API_KEY` - Zep Cloud API key

**Optional env vars:**
- `LLM_BOOST_API_KEY` / `LLM_BOOST_BASE_URL` / `LLM_BOOST_MODEL_NAME` - Secondary accelerator LLM
- `FLASK_HOST` (default: `0.0.0.0`)
- `FLASK_PORT` (default: `5001`)
- `FLASK_DEBUG` (default: `True`)
- `OASIS_DEFAULT_MAX_ROUNDS` (default: `10`)
- `REPORT_AGENT_MAX_TOOL_CALLS` (default: `5`)
- `REPORT_AGENT_MAX_REFLECTION_ROUNDS` (default: `2`)
- `REPORT_AGENT_TEMPERATURE` (default: `0.5`)

**Build:**
- `frontend/vite.config.js` - Vite config with dev proxy from `/api` to Flask backend on port 5001
- `backend/pyproject.toml` - Python project metadata and dependencies
- `Dockerfile` - Single container running both frontend and backend

## Data Persistence

**Storage:** JSON files on local filesystem (no database)
- Projects and tasks persist as JSON in `backend/app/uploads/`
- Simulation data in `backend/app/uploads/simulations/`
- Reports in `backend/app/uploads/reports/`
- Models: `backend/app/models/project.py`, `backend/app/models/task.py`

**No traditional database** - all structured data is file-based JSON.

## Docker

**Image:** `ghcr.io/666ghj/mirofish:latest`
- Base: `python:3.11`
- Includes Node.js, npm, and uv (`ghcr.io/astral-sh/uv:0.9.26`)
- Exposes ports 3000 (frontend) and 5001 (backend)
- Volume mount: `./backend/uploads:/app/backend/uploads` for data persistence
- Config: `docker-compose.yml` at project root

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js 18+
- uv package manager (for Python backend)
- npm (for frontend)
- `.env` file with LLM and Zep API keys

**Production:**
- Docker (single container via `docker-compose.yml`)
- Persistent volume for `backend/uploads/`
- Network access to Zep Cloud API and LLM API endpoint

## Logging

**Framework:** Python `logging` module with custom setup
- Config: `backend/app/utils/logger.py`
- Console output: INFO level, simple format
- File output: DEBUG level, detailed format with rotation (10MB, 5 backups)
- Log directory: `backend/logs/`
- Named loggers per module (e.g., `mirofish.simulation_runner`, `mirofish.zep_tools`)

---

*Stack analysis: 2026-03-24*
