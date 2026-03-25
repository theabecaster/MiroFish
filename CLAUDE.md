# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is MiroFish

MiroFish is a multi-agent simulation engine that builds knowledge graphs from documents, runs social simulations (Twitter/Reddit platforms via OASIS/CAMEL-AI), generates analytical reports, and provides an interactive interview mode. It follows a 5-step workflow: Graph Build → Environment Setup → Simulation → Report → Interaction.

## Commands

```bash
# Setup
npm run setup          # Install root + frontend deps
npm run setup:backend  # Install Python deps via uv
npm run setup:all      # Both

# Development (starts frontend on :3000, backend on :5001)
npm run dev            # Both concurrently
npm run frontend       # Frontend only (Vite dev server)
npm run backend        # Backend only (Flask via uv)

# Build
npm run build          # Frontend production build

# Docker
docker compose up -d   # Full stack
```

## Architecture

**Monorepo** with two main directories:

- `frontend/` — Vue 3 + Vite SPA. D3 for graph visualization. Axios for API calls with retry logic.
- `backend/` — Flask (Python 3.11+). Uses `uv` for package management. Entry point: `backend/run.py`.

**Backend structure:**
- `app/api/` — Three Flask blueprints: `graph`, `simulation`, `report`
- `app/services/` — All business logic (~28 files). Key services: `OntologyGenerator`, `GraphBuilderService`, `SimulationRunner`, `ReportAgent`, `ZepToolsService`
- `app/models/` — `Project` and `Task` data models (JSON file persistence, not a database)
- `app/utils/` — `llm_client` (OpenAI SDK wrapper), `file_parser`, `logger`
- `app/config.py` — Central configuration from environment variables

**External dependencies:**
- **Zep Cloud** — Knowledge graph storage and vector search (requires `ZEP_API_KEY`)
- **LLM API** — Any OpenAI SDK-compatible endpoint (requires `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`)
- **OASIS/CAMEL-AI** — Multi-agent simulation framework, runs as subprocess

**Frontend routes:**
- `/` → Home (project list)
- `/process/:projectId` → Steps 1-2 (graph build + env setup)
- `/simulation/:simulationId` → Step 3 (simulation control)
- `/simulation/:simulationId/start` → Simulation runner
- `/report/:reportId` → Step 4 (report view)
- `/interaction/:reportId` → Step 5 (interview)

**Data flow:** Frontend → Axios → Flask blueprints → Services → Zep Cloud / LLM API / OASIS subprocess. Async tasks use threading with progress tracking via `Task` model.

## Environment

Copy `.env.example` to `.env`. Required keys: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `ZEP_API_KEY`. Optional boost LLM config available for a secondary model.

## Key Patterns

- LLM responses are parsed with robust JSON extraction that handles thinking tags and markdown fences (see `llm_client.py`)
- Simulations run in subprocesses communicating via IPC (named pipes/sockets)
- Reports stream section-by-section with structured JSONL agent logs
- Projects and tasks persist as JSON files in `backend/app/uploads/`
- Vite proxies `/api` requests to the Flask backend during development

<!-- GSD: Project and planning context now lives in parent directory (Preflight/CLAUDE.md and Preflight/.planning/) -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.11+ - Backend (Flask API, all services, simulation engine)
- JavaScript (ES Modules) - Frontend (Vue 3 SPA)
- HTML/CSS - Frontend templates within `.vue` single-file components
## Runtime
- Python 3.11+ (specified in `backend/pyproject.toml` `requires-python = ">=3.11"`)
- Node.js >= 18.0.0 (specified in `package.json` `engines`)
- **uv** (Python) - Astral's fast Python package manager. Lockfile: `backend/uv.lock` (present)
- **npm** (Node.js) - Lockfile: `frontend/package-lock.json` (present), root `package-lock.json` (present)
- **hatchling** - Python build backend (`backend/pyproject.toml`)
- **Vite 7.2.4** - Frontend build tool (`frontend/package.json`)
## Frameworks
- **Flask >= 3.0.0** - Python web framework, application factory pattern in `backend/app/__init__.py`
- **Flask-CORS >= 6.0.0** - Cross-origin resource sharing
- **Vue 3.5.24** - Frontend reactive UI framework (`frontend/package.json`)
- **Vue Router 4.6.3** - Client-side routing (`frontend/src/router/index.js`)
- **D3 7.9.0** - Graph visualization library (`frontend/package.json`)
- **Axios 1.13.2** - Frontend HTTP client with retry logic (`frontend/src/api/index.js`)
- **Vite 7.2.4** - Frontend dev server and bundler (`frontend/vite.config.js`)
- **@vitejs/plugin-vue 6.0.1** - Vue 3 Vite plugin
- **concurrently 9.1.2** - Root-level dev dependency for running frontend + backend simultaneously
- **pytest >= 8.0.0** - Python test framework (optional dev dependency in `backend/pyproject.toml`)
- **pytest-asyncio >= 0.23.0** - Async test support
## Key Dependencies
- **openai >= 1.0.0** - OpenAI SDK used as universal LLM client (`backend/app/utils/llm_client.py`). Wraps any OpenAI-compatible API endpoint.
- **zep-cloud == 3.13.0** - Zep Cloud SDK for knowledge graph storage and retrieval (`backend/app/services/zep_tools.py`, `backend/app/services/graph_builder.py`)
- **camel-oasis == 0.2.5** - OASIS multi-agent social simulation framework (`backend/app/services/simulation_runner.py`)
- **camel-ai == 0.2.78** - CAMEL-AI agent framework, dependency of OASIS
- **pydantic >= 2.0.0** - Data validation (used by dependencies and potentially models)
- **PyMuPDF >= 1.24.0** - PDF text extraction (`backend/app/utils/file_parser.py`, imported as `fitz`)
- **charset-normalizer >= 3.0.0** - Character encoding detection for non-UTF-8 files
- **chardet >= 5.0.0** - Fallback encoding detection
- **python-dotenv >= 1.0.0** - Environment variable loading from `.env` files (`backend/app/config.py`)
## Configuration
- Configuration loaded from project root `.env` file via `python-dotenv` in `backend/app/config.py`
- Centralized `Config` class at `backend/app/config.py` reads all env vars
- Frontend uses `VITE_API_BASE_URL` env var (optional, defaults to `http://localhost:5001`)
- `LLM_API_KEY` - API key for LLM provider
- `LLM_BASE_URL` - LLM API endpoint (default: `https://api.openai.com/v1`)
- `LLM_MODEL_NAME` - Model identifier (default: `gpt-4o-mini`)
- `ZEP_API_KEY` - Zep Cloud API key
- `LLM_BOOST_API_KEY` / `LLM_BOOST_BASE_URL` / `LLM_BOOST_MODEL_NAME` - Secondary accelerator LLM
- `FLASK_HOST` (default: `0.0.0.0`)
- `FLASK_PORT` (default: `5001`)
- `FLASK_DEBUG` (default: `True`)
- `OASIS_DEFAULT_MAX_ROUNDS` (default: `10`)
- `REPORT_AGENT_MAX_TOOL_CALLS` (default: `5`)
- `REPORT_AGENT_MAX_REFLECTION_ROUNDS` (default: `2`)
- `REPORT_AGENT_TEMPERATURE` (default: `0.5`)
- `frontend/vite.config.js` - Vite config with dev proxy from `/api` to Flask backend on port 5001
- `backend/pyproject.toml` - Python project metadata and dependencies
- `Dockerfile` - Single container running both frontend and backend
## Data Persistence
- Projects and tasks persist as JSON in `backend/app/uploads/`
- Simulation data in `backend/app/uploads/simulations/`
- Reports in `backend/app/uploads/reports/`
- Models: `backend/app/models/project.py`, `backend/app/models/task.py`
## Docker
- Base: `python:3.11`
- Includes Node.js, npm, and uv (`ghcr.io/astral-sh/uv:0.9.26`)
- Exposes ports 3000 (frontend) and 5001 (backend)
- Volume mount: `./backend/uploads:/app/backend/uploads` for data persistence
- Config: `docker-compose.yml` at project root
## Platform Requirements
- Python 3.11+
- Node.js 18+
- uv package manager (for Python backend)
- npm (for frontend)
- `.env` file with LLM and Zep API keys
- Docker (single container via `docker-compose.yml`)
- Persistent volume for `backend/uploads/`
- Network access to Zep Cloud API and LLM API endpoint
## Logging
- Config: `backend/app/utils/logger.py`
- Console output: INFO level, simple format
- File output: DEBUG level, detailed format with rotation (10MB, 5 backups)
- Log directory: `backend/logs/`
- Named loggers per module (e.g., `mirofish.simulation_runner`, `mirofish.zep_tools`)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Languages
## Naming Patterns
- Use `snake_case.py` for all modules: `graph_builder.py`, `llm_client.py`, `ontology_generator.py`
- Service files named after the domain concept: `report_agent.py`, `simulation_runner.py`, `zep_tools.py`
- Model files are singular nouns: `project.py`, `task.py`
- Use `PascalCase`: `GraphBuilderService`, `OntologyGenerator`, `ProjectManager`, `TaskManager`
- Service classes end with descriptive suffix: `Service`, `Generator`, `Manager`, `Reader`, `Runner`, `Agent`
- Enums use `PascalCase` and extend `str, Enum`: `ProjectStatus`, `TaskStatus`, `SimulationStatus`
- Dataclasses use `PascalCase`: `Project`, `Task`, `GraphInfo`
- Use `snake_case`: `generate_ontology()`, `build_graph()`, `get_project()`
- Private methods prefixed with underscore: `_validate_and_process()`, `_build_user_message()`, `_ensure_projects_dir()`
- Flask route handlers use descriptive names matching the action: `generate_report()`, `get_graph_data()`, `list_projects()`
- Use `snake_case`: `project_id`, `graph_name`, `task_manager`
- Constants use `UPPER_SNAKE_CASE`: `MAX_TEXT_LENGTH_FOR_LLM`, `ONTOLOGY_SYSTEM_PROMPT`, `LOG_DIR`
- ID prefixes use short names: `proj_`, `sim_`, `task_`
- Vue components use `PascalCase.vue`: `GraphPanel.vue`, `Step1GraphBuild.vue`, `Home.vue`
- JS modules use `camelCase.js`: `pendingUpload.js`, `index.js`
- API modules match backend blueprint names: `graph.js`, `simulation.js`, `report.js`
- Use `camelCase`: `generateOntology()`, `buildGraph()`, `getTaskStatus()`, `requestWithRetry()`
- Event handlers prefixed with `handle`: `handleEnterEnvSetup`
- Use `camelCase`: `projectData`, `simulationId`, `currentPhase`
- Reactive state uses `camelCase`: `simulationRequirement`, `isPending`
## Code Style
- No Prettier or ESLint configured for the frontend
- No flake8, pylint, or black configured for the backend
- Indentation: 4 spaces for Python, 2 spaces for Vue/JS (informal convention observed)
- Python follows PEP 8 loosely (no enforced linting)
- No automated linting tools configured
- Backend uses `# noqa: E402, F401` annotations in `backend/app/api/__init__.py` for import ordering
- Python uses f-strings exclusively: `f"项目不存在: {project_id}"`
- JavaScript uses template literals: `` `/api/graph/data/${graphId}` ``
## Comments and Documentation
- Variable names, function names, class names
- Entity type definitions and descriptions (passed to LLM/Zep)
- Log messages to external services
- Use triple-quoted docstrings with Chinese descriptions
- Follow Google-style format with `Args:` and `Returns:` sections
- Module-level docstrings describe the module's purpose
- Use `@param` and `@returns` annotations on API functions in `frontend/src/api/`
- Python API routes use comment blocks to separate sections:
## Import Organization
- Use relative imports within the `app` package: `from ..config import Config`
- Import specific names, not modules: `from ..utils.logger import get_logger` (not `from ..utils import logger`)
- Type imports use `from typing import Dict, Any, List, Optional`
- No path aliases configured. All imports use relative paths (`../api/`, `./index`)
## API Response Format
- `200` - Success (all successful operations)
- `400` - Bad request (missing/invalid parameters)
- `404` - Resource not found
- `500` - Server error (config issues, unhandled exceptions)
## Error Handling
- Every route handler wraps its body in `try/except Exception`
- Exceptions return `jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})` with HTTP 500
- Validation errors return early with HTTP 400
- Services raise exceptions on failure (no `success` envelope)
- Services validate their own inputs: `if not self.api_key: raise ValueError("ZEP_API_KEY 未配置")`
- LLM client raises `ValueError` for invalid JSON responses
- Axios interceptor handles network errors and timeout globally in `frontend/src/api/index.js`
- `requestWithRetry()` provides exponential backoff retry (3 attempts default)
- Components use `try/catch` around API calls
- `backend/app/utils/retry.py` provides `@retry_with_backoff` decorator and `RetryableAPIClient` class
- Exponential backoff with jitter
- Used for external API calls (LLM, Zep)
- `requestWithRetry()` in `frontend/src/api/index.js` with exponential backoff
- Applied to write operations (`generateOntology`, `buildGraph`)
## Logging
- Root: `mirofish`
- API layer: `mirofish.api`, `mirofish.api.report`
- Services: `mirofish.report_agent`, `mirofish.build`
- Utilities: `mirofish.retry`, `mirofish.zep_paging`
- Request middleware: `mirofish.request`
- `logger.info()` - Operation start/complete, major state changes
- `logger.debug()` - Request details, parameter values, progress updates
- `logger.warning()` - Retry attempts, pagination limits reached
- `logger.error()` - Failed operations, exception details
- Console: INFO+ level, simple format `[HH:MM:SS] LEVEL: message`
- File: DEBUG+ level, detailed format `[YYYY-MM-DD HH:MM:SS] LEVEL [name.func:line] message`
- Log files: `backend/logs/YYYY-MM-DD.log`, rotating at 10MB, 5 backups
- Uses `console.log()`, `console.error()`, `console.warn()` directly (no logging framework)
## Async/Background Task Pattern
## Data Model Pattern
- Define with `@dataclass`
- Include `to_dict()` method for JSON serialization
- Include `from_dict()` classmethod for deserialization
- Persist as JSON files on disk (not a database)
- `ProjectManager` at `backend/app/models/project.py` - all methods are `@classmethod`
- `TaskManager` at `backend/app/models/task.py` - singleton pattern, in-memory dict
## Vue Component Pattern
- No Vuex or Pinia. Uses a simple reactive module at `frontend/src/store/pendingUpload.js`
- State shared via `reactive()` objects exported from plain JS modules
- Props drilling from parent views to child components
- Scoped styles in components (some use global styles in `App.vue`)
- No CSS preprocessor (plain CSS)
- No utility framework (no Tailwind, no Bootstrap)
- Custom CSS with monospace font family: `'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace`
- Black and white minimalist design aesthetic
## Flask Blueprint Pattern
## Service Initialization Pattern
## Type Hints
- Function signatures: `def generate(self, document_texts: List[str]) -> Dict[str, Any]:`
- Optional parameters: `Optional[str] = None`
- Uses `typing` module: `Dict`, `Any`, `List`, `Optional`, `Callable`, `Tuple`
- Dataclass fields are typed: `project_id: str`, `ontology: Optional[Dict[str, Any]] = None`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Two-tier client-server architecture (SPA + REST API)
- No database -- all persistence via JSON files on disk (`backend/uploads/`)
- Background tasks run in Python threads, tracked by an in-memory singleton `TaskManager`
- OASIS simulations launch as separate Python subprocesses with file-based IPC (command/response JSON files)
- External services: Zep Cloud for knowledge graph storage, any OpenAI-compatible LLM API
- No authentication or authorization layer
## Layers
- Purpose: Single-page application providing the 5-step workflow UI
- Location: `frontend/src/`
- Contains: Vue 3 components, views, router, API client, minimal reactive store
- Depends on: Backend REST API (via Axios), D3 for graph visualization
- Used by: End users via browser
- Purpose: HTTP request handling, input validation, response formatting
- Location: `backend/app/api/`
- Contains: Three Flask blueprints -- `graph_bp`, `simulation_bp`, `report_bp`
- Depends on: Services layer, Models layer
- Used by: Frontend via `/api/*` routes
- Purpose: All domain logic -- ontology generation, graph building, simulation orchestration, report generation
- Location: `backend/app/services/`
- Contains: 13 service modules (~430KB total)
- Depends on: Utils layer, external APIs (Zep Cloud, LLM), Models layer
- Used by: API layer
- Purpose: Data models and persistence managers for projects, tasks, simulations, reports
- Location: `backend/app/models/`
- Contains: `Project`/`ProjectManager` (JSON file persistence), `Task`/`TaskManager` (in-memory singleton)
- Depends on: Config
- Used by: API layer, Services layer
- Purpose: Cross-cutting utilities -- LLM client, file parsing, logging, retry logic, Zep pagination
- Location: `backend/app/utils/`
- Contains: `LLMClient`, `FileParser`, `retry_with_backoff`, `setup_logger`, `zep_paging`
- Depends on: Config, OpenAI SDK
- Used by: Services layer
- Purpose: Standalone simulation scripts launched as subprocesses by `SimulationRunner`
- Location: `backend/scripts/`
- Contains: `run_parallel_simulation.py`, `run_twitter_simulation.py`, `run_reddit_simulation.py`, `action_logger.py`
- Depends on: OASIS/CAMEL-AI libraries, simulation config JSON files
- Used by: `SimulationRunner` service (via `subprocess.Popen`)
## Data Flow
- Project state: JSON files on disk (`backend/uploads/projects/{id}/project.json`)
- Task state: In-memory singleton `TaskManager` with thread-safe locking (lost on restart)
- Simulation state: JSON files (`simulation_state.json`, `run_state.json`) in simulation directories
- Report state: JSON files in `backend/uploads/reports/{id}/`
- Frontend state: Vue reactive state, no Vuex/Pinia -- minimal `pendingUpload` reactive store
## Key Abstractions
- Purpose: Represents a document analysis project through its lifecycle
- Examples: `backend/app/models/project.py`
- Pattern: Dataclass with JSON file persistence via `ProjectManager` (class methods)
- States: CREATED -> ONTOLOGY_GENERATED -> GRAPH_BUILDING -> GRAPH_COMPLETED | FAILED
- Purpose: Tracks progress of long-running background operations (graph build, report generation)
- Examples: `backend/app/models/task.py`
- Pattern: In-memory singleton `TaskManager` with thread-safe dict storage
- States: PENDING -> PROCESSING -> COMPLETED | FAILED
- Purpose: Configuration and metadata for a simulation setup
- Examples: `backend/app/services/simulation_manager.py`
- Pattern: Dataclass with JSON file persistence in simulation directory
- Purpose: Real-time tracking of a running simulation (rounds, actions, per-platform progress)
- Examples: `backend/app/services/simulation_runner.py`
- Pattern: Dataclass tracking subprocess output, serialized to `run_state.json`
- Purpose: Unified wrapper around any OpenAI-compatible LLM endpoint
- Examples: `backend/app/utils/llm_client.py`
- Pattern: Wraps OpenAI SDK, provides `chat()` and `chat_json()` with thinking-tag cleanup and robust JSON extraction
- Purpose: Inter-process communication between Flask and simulation subprocess
- Examples: `backend/app/services/simulation_ipc.py`
- Pattern: File-system based command/response -- JSON files in `ipc_commands/` and `ipc_responses/` directories
## Entry Points
- Location: `frontend/src/main.js`
- Triggers: Browser load
- Responsibilities: Mounts Vue app with router
- Location: `backend/run.py`
- Triggers: `uv run python run.py` or `npm run backend`
- Responsibilities: Validates config, creates Flask app via factory, starts threaded dev server on port 5001
- Location: `backend/app/__init__.py`
- Triggers: Called by `run.py`
- Responsibilities: Creates Flask app, enables CORS, registers blueprints (`/api/graph`, `/api/simulation`, `/api/report`), registers simulation cleanup handler
- Location: `backend/scripts/run_parallel_simulation.py`
- Triggers: Spawned by `SimulationRunner` via `subprocess.Popen`
- Responsibilities: Runs OASIS Twitter/Reddit simulations, logs actions, enters IPC wait mode
## Error Handling
- API routes wrap all logic in try/except, return `{"success": false, "error": "message"}` with appropriate HTTP status codes
- `retry_with_backoff` decorator (`backend/app/utils/retry.py`) provides exponential backoff for external API calls (LLM, Zep)
- `LLMClient.chat_json()` has fallback: tries `response_format: json_object` first, then retries without it for providers that don't support it
- Thinking tag cleanup (`<think>...</think>`) handles reasoning models that leak internal chain-of-thought
- Background tasks catch all exceptions and update `TaskManager` with failure status
- Simulation subprocess failures detected via process exit code and output file monitoring
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD: Workflow enforcement and developer profile now in parent CLAUDE.md (Preflight/CLAUDE.md) -->
