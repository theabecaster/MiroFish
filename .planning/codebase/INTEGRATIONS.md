# External Integrations

**Analysis Date:** 2026-03-24

## APIs & External Services

### LLM API (OpenAI-Compatible)

Any LLM provider exposing an OpenAI-compatible chat completions endpoint.

- **SDK/Client:** `openai` Python SDK >= 1.0.0
- **Wrapper:** `backend/app/utils/llm_client.py` (`LLMClient` class)
- **Auth:** Bearer token via `LLM_API_KEY` env var
- **Endpoint:** Configurable via `LLM_BASE_URL` (default: `https://api.openai.com/v1`)
- **Model:** Configurable via `LLM_MODEL_NAME` (default: `gpt-4o-mini`)
- **Default recommended provider:** Alibaba DashScope (Qwen models) per `.env.example`

**Usage patterns:**
- `LLMClient.chat()` - Plain text completions with thinking-tag cleanup (strips `<think>` blocks from reasoning models)
- `LLMClient.chat_json()` - JSON-mode completions with fallback for providers that do not support `response_format: json_object`
- Called from: `backend/app/services/ontology_generator.py`, `backend/app/services/report_agent.py`, `backend/app/services/simulation_config_generator.py`, `backend/app/services/oasis_profile_generator.py`

**Optional Boost LLM:**
- Secondary LLM configuration for acceleration tasks
- Auth: `LLM_BOOST_API_KEY`
- Endpoint: `LLM_BOOST_BASE_URL`
- Model: `LLM_BOOST_MODEL_NAME`
- All three must be set together or omitted entirely

### Zep Cloud (Knowledge Graph)

Cloud-hosted knowledge graph storage, vector search, and memory management.

- **SDK/Client:** `zep-cloud` == 3.13.0 (pinned)
- **Auth:** API key via `ZEP_API_KEY` env var
- **Client initialization:** `Zep(api_key=...)` in multiple service files

**Services that use Zep directly:**
- `backend/app/services/graph_builder.py` - Creates standalone graphs, adds episodes (text chunks) as `EpisodeData`, reads nodes/edges
- `backend/app/services/zep_tools.py` - Search tools for report agent: `InsightForge` (hybrid multi-dimensional retrieval), `PanoramaSearch` (broad search including expired content), `QuickSearch` (fast retrieval)
- `backend/app/services/zep_entity_reader.py` - Reads entity/node details from graphs
- `backend/app/services/zep_graph_memory_updater.py` - Writes simulation agent activities back to graph as episodes
- `backend/app/utils/zep_paging.py` - Pagination helper for node/edge listing with exponential backoff retry

**Zep API operations used:**
- `client.graph.add()` - Create new graph
- `client.graph.episode.add()` - Add text episodes to graph
- `client.graph.node.get_by_graph_id()` - List nodes (paginated with UUID cursor)
- `client.graph.edge.get_by_graph_id()` - List edges (paginated with UUID cursor)
- `client.graph.search()` - Semantic search over graph
- Graph node/edge read operations with retry logic (handles `InternalServerError`)

**Pagination:**
- Custom pagination in `backend/app/utils/zep_paging.py`
- Max 2000 nodes per graph, page size 100
- Exponential backoff retry (3 attempts, 2s initial delay)

### OASIS / CAMEL-AI (Multi-Agent Simulation)

Social media simulation framework that runs as a subprocess.

- **Packages:** `camel-oasis` == 0.2.5, `camel-ai` == 0.2.78
- **Runner:** `backend/app/services/simulation_runner.py` (`SimulationRunner` class)
- **Execution model:** Runs as a Python subprocess (not in-process), managed via `subprocess` module
- **Platforms supported:** Twitter and Reddit (configurable actions in `backend/app/config.py`)

**IPC mechanism:** File-system based inter-process communication
- Implementation: `backend/app/services/simulation_ipc.py`
- Commands written as JSON files to `{simulation_dir}/ipc_commands/`
- Responses read from `{simulation_dir}/ipc_responses/`
- Polling-based with configurable timeout (default 60s) and interval (0.5s)
- Command types: `INTERVIEW` (single agent), `BATCH_INTERVIEW` (multiple agents), `CLOSE_ENV`
- Environment status tracked via `{simulation_dir}/env_status.json`

**Twitter actions:** `CREATE_POST`, `LIKE_POST`, `REPOST`, `FOLLOW`, `DO_NOTHING`, `QUOTE_POST`
**Reddit actions:** `LIKE_POST`, `DISLIKE_POST`, `CREATE_POST`, `CREATE_COMMENT`, `LIKE_COMMENT`, `DISLIKE_COMMENT`, `SEARCH_POSTS`, `SEARCH_USER`, `TREND`, `REFRESH`, `DO_NOTHING`, `FOLLOW`, `MUTE`

## Data Storage

**Databases:**
- None. No SQL or NoSQL database is used.

**File Storage:**
- Local filesystem only
- Upload directory: `backend/app/uploads/` (configurable via `Config.UPLOAD_FOLDER`)
- Max upload size: 50MB (`Config.MAX_CONTENT_LENGTH`)
- Allowed file types: `.pdf`, `.md`, `.txt`, `.markdown`
- Simulation data: `backend/app/uploads/simulations/`
- Report data and agent logs: `backend/app/uploads/reports/{reportId}/`
- Project/task metadata: JSON files in `backend/app/uploads/`

**Caching:**
- None. No caching layer is present.

## Authentication & Identity

**Auth Provider:**
- None. The application has no user authentication or authorization.
- API endpoints are open (CORS allows all origins: `"origins": "*"`)
- Flask secret key is hardcoded default: `'mirofish-secret-key'` in `backend/app/config.py`

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- Python `logging` module via custom `backend/app/utils/logger.py`
- Rotating file logs in `backend/logs/` (10MB per file, 5 backups)
- Request/response logging middleware in `backend/app/__init__.py`
- Structured JSONL agent logs per report: `backend/app/uploads/reports/{reportId}/agent_log.jsonl`

**Health Check:**
- `GET /health` endpoint returns `{"status": "ok", "service": "MiroFish Backend"}` (defined in `backend/app/__init__.py`)

## CI/CD & Deployment

**Hosting:**
- Docker container via `docker-compose.yml`
- Image published to GitHub Container Registry: `ghcr.io/666ghj/mirofish:latest`
- Mirror available: `ghcr.nju.edu.cn/666ghj/mirofish:latest`

**CI Pipeline:**
- Not detected in repository (no `.github/workflows/`, no CI config files found)

## Environment Configuration

**Required env vars:**
| Variable | Purpose | Used By |
|----------|---------|---------|
| `LLM_API_KEY` | LLM provider authentication | `backend/app/utils/llm_client.py` |
| `LLM_BASE_URL` | LLM API endpoint URL | `backend/app/utils/llm_client.py` |
| `LLM_MODEL_NAME` | LLM model identifier | `backend/app/utils/llm_client.py` |
| `ZEP_API_KEY` | Zep Cloud authentication | `backend/app/services/graph_builder.py`, `backend/app/services/zep_tools.py`, `backend/app/services/zep_entity_reader.py`, `backend/app/services/zep_graph_memory_updater.py` |

**Optional env vars:**
| Variable | Purpose | Default |
|----------|---------|---------|
| `LLM_BOOST_API_KEY` | Secondary LLM auth | Not set |
| `LLM_BOOST_BASE_URL` | Secondary LLM endpoint | Not set |
| `LLM_BOOST_MODEL_NAME` | Secondary LLM model | Not set |
| `FLASK_HOST` | Backend bind address | `0.0.0.0` |
| `FLASK_PORT` | Backend port | `5001` |
| `FLASK_DEBUG` | Debug mode | `True` |
| `OASIS_DEFAULT_MAX_ROUNDS` | Max simulation rounds | `10` |
| `REPORT_AGENT_MAX_TOOL_CALLS` | Max Zep tool calls per report section | `5` |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | Max ReACT reflection iterations | `2` |
| `REPORT_AGENT_TEMPERATURE` | LLM temperature for reports | `0.5` |
| `VITE_API_BASE_URL` | Frontend API base URL | `http://localhost:5001` |

**Secrets location:**
- `.env` file in project root (git-ignored)
- Template provided: `.env.example`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## API Surface (Internal Flask Endpoints)

Three Flask blueprints registered in `backend/app/__init__.py`:

| Blueprint | Prefix | File |
|-----------|--------|------|
| `graph` | `/api/graph` | `backend/app/api/graph.py` |
| `simulation` | `/api/simulation` | `backend/app/api/simulation.py` |
| `report` | `/api/report` | `backend/app/api/report.py` |

Frontend communicates via Axios (`frontend/src/api/index.js`) with 5-minute timeout and exponential backoff retry. In development, Vite proxies `/api` requests to `http://localhost:5001`.

## Retry & Resilience Patterns

**Backend retry utility:** `backend/app/utils/retry.py`
- `retry_with_backoff` decorator - Exponential backoff with jitter (sync)
- `retry_with_backoff_async` decorator - Async version
- `RetryableAPIClient` class - Wrapper for retryable API calls with batch support
- Default: 3 retries, 1s initial delay, 30s max delay, 2x backoff factor

**Zep pagination retry:** `backend/app/utils/zep_paging.py`
- Retries on `ConnectionError`, `TimeoutError`, `OSError`, `InternalServerError`
- 3 attempts with 2s initial delay, doubling each retry

**Frontend retry:** `frontend/src/api/index.js`
- `requestWithRetry()` function: 3 retries with exponential backoff (1s, 2s, 4s)

---

*Integration audit: 2026-03-24*
