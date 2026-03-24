# Codebase Structure

**Analysis Date:** 2026-03-24

## Directory Layout

```
MiroFish/
├── backend/                    # Python Flask backend
│   ├── app/                    # Application package
│   │   ├── __init__.py         # Flask app factory (create_app)
│   │   ├── config.py           # Central configuration from env vars
│   │   ├── api/                # Flask blueprints (route handlers)
│   │   │   ├── __init__.py     # Blueprint registration
│   │   │   ├── graph.py        # /api/graph/* routes (20KB)
│   │   │   ├── simulation.py   # /api/simulation/* routes (95KB)
│   │   │   └── report.py       # /api/report/* routes (30KB)
│   │   ├── services/           # Business logic (430KB total)
│   │   │   ├── __init__.py     # Service exports
│   │   │   ├── ontology_generator.py     # LLM-based ontology design (16KB)
│   │   │   ├── graph_builder.py          # Zep graph construction (18KB)
│   │   │   ├── text_processor.py         # Text chunking (2KB)
│   │   │   ├── zep_entity_reader.py      # Read entities from Zep (15KB)
│   │   │   ├── zep_graph_memory_updater.py # Update graph with sim data (22KB)
│   │   │   ├── zep_tools.py              # Zep search tools for ReportAgent (66KB)
│   │   │   ├── oasis_profile_generator.py # Agent profile generation (49KB)
│   │   │   ├── simulation_config_generator.py # LLM-generated sim params (39KB)
│   │   │   ├── simulation_manager.py     # Simulation state management (20KB)
│   │   │   ├── simulation_runner.py      # Subprocess launcher + monitor (69KB)
│   │   │   ├── simulation_ipc.py         # File-based IPC protocol (12KB)
│   │   │   └── report_agent.py           # ReACT report generator (99KB)
│   │   ├── models/             # Data models
│   │   │   ├── __init__.py
│   │   │   ├── project.py      # Project dataclass + ProjectManager (10KB)
│   │   │   └── task.py         # Task dataclass + TaskManager singleton (6KB)
│   │   └── utils/              # Shared utilities
│   │       ├── __init__.py
│   │       ├── llm_client.py   # OpenAI SDK wrapper (5KB)
│   │       ├── file_parser.py  # PDF/MD/TXT text extraction (5KB)
│   │       ├── logger.py       # Logging setup (3KB)
│   │       ├── retry.py        # Exponential backoff decorator (8KB)
│   │       └── zep_paging.py   # Zep API pagination helpers (4KB)
│   ├── scripts/                # Standalone simulation scripts
│   │   ├── run_parallel_simulation.py  # Main: dual-platform sim
│   │   ├── run_twitter_simulation.py   # Twitter-only sim
│   │   ├── run_reddit_simulation.py    # Reddit-only sim
│   │   ├── action_logger.py            # JSONL action logging
│   │   └── test_profile_format.py      # Profile format test
│   ├── uploads/                # Runtime data (gitignored in part)
│   │   ├── projects/           # Per-project dirs with JSON + files
│   │   ├── simulations/        # Per-simulation dirs with configs + logs
│   │   └── reports/            # Per-report dirs with JSON + agent logs
│   ├── logs/                   # Backend log files
│   ├── run.py                  # Backend entry point
│   ├── pyproject.toml          # Python dependencies (uv)
│   └── uv.lock                 # Locked Python dependencies
├── frontend/                   # Vue 3 SPA
│   ├── src/
│   │   ├── main.js             # Vue app bootstrap
│   │   ├── App.vue             # Root component (just <router-view />)
│   │   ├── api/
│   │   │   └── index.js        # Axios instance + retry helper
│   │   ├── router/
│   │   │   └── index.js        # Vue Router routes (6 routes)
│   │   ├── store/
│   │   │   └── pendingUpload.js # Reactive store for upload state
│   │   ├── views/              # Page-level components
│   │   │   ├── Home.vue        # Project list + upload (20KB)
│   │   │   ├── MainView.vue    # Steps 1-2 container (15KB)
│   │   │   ├── Process.vue     # Legacy/unused? (52KB)
│   │   │   ├── SimulationView.vue    # Step 3 config (11KB)
│   │   │   ├── SimulationRunView.vue # Step 3 runner (12KB)
│   │   │   ├── ReportView.vue        # Step 4 display (9KB)
│   │   │   └── InteractionView.vue   # Step 5 interview (9KB)
│   │   ├── components/         # Reusable step components
│   │   │   ├── Step1GraphBuild.vue   # Graph build UI (18KB)
│   │   │   ├── Step2EnvSetup.vue     # Environment setup UI (69KB)
│   │   │   ├── Step3Simulation.vue   # Simulation UI (39KB)
│   │   │   ├── Step4Report.vue       # Report display (145KB)
│   │   │   ├── Step5Interaction.vue  # Interview UI (64KB)
│   │   │   ├── GraphPanel.vue        # D3 graph visualization (40KB)
│   │   │   └── HistoryDatabase.vue   # Project history (34KB)
│   │   └── assets/
│   │       └── logo/           # Logo images
│   ├── public/                 # Static files
│   ├── package.json            # Node dependencies
│   ├── package-lock.json
│   ├── vite.config.js          # Vite config (proxy /api to :5001)
│   └── index.html              # HTML entry
├── static/image/               # README screenshots
├── .github/workflows/          # CI/CD (GitHub Actions)
├── .env.example                # Environment variable template
├── .env                        # Active environment config (gitignored)
├── package.json                # Root: dev scripts (concurrently)
├── docker-compose.yml          # Single-service Docker config
├── Dockerfile                  # Full-stack Docker image
├── CLAUDE.md                   # AI assistant instructions
├── README.md                   # Chinese README
├── README-EN.md                # English README
└── LICENSE                     # AGPL-3.0
```

## Directory Purposes

**`backend/app/api/`:**
- Purpose: HTTP route handlers organized as Flask blueprints
- Contains: Three large Python files, one per domain (graph, simulation, report)
- Key files: `graph.py` (project CRUD + ontology + graph build), `simulation.py` (entity reading, profile gen, sim control, interview), `report.py` (report generation + chat)

**`backend/app/services/`:**
- Purpose: All business logic -- the heaviest directory in the codebase
- Contains: 13 service modules totaling ~430KB
- Key files: `report_agent.py` (99KB, largest file), `simulation_runner.py` (69KB), `zep_tools.py` (66KB), `oasis_profile_generator.py` (49KB)

**`backend/app/models/`:**
- Purpose: Data models with built-in persistence
- Contains: `Project` (JSON file persistence) and `Task` (in-memory persistence)
- Key files: `project.py` (ProjectManager with CRUD), `task.py` (TaskManager singleton)

**`backend/app/utils/`:**
- Purpose: Shared infrastructure utilities
- Contains: LLM client, file parser, logging, retry, Zep pagination
- Key files: `llm_client.py` (OpenAI wrapper with thinking-tag cleanup)

**`backend/scripts/`:**
- Purpose: Standalone Python scripts run as subprocesses for OASIS simulations
- Contains: Simulation runners that use CAMEL-AI/OASIS libraries directly
- Key files: `run_parallel_simulation.py` (main entry point for simulation subprocess)

**`backend/uploads/`:**
- Purpose: All runtime data persistence (acts as the "database")
- Contains: Subdirectories per project, simulation, and report
- Structure: `projects/{id}/project.json`, `simulations/{id}/simulation_state.json`, `reports/{id}/report.json`

**`frontend/src/views/`:**
- Purpose: Page-level Vue components, one per route
- Contains: 7 view files mapping to the 5-step workflow + home
- Key files: `Home.vue` (entry), `MainView.vue` (steps 1-2 container)

**`frontend/src/components/`:**
- Purpose: Step-specific UI components and reusable widgets
- Contains: 7 components, many very large (Step4Report.vue is 145KB)
- Key files: `GraphPanel.vue` (D3 visualization), `Step2EnvSetup.vue` (complex entity/profile configuration)

## Key File Locations

**Entry Points:**
- `backend/run.py`: Backend startup -- validates config, creates Flask app, starts server
- `frontend/src/main.js`: Frontend bootstrap -- mounts Vue app with router
- `backend/scripts/run_parallel_simulation.py`: Simulation subprocess entry

**Configuration:**
- `backend/app/config.py`: Central config class loading from `.env`
- `.env.example`: Template for required environment variables
- `frontend/vite.config.js`: Vite dev server config (port 3000, proxy to 5001)
- `backend/pyproject.toml`: Python dependencies
- `frontend/package.json`: Node dependencies
- `package.json`: Root workspace scripts

**Core Logic:**
- `backend/app/services/report_agent.py`: ReACT-pattern report generation (99KB, largest file)
- `backend/app/services/simulation_runner.py`: Simulation subprocess management (69KB)
- `backend/app/services/zep_tools.py`: Zep Cloud search tool abstractions (66KB)
- `backend/app/services/oasis_profile_generator.py`: LLM-based agent profile creation (49KB)
- `backend/app/services/simulation_config_generator.py`: LLM-generated simulation parameters (39KB)
- `backend/app/utils/llm_client.py`: LLM abstraction layer (5KB)

**API Routes:**
- `backend/app/api/graph.py`: `/api/graph/*` -- project CRUD, file upload, ontology, graph build
- `backend/app/api/simulation.py`: `/api/simulation/*` -- entity reading, profiles, sim control, interview
- `backend/app/api/report.py`: `/api/report/*` -- report generation, status, chat

**Testing:**
- `backend/scripts/test_profile_format.py`: Only test file found -- profile format validation

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `graph_builder.py`, `simulation_runner.py`)
- Vue: `PascalCase.vue` for views and components (e.g., `MainView.vue`, `GraphPanel.vue`)
- JavaScript: `camelCase.js` or `index.js` (e.g., `pendingUpload.js`)

**Directories:**
- All lowercase, no separators (e.g., `services`, `models`, `utils`, `views`, `components`)

**IDs:**
- Projects: `proj_{12-char-hex}` (e.g., `proj_095ec9bcc8a5`)
- Simulations: `sim_{12-char-hex}`
- Reports: `report_{12-char-hex}`
- Tasks: UUID v4

## Where to Add New Code

**New API Endpoint:**
- Add route to existing blueprint in `backend/app/api/{graph|simulation|report}.py`
- Or create new blueprint in `backend/app/api/`, register in `backend/app/api/__init__.py` and `backend/app/__init__.py`

**New Service/Business Logic:**
- Create file in `backend/app/services/`
- Export from `backend/app/services/__init__.py`
- Follow existing pattern: class with `Config` dependency injection, dataclass for data structures

**New Data Model:**
- Add to `backend/app/models/`
- Follow `Project` pattern: dataclass + Manager class with JSON persistence
- Export from `backend/app/models/__init__.py`

**New Utility:**
- Add to `backend/app/utils/`
- Export from `backend/app/utils/__init__.py`

**New Frontend View:**
- Create `.vue` file in `frontend/src/views/`
- Add route in `frontend/src/router/index.js`

**New Frontend Component:**
- Create `.vue` file in `frontend/src/components/`
- Import directly where needed (no barrel file)

**New Simulation Script:**
- Add to `backend/scripts/`
- Follow `run_parallel_simulation.py` pattern for IPC compatibility

## Special Directories

**`backend/uploads/`:**
- Purpose: All runtime data -- projects, simulations, reports
- Generated: Yes, at runtime
- Committed: Partially (directory structure exists in repo, contents mostly gitignored)
- Docker: Mounted as volume in `docker-compose.yml` for persistence

**`backend/logs/`:**
- Purpose: Application log files
- Generated: Yes, at runtime
- Committed: No (gitignored)

**`backend/.venv/`:**
- Purpose: Python virtual environment managed by `uv`
- Generated: Yes, by `uv sync`
- Committed: No

**`frontend/node_modules/`:**
- Purpose: Node.js dependencies
- Generated: Yes, by `npm install`
- Committed: No

**`static/image/`:**
- Purpose: Screenshots for README documentation
- Generated: No (manually added)
- Committed: Yes

**`.github/workflows/`:**
- Purpose: GitHub Actions CI/CD configuration
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-03-24*
