# Codebase Concerns

**Analysis Date:** 2026-03-24

## Tech Debt

### Critical

**Hardcoded Flask SECRET_KEY:**
- Issue: The Flask `SECRET_KEY` defaults to `'mirofish-secret-key'` when no environment variable is set. This is a static, predictable secret used for session signing.
- Files: `backend/app/config.py:24`
- Impact: Session forgery, cookie tampering. Any attacker who knows this default can forge signed cookies.
- Fix approach: Remove the default value. Require `SECRET_KEY` via environment variable and fail on startup if missing. Add it to `Config.validate()`.

**Stack traces exposed in API responses:**
- Issue: Every error handler returns `traceback.format_exc()` in the JSON response body. This leaks internal file paths, library versions, and code structure to clients.
- Files: `backend/app/api/graph.py:253`, `backend/app/api/graph.py:523`, `backend/app/api/report.py:194`, `backend/app/api/report.py:310`, `backend/app/api/report.py:389`, `backend/app/api/simulation.py` (30+ occurrences across the file)
- Impact: Information disclosure vulnerability. Attackers gain knowledge of internal architecture, dependency versions, and file paths.
- Fix approach: Return tracebacks only when `Config.DEBUG` is `True`. In production, return generic error messages and log tracebacks server-side only.

**CORS allows all origins:**
- Issue: `CORS(app, resources={r"/api/*": {"origins": "*"}})` permits any origin to make API requests.
- Files: `backend/app/__init__.py:43`
- Impact: Any website can make cross-origin requests to the API, enabling CSRF-like attacks and unauthorized access from malicious frontends.
- Fix approach: Restrict origins to the frontend URL (e.g., `http://localhost:3000` in development, the production domain in production). Make origins configurable via environment variable.

### High

**No authentication or authorization on any API endpoint:**
- Issue: All API endpoints are publicly accessible with no authentication. Anyone with network access can create/delete projects, run simulations, generate reports, and access all data.
- Files: All files in `backend/app/api/` (graph.py, simulation.py, report.py)
- Impact: Complete unauthorized access to all functionality. Data exfiltration, deletion, and resource abuse (LLM API costs).
- Fix approach: Implement API key authentication at minimum. Add a middleware or decorator that validates an API token from the `Authorization` header. For multi-user scenarios, add proper user/session management.

**No rate limiting on API endpoints:**
- Issue: No rate limiting exists on any endpoint, including the LLM-calling endpoints that incur real costs.
- Files: All files in `backend/app/api/`
- Impact: API abuse, denial of service, and runaway LLM API costs. A single client can exhaust LLM quotas or Zep API limits.
- Fix approach: Add Flask-Limiter or similar rate limiting middleware. Apply stricter limits to resource-intensive endpoints (ontology generation, graph building, report generation).

**Task state stored only in memory (TaskManager singleton):**
- Issue: `TaskManager` stores all task state in an in-memory dictionary. Server restarts lose all task tracking data. Running background tasks become orphaned with no status tracking.
- Files: `backend/app/models/task.py:54-71`
- Impact: After server restart, clients polling for task status get 404s. No way to recover or track in-progress tasks. Tasks accumulate in memory without cleanup (cleanup_old_tasks is defined but never called automatically).
- Fix approach: Persist task state to disk (JSON files in uploads directory, similar to how projects are stored). Add periodic cleanup via a background thread or signal handler.

**Temporary file leak in report download:**
- Issue: `tempfile.NamedTemporaryFile(delete=False)` creates a temporary file that is never cleaned up.
- Files: `backend/app/api/report.py:413-416`
- Impact: Disk space leak. Each download when the markdown file is missing creates a permanent orphan temp file.
- Fix approach: Use `@after_this_request` to clean up the temp file after sending, or use `send_file` with a BytesIO buffer instead.

### Medium

**Simulation process management uses class-level mutable state:**
- Issue: `SimulationRunner` stores processes, threads, file handles, and run states in class-level dictionaries (`_run_states`, `_processes`, `_action_queues`, `_monitor_threads`, `_stdout_files`, `_stderr_files`). These are shared across all threads and never bounded.
- Files: `backend/app/services/simulation_runner.py:219-227`
- Impact: Memory leak over time as completed simulations accumulate references. No cleanup of file handles for completed simulations. Thread-safety concerns with mutable class-level dictionaries.
- Fix approach: Implement bounded storage with automatic cleanup of completed simulations. Close file handles in a `finally` block. Consider using a proper process manager or task queue.

**File-system-based IPC for simulation communication:**
- Issue: The IPC mechanism between Flask and simulation subprocesses uses file-system polling (writing JSON files to directories and polling for responses).
- Files: `backend/app/services/simulation_ipc.py:1-10`
- Impact: Slow, unreliable, and race-condition prone. File operations are not atomic. Polling adds latency. Stale command/response files may accumulate.
- Fix approach: Use Unix domain sockets, named pipes, or a message queue (Redis, ZeroMQ) for reliable IPC. As a quick fix, ensure atomic file writes (write to temp file, then rename).

**Dockerfile runs in development mode:**
- Issue: The Docker CMD runs `npm run dev` which starts both frontend (Vite dev server) and backend in development mode.
- Files: `Dockerfile:29`
- Impact: Development mode in production: debug logging, hot reload overhead, unoptimized frontend, Flask debug mode enabled. Performance and security implications.
- Fix approach: Create a production Dockerfile that builds the frontend with `npm run build`, serves static files via nginx or similar, and runs Flask with gunicorn/waitress in production mode.

**Request body logging in middleware:**
- Issue: The `before_request` middleware logs the full JSON request body at DEBUG level. This can log sensitive data (API keys, user content).
- Files: `backend/app/__init__.py:56-57`
- Impact: Sensitive data in log files. If log files are exposed or collected, user data leaks.
- Fix approach: Redact or omit request body logging, or implement a sanitizer that strips sensitive fields before logging.

**LLM client has no retry logic for API calls:**
- Issue: `LLMClient.chat()` and `chat_json()` make single API calls with no retry on transient failures. While a `retry.py` utility exists, it is not used by the LLM client.
- Files: `backend/app/utils/llm_client.py:53-70`, `backend/app/utils/retry.py` (exists but unused by LLMClient)
- Impact: Transient API failures (rate limits, timeouts, 5xx errors) cause immediate task failure instead of retrying.
- Fix approach: Apply the `@retry_with_backoff` decorator to `LLMClient.chat()` and `chat_json()` methods, targeting transient exceptions (timeout, rate limit, server errors).

## Known Bugs

**Unclosed `<think>` tag handling may eat valid content:**
- Symptoms: The regex `r'<think>[\s\S]*'` strips everything from an unclosed `<think>` tag to the end of the response. If the model outputs `<think>` as part of valid content (not as a reasoning tag), all subsequent content is lost.
- Files: `backend/app/utils/llm_client.py:69`, `backend/app/utils/llm_client.py:141`
- Trigger: Models that use `<think>` in their output for reasons other than CoT reasoning.
- Workaround: Current implementation handles the common case correctly for known thinking models.

## Security Considerations

**No input validation on project/simulation IDs:**
- Risk: Route parameters like `project_id`, `simulation_id`, `graph_id`, and `report_id` are passed directly to filesystem operations (constructing paths via `os.path.join`). While `os.path.join` provides some protection, a malicious ID containing `../` could potentially traverse directories.
- Files: `backend/app/models/project.py:113-115` (constructs paths from `project_id`), `backend/app/services/simulation_manager.py:128`, `backend/app/services/simulation_runner.py:207-209`
- Current mitigation: IDs are generated server-side with predictable formats (`proj_`, `sim_`, `report_`). User-supplied IDs only come from URL route parameters.
- Recommendations: Validate that IDs match expected format (regex: `^(proj|sim|report)_[a-f0-9]{12}$`) before using them in filesystem paths. Reject any ID containing path separators.

**Debug mode enabled by default:**
- Risk: `DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'` defaults to `True` when `FLASK_DEBUG` is not set.
- Files: `backend/app/config.py:25`
- Current mitigation: None.
- Recommendations: Default to `False`. Require explicit opt-in for debug mode.

**Uploaded file handling accepts user-provided filenames:**
- Risk: While the code generates safe filenames for storage, the original filename is stored in project metadata and used in responses. Filenames with special characters could cause issues downstream.
- Files: `backend/app/models/project.py:256-259` (generates safe filename), `backend/app/api/graph.py:183-200` (accepts uploads)
- Current mitigation: Files are saved with UUID-based names. Only the original filename is stored for display.
- Recommendations: Sanitize original filenames before storing in metadata. Limit filename length.

## Performance Bottlenecks

**Synchronous LLM calls in request handlers:**
- Problem: Ontology generation (`/ontology/generate`) makes synchronous LLM calls in the request handler thread, blocking the Flask worker for the entire duration.
- Files: `backend/app/api/graph.py:216-221`
- Cause: Unlike graph building and report generation (which use background threads), ontology generation runs synchronously.
- Improvement path: Move ontology generation to a background thread like other long-running operations, returning a task_id for polling.

**Graph entity listing reads all nodes without pagination:**
- Problem: `ZepEntityReader.filter_defined_entities()` fetches all nodes from the graph via `fetch_all_nodes()`, which pages through the entire Zep API result set. For large graphs, this is slow and memory-intensive.
- Files: `backend/app/services/zep_entity_reader.py`, `backend/app/utils/zep_paging.py`
- Cause: No server-side filtering or pagination support in the API layer.
- Improvement path: Add pagination parameters to entity listing endpoints. Implement cursor-based pagination.

**Report search scans filesystem for simulation-to-report mapping:**
- Problem: `_get_report_id_for_simulation()` iterates over all report directories and reads each `meta.json` to find reports matching a simulation ID.
- Files: `backend/app/api/simulation.py:812-868`
- Cause: No index or database for report lookups.
- Improvement path: Maintain a lightweight index file mapping simulation_id to report_id, or use SQLite for metadata.

## Fragile Areas

**SimulationRunner class-level state:**
- Files: `backend/app/services/simulation_runner.py:195-227`
- Why fragile: All state is class-level and mutable. Multiple threads access and modify `_run_states`, `_processes`, `_action_queues` concurrently. No thread lock protects these dictionaries (unlike TaskManager which uses `_task_lock`).
- Safe modification: Always acquire a lock before reading/writing class-level state. Consider converting to instance-based management with explicit locking.
- Test coverage: None.

**Report Agent tool call parsing:**
- Files: `backend/app/services/report_agent.py:1060-1124`
- Why fragile: Uses regex and manual JSON extraction to parse tool calls from LLM free-text responses. Different models format tool calls differently. The parsing must handle thinking tags, markdown fences, and varied JSON structures.
- Safe modification: Test with multiple LLM providers before changing parsing logic. Add unit tests for known response formats.
- Test coverage: None.

**File-based project/simulation persistence:**
- Files: `backend/app/models/project.py:168-174` (JSON file read/write), `backend/app/services/simulation_manager.py`
- Why fragile: Concurrent writes to the same JSON file can cause data corruption. No file locking. No transactional guarantees.
- Safe modification: Use atomic writes (write to temp file, rename). Consider migrating to SQLite.
- Test coverage: None.

## Scaling Limits

**In-memory task state:**
- Current capacity: Unbounded dictionary in a singleton.
- Limit: Memory exhaustion if many tasks accumulate. `cleanup_old_tasks()` exists but is never called automatically.
- Scaling path: Persist to disk or database. Add automatic periodic cleanup.

**Single-process Flask with threading:**
- Current capacity: One Flask process, background tasks via `threading.Thread`.
- Limit: GIL contention. One CPU core maximum for Python threads. Cannot scale horizontally.
- Scaling path: Use Celery or similar task queue for background work. Run Flask behind gunicorn with multiple workers.

**File-system-based data storage:**
- Current capacity: All projects, simulations, and reports stored as JSON files on local filesystem.
- Limit: No concurrent access safety. Performance degrades with thousands of projects (directory listing).
- Scaling path: Migrate to SQLite for metadata, keep large files (documents, logs) on filesystem.

## Dependencies at Risk

**OASIS/CAMEL-AI framework:**
- Risk: Runs as a subprocess. The codebase depends on OASIS being installed and accessible. No version pinning visible in the subprocess invocation.
- Impact: OASIS API changes or installation issues silently break simulation functionality.
- Migration plan: Pin OASIS version in `pyproject.toml`. Add health check for OASIS availability.

**Zep Cloud API:**
- Risk: Hard dependency on Zep Cloud for all graph operations. No local fallback or mock mode.
- Impact: Zep Cloud outage or API changes break graph building, searching, and report generation.
- Migration plan: Abstract Zep behind an interface to allow alternative graph storage backends.

## Missing Critical Features

**No test suite:**
- Problem: Zero test files exist in the project. `pytest` is listed as a dev dependency in `backend/pyproject.toml:39-40` but no tests exist. The only test-like file is `backend/scripts/test_profile_format.py` which is a standalone script, not a pytest test.
- Blocks: Safe refactoring, CI/CD pipeline, regression detection.

**No database:**
- Problem: All persistence is JSON files on the filesystem. No relational database, no SQLite, no proper data store.
- Blocks: Concurrent access, data integrity, efficient querying, horizontal scaling.

**No input sanitization/validation layer:**
- Problem: Request data is extracted directly from `request.get_json()` and `request.form` with minimal validation. No schema validation library (marshmallow, pydantic, etc.) is used.
- Blocks: Robust API contracts, clear error messages for malformed input, defense against injection attacks.

## Test Coverage Gaps

**Everything:**
- What's not tested: The entire codebase has zero automated tests.
- Files: All files in `backend/app/`
- Risk: Any change can introduce regressions undetected. No CI safety net.
- Priority: Critical. Start with unit tests for `LLMClient._extract_json()`, `TextProcessor.split_text()`, `FileParser.extract_text()`, and API endpoint integration tests.

## TODO/FIXME Comments

**Single TODO found:**
- Files: `frontend/src/views/Process.vue:484`
- Content: `// TODO: enter environment setup step` (translated from Chinese)
- Impact: Low. Appears to be a navigation placeholder.

---

*Concerns audit: 2026-03-24*
