# Coding Conventions

**Analysis Date:** 2026-03-24

## Languages

**Backend:** Python 3.11+ (Flask)
**Frontend:** JavaScript (Vue 3 with Vite, no TypeScript)

## Naming Patterns

**Python Files:**
- Use `snake_case.py` for all modules: `graph_builder.py`, `llm_client.py`, `ontology_generator.py`
- Service files named after the domain concept: `report_agent.py`, `simulation_runner.py`, `zep_tools.py`
- Model files are singular nouns: `project.py`, `task.py`

**Python Classes:**
- Use `PascalCase`: `GraphBuilderService`, `OntologyGenerator`, `ProjectManager`, `TaskManager`
- Service classes end with descriptive suffix: `Service`, `Generator`, `Manager`, `Reader`, `Runner`, `Agent`
- Enums use `PascalCase` and extend `str, Enum`: `ProjectStatus`, `TaskStatus`, `SimulationStatus`
- Dataclasses use `PascalCase`: `Project`, `Task`, `GraphInfo`

**Python Functions/Methods:**
- Use `snake_case`: `generate_ontology()`, `build_graph()`, `get_project()`
- Private methods prefixed with underscore: `_validate_and_process()`, `_build_user_message()`, `_ensure_projects_dir()`
- Flask route handlers use descriptive names matching the action: `generate_report()`, `get_graph_data()`, `list_projects()`

**Python Variables:**
- Use `snake_case`: `project_id`, `graph_name`, `task_manager`
- Constants use `UPPER_SNAKE_CASE`: `MAX_TEXT_LENGTH_FOR_LLM`, `ONTOLOGY_SYSTEM_PROMPT`, `LOG_DIR`
- ID prefixes use short names: `proj_`, `sim_`, `task_`

**JavaScript/Vue Files:**
- Vue components use `PascalCase.vue`: `GraphPanel.vue`, `Step1GraphBuild.vue`, `Home.vue`
- JS modules use `camelCase.js`: `pendingUpload.js`, `index.js`
- API modules match backend blueprint names: `graph.js`, `simulation.js`, `report.js`

**JavaScript Functions:**
- Use `camelCase`: `generateOntology()`, `buildGraph()`, `getTaskStatus()`, `requestWithRetry()`
- Event handlers prefixed with `handle`: `handleEnterEnvSetup`

**JavaScript Variables:**
- Use `camelCase`: `projectData`, `simulationId`, `currentPhase`
- Reactive state uses `camelCase`: `simulationRequirement`, `isPending`

## Code Style

**Formatting:**
- No Prettier or ESLint configured for the frontend
- No flake8, pylint, or black configured for the backend
- Indentation: 4 spaces for Python, 2 spaces for Vue/JS (informal convention observed)
- Python follows PEP 8 loosely (no enforced linting)

**Linting:**
- No automated linting tools configured
- Backend uses `# noqa: E402, F401` annotations in `backend/app/api/__init__.py` for import ordering

**String Formatting:**
- Python uses f-strings exclusively: `f"项目不存在: {project_id}"`
- JavaScript uses template literals: `` `/api/graph/data/${graphId}` ``

## Comments and Documentation

**Language:** Comments and docstrings are primarily in Chinese (Simplified). Use Chinese for user-facing messages, docstrings, and inline comments. English is used for:
- Variable names, function names, class names
- Entity type definitions and descriptions (passed to LLM/Zep)
- Log messages to external services

**Python Docstrings:**
- Use triple-quoted docstrings with Chinese descriptions
- Follow Google-style format with `Args:` and `Returns:` sections
- Module-level docstrings describe the module's purpose

```python
def generate(
    self,
    document_texts: List[str],
    simulation_requirement: str,
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成本体定义

    Args:
        document_texts: 文档文本列表
        simulation_requirement: 模拟需求描述
        additional_context: 额外上下文

    Returns:
        本体定义（entity_types, edge_types等）
    """
```

**JavaScript JSDoc:**
- Use `@param` and `@returns` annotations on API functions in `frontend/src/api/`
```javascript
/**
 * 生成本体（上传文档和模拟需求）
 * @param {Object} data - 包含files, simulation_requirement, project_name等
 * @returns {Promise}
 */
```

**Section Dividers:**
- Python API routes use comment blocks to separate sections:
```python
# ============== 项目管理接口 ==============
# ============== 接口1：上传文件并生成本体 ==============
```

## Import Organization

**Python Import Order:**
1. Standard library imports (`os`, `json`, `uuid`, `threading`, `traceback`)
2. Third-party imports (`flask`, `zep_cloud`, `openai`)
3. Local application imports (relative, using `..` notation)

```python
import os
import json
import traceback
import threading
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
```

**Python Import Style:**
- Use relative imports within the `app` package: `from ..config import Config`
- Import specific names, not modules: `from ..utils.logger import get_logger` (not `from ..utils import logger`)
- Type imports use `from typing import Dict, Any, List, Optional`

**JavaScript Import Order:**
1. Third-party libraries (`vue`, `vue-router`, `axios`, `d3`)
2. Local modules (API functions, components, stores)

```javascript
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { createSimulation } from '../api/simulation'
```

**Path Aliases:**
- No path aliases configured. All imports use relative paths (`../api/`, `./index`)

## API Response Format

**All API responses follow a consistent envelope pattern:**

Success response:
```json
{
    "success": true,
    "data": { ... },
    "message": "optional success message"
}
```

Success with list:
```json
{
    "success": true,
    "data": [ ... ],
    "count": 5
}
```

Error response:
```json
{
    "success": false,
    "error": "Human-readable error description (Chinese)",
    "traceback": "Full Python traceback (in 500 errors only)"
}
```

**HTTP Status Codes Used:**
- `200` - Success (all successful operations)
- `400` - Bad request (missing/invalid parameters)
- `404` - Resource not found
- `500` - Server error (config issues, unhandled exceptions)

**Key pattern:** The frontend Axios interceptor in `frontend/src/api/index.js` checks `res.success` and auto-rejects if `false`. Frontend API calls receive the unwrapped response data (not the Axios wrapper).

## Error Handling

**Backend API Route Pattern:**
- Every route handler wraps its body in `try/except Exception`
- Exceptions return `jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})` with HTTP 500
- Validation errors return early with HTTP 400

```python
@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    try:
        # ... validation ...
        if not simulation_requirement:
            return jsonify({"success": False, "error": "请提供模拟需求描述"}), 400
        # ... business logic ...
        return jsonify({"success": True, "data": {...}})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
```

**Backend Service Pattern:**
- Services raise exceptions on failure (no `success` envelope)
- Services validate their own inputs: `if not self.api_key: raise ValueError("ZEP_API_KEY 未配置")`
- LLM client raises `ValueError` for invalid JSON responses

**Frontend Error Handling:**
- Axios interceptor handles network errors and timeout globally in `frontend/src/api/index.js`
- `requestWithRetry()` provides exponential backoff retry (3 attempts default)
- Components use `try/catch` around API calls

**Retry Pattern (Backend):**
- `backend/app/utils/retry.py` provides `@retry_with_backoff` decorator and `RetryableAPIClient` class
- Exponential backoff with jitter
- Used for external API calls (LLM, Zep)

**Retry Pattern (Frontend):**
- `requestWithRetry()` in `frontend/src/api/index.js` with exponential backoff
- Applied to write operations (`generateOntology`, `buildGraph`)

## Logging

**Framework:** Python `logging` module via custom wrapper at `backend/app/utils/logger.py`

**Logger Initialization:**
```python
from ..utils.logger import get_logger
logger = get_logger('mirofish.api')          # In API routes
logger = get_logger('mirofish.report_agent')  # In services
logger = get_logger('mirofish.retry')         # In utilities
```

**Logger Naming Convention:**
- Root: `mirofish`
- API layer: `mirofish.api`, `mirofish.api.report`
- Services: `mirofish.report_agent`, `mirofish.build`
- Utilities: `mirofish.retry`, `mirofish.zep_paging`
- Request middleware: `mirofish.request`

**Log Levels Used:**
- `logger.info()` - Operation start/complete, major state changes
- `logger.debug()` - Request details, parameter values, progress updates
- `logger.warning()` - Retry attempts, pagination limits reached
- `logger.error()` - Failed operations, exception details

**Log Output:**
- Console: INFO+ level, simple format `[HH:MM:SS] LEVEL: message`
- File: DEBUG+ level, detailed format `[YYYY-MM-DD HH:MM:SS] LEVEL [name.func:line] message`
- Log files: `backend/logs/YYYY-MM-DD.log`, rotating at 10MB, 5 backups

**Frontend Logging:**
- Uses `console.log()`, `console.error()`, `console.warn()` directly (no logging framework)

## Async/Background Task Pattern

**Long-running operations use threading with task tracking:**

```python
# 1. Create task
task_manager = TaskManager()
task_id = task_manager.create_task(f"构建图谱: {graph_name}")

# 2. Define task function
def build_task():
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, message="...", progress=5)
        # ... do work ...
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, result={...})
    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=traceback.format_exc())

# 3. Launch thread
thread = threading.Thread(target=build_task, daemon=True)
thread.start()

# 4. Return task_id immediately
return jsonify({"success": True, "data": {"task_id": task_id}})
```

The `TaskManager` at `backend/app/models/task.py` is a thread-safe singleton using `threading.Lock`.

## Data Model Pattern

**Models use Python `dataclasses` (not SQLAlchemy/ORM):**
- Define with `@dataclass`
- Include `to_dict()` method for JSON serialization
- Include `from_dict()` classmethod for deserialization
- Persist as JSON files on disk (not a database)

**Manager classes use `@classmethod` methods:**
- `ProjectManager` at `backend/app/models/project.py` - all methods are `@classmethod`
- `TaskManager` at `backend/app/models/task.py` - singleton pattern, in-memory dict

**Enum pattern:**
```python
class ProjectStatus(str, Enum):
    CREATED = "created"
    ONTOLOGY_GENERATED = "ontology_generated"
    GRAPH_BUILDING = "graph_building"
```

## Vue Component Pattern

**Use Composition API with `<script setup>`:**
```vue
<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  currentPhase: { type: Number, default: 0 },
  projectData: Object,
})
</script>
```

**Component Structure Order:**
1. `<template>` - HTML template
2. `<script setup>` - Component logic
3. `<style>` or `<style scoped>` - CSS styles

**State Management:**
- No Vuex or Pinia. Uses a simple reactive module at `frontend/src/store/pendingUpload.js`
- State shared via `reactive()` objects exported from plain JS modules
- Props drilling from parent views to child components

**CSS:**
- Scoped styles in components (some use global styles in `App.vue`)
- No CSS preprocessor (plain CSS)
- No utility framework (no Tailwind, no Bootstrap)
- Custom CSS with monospace font family: `'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace`
- Black and white minimalist design aesthetic

## Flask Blueprint Pattern

**Blueprints defined in `backend/app/api/__init__.py`:**
```python
graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
```

**Registered with URL prefixes in `backend/app/__init__.py`:**
```python
app.register_blueprint(graph_bp, url_prefix='/api/graph')
app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
app.register_blueprint(report_bp, url_prefix='/api/report')
```

**Route handler files import their blueprint from `__init__.py`:**
```python
from . import graph_bp
```

## Service Initialization Pattern

**Services accept optional config, defaulting to `Config` class:**
```python
class GraphBuilderService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY 未配置")
        self.client = Zep(api_key=self.api_key)
```

**Services are instantiated per-request in route handlers (no dependency injection):**
```python
builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
```

## Type Hints

**Backend uses Python type hints consistently:**
- Function signatures: `def generate(self, document_texts: List[str]) -> Dict[str, Any]:`
- Optional parameters: `Optional[str] = None`
- Uses `typing` module: `Dict`, `Any`, `List`, `Optional`, `Callable`, `Tuple`
- Dataclass fields are typed: `project_id: str`, `ontology: Optional[Dict[str, Any]] = None`

**Frontend has no TypeScript -- no type annotations.**

---

*Convention analysis: 2026-03-24*
