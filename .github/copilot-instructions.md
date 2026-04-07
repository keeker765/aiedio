# Copilot Instructions for Aiedio

## What is this project?

Aiedio is an AI-powered video generation pipeline. Trending topics are crawled from the web, fed to LLMs to generate storyboards/scripts, then assembled into video via multi-modal AI models. The system has four isolated modules owned by different team members (enforced via CODEOWNERS).

## Architecture & Data Flow

```
Client (vanilla HTML/JS)
  │  HTTP REST (port 8000)
  ▼
Backend (FastAPI + Uvicorn)
  │  Direct Python import
  ▼
Core Engine (ZhipuAI GLM, LangChain, MoviePy)
  │  Direct Python import
  ▼
Crawler (BeautifulSoup, Playwright → hot_trends.json)
```

- **Backend → Core Engine**: `from core_engine.src.asset_builder import AI_Engine`
- **Core Engine → Crawler**: `from github_spider import fetch_github_hot` (with `sys.path` manipulation)
- **Client → Backend**: Fetch API to `http://localhost:8000/`
- All cross-module calls are currently synchronous direct imports (no message queues yet).

## Module Layout

Each Python module follows this structure:

```
module_name/
├── requirements.txt    # module-specific dependencies
├── src/
│   ├── __init__.py
│   └── *.py            # source files
├── tests/
│   └── __init__.py
└── output/             # (core_engine only) generated artifacts
```

## Running the Project

> ⚠️ **All commands must be run from the project root** (`aiedio/`). Cross-module imports (`from core_engine.src...`, `from backend.src...`) and hardcoded relative paths (`crawler/src/hot_trends.json`) break if you `cd` into a subdirectory first.

### Backend
```bash
# From project root:
pip install -r backend/requirements.txt
python -m uvicorn backend.src.main:app --reload
# Serves on http://localhost:8000
# GET /ui serves client/index.html
# GET /ai-test calls AI_Engine.generate() for a quick smoke test
```

### Core Engine (standalone storyboard generation)
```bash
# From project root:
pip install -r core_engine/requirements.txt
python core_engine/src/story_prompt.py [--lang zh|en]
# Outputs to core_engine/output/storyboards.json and storyboards.md
```

### Crawler (standalone)
```bash
# From project root:
pip install -r crawler/requirements.txt
python crawler/src/crawler.py
# Outputs to crawler/src/hot_trends.json
```

No build step exists for the client yet — `client/index.html` is served directly by the backend's `/ui` endpoint. `client/src/` is currently empty.

## Key Conventions

### Directory Ownership (strict boundary)
Each directory is owned by a specific team member via `.github/CODEOWNERS`. Never modify files outside the module you're working on without coordination. The boundaries are:
- `client/` — frontend team
- `backend/` — backend engineer
- `core_engine/` — architecture lead
- `crawler/` — crawler engineer

### API Keys & Secrets
Two separate API keys are used — never hardcode either:
```bash
$env:ZHIPU_API_KEY      = "..."   # asset_builder.py → ZhipuAI GLM-4-Flash
$env:OPENROUTER_API_KEY = "..."   # story_prompt.py  → OpenRouter free LLM
```
Both modules return a `[Placeholder]` string (not an error) when the key is missing, so the system degrades gracefully.

### Python Style
- snake_case for functions: `fetch_github_hot()`, `build_story_prompt()`
- Underscore-prefix for module-level private constants: `_API_KEY`, `_ROOT`
- Static methods for stateless utilities: `AI_Engine.generate()`
- Guard CLI entry points: `if __name__ == "__main__"`
- Pydantic `BaseModel` for FastAPI request/response schemas

### API Response Format
Backend returns consistent JSON:
```json
{"success": true, "data": {...}, "message": "..."}
```

### Documentation Language
- Code (names, comments): English
- Project docs (`docs/`): Chinese
- Some CLI tools support `--lang en|zh` for bilingual output

### Crawler Behavior
- `crawler.py` tries **Zhihu first**, falls back to GitHub if Zhihu returns nothing
- Each spider returns the same schema (top 5 items):
```json
[{"platform": "github|zhihu", "title": "...", "hot_value": "..."}]
```
- Output is written to `crawler/src/hot_trends.json` (path is hardcoded; must run from project root)

### Core Engine Storyboard Format
```json
{
  "trend": {"platform": "...", "title": "..."},
  "storyboard": {
    "scenes": [
      {"scene_id": 1, "visual": "...", "narration": "...", "style": "..."}
    ]
  }
}
```
