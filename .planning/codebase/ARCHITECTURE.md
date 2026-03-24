# Architecture

**Analysis Date:** 2026-03-24

## Pattern Overview

**Overall:** Monorepo with a Vue 3 SPA frontend and Flask API backend, connected via REST. Long-running tasks use background threads with polling-based progress tracking. Simulations run as subprocess scripts communicating via file-system IPC.

**Key Characteristics:**
- Two-tier client-server architecture (SPA + REST API)
- No database -- all persistence via JSON files on disk (`backend/uploads/`)
- Background tasks run in Python threads, tracked by an in-memory singleton `TaskManager`
- OASIS simulations launch as separate Python subprocesses with file-based IPC (command/response JSON files)
- External services: Zep Cloud for knowledge graph storage, any OpenAI-compatible LLM API
- No authentication or authorization layer

## Layers

**Frontend (Presentation):**
- Purpose: Single-page application providing the 5-step workflow UI
- Location: `frontend/src/`
- Contains: Vue 3 components, views, router, API client, minimal reactive store
- Depends on: Backend REST API (via Axios), D3 for graph visualization
- Used by: End users via browser

**API Layer (Controllers):**
- Purpose: HTTP request handling, input validation, response formatting
- Location: `backend/app/api/`
- Contains: Three Flask blueprints -- `graph_bp`, `simulation_bp`, `report_bp`
- Depends on: Services layer, Models layer
- Used by: Frontend via `/api/*` routes

**Services Layer (Business Logic):**
- Purpose: All domain logic -- ontology generation, graph building, simulation orchestration, report generation
- Location: `backend/app/services/`
- Contains: 13 service modules (~430KB total)
- Depends on: Utils layer, external APIs (Zep Cloud, LLM), Models layer
- Used by: API layer

**Models Layer (Data):**
- Purpose: Data models and persistence managers for projects, tasks, simulations, reports
- Location: `backend/app/models/`
- Contains: `Project`/`ProjectManager` (JSON file persistence), `Task`/`TaskManager` (in-memory singleton)
- Depends on: Config
- Used by: API layer, Services layer

**Utils Layer (Infrastructure):**
- Purpose: Cross-cutting utilities -- LLM client, file parsing, logging, retry logic, Zep pagination
- Location: `backend/app/utils/`
- Contains: `LLMClient`, `FileParser`, `retry_with_backoff`, `setup_logger`, `zep_paging`
- Depends on: Config, OpenAI SDK
- Used by: Services layer

**Scripts Layer (Subprocess):**
- Purpose: Standalone simulation scripts launched as subprocesses by `SimulationRunner`
- Location: `backend/scripts/`
- Contains: `run_parallel_simulation.py`, `run_twitter_simulation.py`, `run_reddit_simulation.py`, `action_logger.py`
- Depends on: OASIS/CAMEL-AI libraries, simulation config JSON files
- Used by: `SimulationRunner` service (via `subprocess.Popen`)

## Data Flow

**Step 1 -- Graph Build (Document Upload + Ontology + Knowledge Graph):**

1. User uploads documents (PDF/MD/TXT) via frontend
2. `POST /api/graph/upload` saves files to `backend/uploads/projects/{project_id}/files/`
3. `FileParser` extracts text; saved as `extracted_text.txt` in project dir
4. `POST /api/graph/ontology/generate` sends text to `OntologyGenerator` which uses `LLMClient` to generate entity/relationship type definitions
5. `POST /api/graph/build` launches `GraphBuilderService.build_graph_async()` in a background thread
6. `GraphBuilderService` chunks text via `TextProcessor`, then sends episodes to Zep Cloud API to build a standalone graph
7. Frontend polls `GET /api/graph/build/status/{task_id}` for progress updates from `TaskManager`

**Step 2 -- Environment Setup (Entity Reading + Profile Generation + Simulation Config):**

1. `GET /api/simulation/entities/{graph_id}` reads entities from Zep graph via `ZepEntityReader`
2. `POST /api/simulation/prepare` calls `OasisProfileGenerator` to create agent profiles from entities using LLM
3. `SimulationConfigGenerator` uses LLM to generate simulation parameters (rounds, timing, events)
4. All config saved to `backend/uploads/simulations/{simulation_id}/`

**Step 3 -- Simulation Run:**

1. `POST /api/simulation/run/{simulation_id}/start` triggers `SimulationRunner`
2. `SimulationRunner` spawns `run_parallel_simulation.py` as a subprocess via `subprocess.Popen`
3. The subprocess runs OASIS/CAMEL-AI Twitter and Reddit simulations in parallel
4. Actions logged to `{sim_dir}/twitter/actions.jsonl` and `{sim_dir}/reddit/actions.jsonl`
5. Backend monitors subprocess output files and `run_state.json` for real-time status
6. Frontend polls `GET /api/simulation/run/{simulation_id}/status` for live updates
7. After simulation completes, subprocess enters IPC wait mode for interview commands

**Step 4 -- Report Generation:**

1. `POST /api/report/generate` launches `ReportAgent` in a background thread
2. `ReportAgent` uses ReACT pattern: plans outline, generates each section using LLM with Zep tool calls
3. Tools available: `InsightForge` (deep hybrid search), `PanoramaSearch` (broad search), `QuickSearch`
4. Report saved as JSON + agent log as JSONL in `backend/uploads/reports/{report_id}/`
5. Frontend polls for completion, then renders report

**Step 5 -- Interaction (Interview):**

1. User sends questions to specific agents via `POST /api/simulation/run/{simulation_id}/interview`
2. Backend writes IPC command file to `{sim_dir}/ipc_commands/`
3. Simulation subprocess polls command directory, executes interview, writes response to `{sim_dir}/ipc_responses/`
4. Backend polls response directory and returns result to frontend

**State Management:**
- Project state: JSON files on disk (`backend/uploads/projects/{id}/project.json`)
- Task state: In-memory singleton `TaskManager` with thread-safe locking (lost on restart)
- Simulation state: JSON files (`simulation_state.json`, `run_state.json`) in simulation directories
- Report state: JSON files in `backend/uploads/reports/{id}/`
- Frontend state: Vue reactive state, no Vuex/Pinia -- minimal `pendingUpload` reactive store

## Key Abstractions

**Project:**
- Purpose: Represents a document analysis project through its lifecycle
- Examples: `backend/app/models/project.py`
- Pattern: Dataclass with JSON file persistence via `ProjectManager` (class methods)
- States: CREATED -> ONTOLOGY_GENERATED -> GRAPH_BUILDING -> GRAPH_COMPLETED | FAILED

**Task:**
- Purpose: Tracks progress of long-running background operations (graph build, report generation)
- Examples: `backend/app/models/task.py`
- Pattern: In-memory singleton `TaskManager` with thread-safe dict storage
- States: PENDING -> PROCESSING -> COMPLETED | FAILED

**SimulationState:**
- Purpose: Configuration and metadata for a simulation setup
- Examples: `backend/app/services/simulation_manager.py`
- Pattern: Dataclass with JSON file persistence in simulation directory

**SimulationRunState:**
- Purpose: Real-time tracking of a running simulation (rounds, actions, per-platform progress)
- Examples: `backend/app/services/simulation_runner.py`
- Pattern: Dataclass tracking subprocess output, serialized to `run_state.json`

**LLMClient:**
- Purpose: Unified wrapper around any OpenAI-compatible LLM endpoint
- Examples: `backend/app/utils/llm_client.py`
- Pattern: Wraps OpenAI SDK, provides `chat()` and `chat_json()` with thinking-tag cleanup and robust JSON extraction

**SimulationIPC:**
- Purpose: Inter-process communication between Flask and simulation subprocess
- Examples: `backend/app/services/simulation_ipc.py`
- Pattern: File-system based command/response -- JSON files in `ipc_commands/` and `ipc_responses/` directories

## Entry Points

**Frontend:**
- Location: `frontend/src/main.js`
- Triggers: Browser load
- Responsibilities: Mounts Vue app with router

**Backend:**
- Location: `backend/run.py`
- Triggers: `uv run python run.py` or `npm run backend`
- Responsibilities: Validates config, creates Flask app via factory, starts threaded dev server on port 5001

**Flask App Factory:**
- Location: `backend/app/__init__.py`
- Triggers: Called by `run.py`
- Responsibilities: Creates Flask app, enables CORS, registers blueprints (`/api/graph`, `/api/simulation`, `/api/report`), registers simulation cleanup handler

**Simulation Subprocess:**
- Location: `backend/scripts/run_parallel_simulation.py`
- Triggers: Spawned by `SimulationRunner` via `subprocess.Popen`
- Responsibilities: Runs OASIS Twitter/Reddit simulations, logs actions, enters IPC wait mode

## Error Handling

**Strategy:** Multi-level try/except with logging and user-facing error responses

**Patterns:**
- API routes wrap all logic in try/except, return `{"success": false, "error": "message"}` with appropriate HTTP status codes
- `retry_with_backoff` decorator (`backend/app/utils/retry.py`) provides exponential backoff for external API calls (LLM, Zep)
- `LLMClient.chat_json()` has fallback: tries `response_format: json_object` first, then retries without it for providers that don't support it
- Thinking tag cleanup (`<think>...</think>`) handles reasoning models that leak internal chain-of-thought
- Background tasks catch all exceptions and update `TaskManager` with failure status
- Simulation subprocess failures detected via process exit code and output file monitoring

## Cross-Cutting Concerns

**Logging:** Custom logger setup in `backend/app/utils/logger.py`. Uses Python `logging` with `get_logger('mirofish.{module}')` pattern. Request/response logging via Flask middleware in `backend/app/__init__.py`. Simulation scripts log to `{sim_dir}/simulation.log`.

**Validation:** Minimal -- config validation in `Config.validate()` checks required env vars. API routes do basic input checking (required fields, file extension allowlists). No schema validation library (no Marshmallow/Pydantic schemas for request validation despite Pydantic being a dependency).

**Authentication:** None. All API endpoints are unauthenticated. CORS is configured to allow all origins (`"*"`).

**Concurrency:** Flask runs with `threaded=True`. Background tasks use `threading.Thread`. `TaskManager` uses threading locks for thread safety. Simulation runs as a separate OS process. No async/await in Flask (though `asyncio` is imported in `simulation_runner.py`).

**Encoding:** Extensive UTF-8 handling for Chinese language support -- Windows-specific encoding patches, `ensure_ascii=False` for JSON, fallback encoding detection via `charset-normalizer` and `chardet`.

---

*Architecture analysis: 2026-03-24*
