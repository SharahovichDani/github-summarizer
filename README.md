# GitHub Repository Summarizer

A FastAPI service that analyzes any public GitHub repository and returns a structured summary using an LLM.

## What it does

Send a GitHub repository URL → get back a JSON summary with:
- `summary` — what the project does and its purpose
- `technologies` — languages, frameworks, and tools used
- `structure` — directory layout and main components

## Setup Instructions

### 1. Clone / unzip the project

```bash
unzip solution.zip
cd program
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure your API key

Set the `NEBIUS_API_KEY` environment variable:

```bash
# Linux / macOS
export NEBIUS_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:NEBIUS_API_KEY="your_api_key_here"
```

Alternatively, you can create a `.env` file (the app loads it automatically):

```bash
cp .env.example .env
# Then edit .env and set your key
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 5. Test the endpoint

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

Expected response:

```json
{
  "summary": "...",
  "technologies": ["Python", "urllib3", "..."],
  "structure": "..."
}
```

### Interactive API docs

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

---

## LLM Model: `meta-llama/Llama-3.3-70B-Instruct`

**Why this model:**

- **Instruction-following** — The `Instruct` variant is fine-tuned specifically to follow user instructions, making it reliable at responding with structured JSON when asked.
- **70B parameters** — Large enough to deeply understand code across multiple files and produce accurate, detailed summaries. Smaller models (e.g. 8B) are less reliable at strict JSON output.
- **Code comprehension** — Llama 3.3 70B performs well on code understanding benchmarks, which is essential for analyzing repositories with multiple source files.
- **Cost efficiency** — At $0.13 input / $0.40 output per million tokens, it is significantly cheaper than larger alternatives (405B costs $1.00/$3.00) while delivering equivalent quality for this task.
- **Availability** — Confirmed available on the Nebius Token Factory API with low latency inference.

---

## File Handling Approach

Processing a GitHub repository for LLM analysis involves two challenges: **too many files** and **irrelevant content**. The approach used here solves both.

### Step 1 — Fetch the file tree

The GitHub Git Trees API (`/repos/{owner}/{repo}/git/trees/{branch}?recursive=1`) returns the full repository structure in a single request, including file paths, types, and sizes — without downloading any content.

### Step 2 — Intelligent filtering (`app/file_filter.py`)

A rule-based filter reduces hundreds of files down to the ~20 most relevant:

| Rule | What it does |
|---|---|
| Skip directories | Only process actual files |
| Skip junk folders | Ignores `tests/`, `docs/`, `node_modules/`, `dist/`, `.github/`, etc. |
| Skip dotfiles | Ignores hidden config files |
| Always include priority files | `README.md`, `package.json`, `pyproject.toml`, `Dockerfile`, `Makefile`, etc. |
| Include source code (dynamic cap: 15-20) | `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.cpp`, etc. Large repos (100+ files) get a higher cap |
| Skip binary/media extensions | Images, fonts, archives, compiled files, lock files |
| Skip oversized files | Files larger than 100KB are excluded |
| Skip changelog/license files | `CHANGELOG.md`, `LICENSE`, `AUTHORS.md`, etc. |
| Cap total files at 30 | Hard limit to protect the LLM context window |

### Step 3 — Download content

Only the filtered files are downloaded via raw GitHub URLs (`raw.githubusercontent.com`). This avoids downloading megabytes of irrelevant content.

### Step 4 — Prompt construction (`app/prompt_builder.py`)

Each file is embedded in the prompt as:
```
=== path/to/file.py ===
[file content]
```

Files longer than 8,000 characters are truncated with `... [truncated]` to prevent context window overflow. The LLM is instructed to respond with JSON only — no extra text.

### Why this approach works

A typical repository has 200-500+ files. Sending everything to an LLM is impossible (context limits) and wasteful (most files are tests, generated code, or assets). By filtering down to 20-30 meaningful files — primarily the entry points, configuration, and core source — the LLM receives exactly the context it needs to produce an accurate summary.
