from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from app.github_client import GitHubClient
from app.file_filter import filter_files
from app.prompt_builder import build_prompt
from app.nebius_client import call_llm

load_dotenv()

app = FastAPI()


# ──────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    github_url: str

class SummarizeResponse(BaseModel):
    summary: str
    technologies: list[str]
    structure: str

# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    # validate its a github URL
    if "github.com" not in request.github_url:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Only GitHub URLs are supported"})
    
    # Step 3: Fetch repo tree
    try:
        client = GitHubClient(request.github_url)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})

    try:
        tree = await client.get_repo_tree()
    except ValueError as e:
        return JSONResponse(status_code=404, content={"status": "error", "message": str(e)})
    except TimeoutError as e:
        return JSONResponse(status_code=504, content={"status": "error", "message": str(e)})
    except RuntimeError as e:
        return JSONResponse(status_code=502, content={"status": "error", "message": str(e)})

    # Step 4: Filter to important files only
    filtered = filter_files(tree)
    if not filtered:
        return JSONResponse(status_code=422, content={"status": "error", "message": "No relevant files found in this repository"})

    # Step 5: Get file contents
    contents = await client.get_files_content(filtered)

    # Step 6: Build LLM prompt
    prompt = build_prompt(request.github_url, contents)

    # Step 7: Call Nebius LLM
    try:
        llm_result = await call_llm(prompt)
    except ValueError as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    except RuntimeError as e:
        return JSONResponse(status_code=502, content={"status": "error", "message": str(e)})

    return SummarizeResponse(
        summary=llm_result.get("summary", ""),
        technologies=llm_result.get("technologies", []),
        structure=llm_result.get("structure", ""),
    )