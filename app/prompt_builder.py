MAX_FILE_CHARS = 8_000  

def build_prompt(repo_url: str, files_content: dict[str, str]) -> str:
    # ── Part 1: Header ──────────────────────────────────────────────────────
    header = f"""You are a senior software engineer analyzing a GitHub repository.
Your job is to read the files below and produce a structured summary.

Repository: {repo_url}

"""

    # ── Part 2: File blocks ─────────────────────────────────────────────────
    file_blocks = ""
    for file_path, content in files_content.items():
        if not content.strip():
            # skip empty files
            continue  

        # Truncate very large files to save context window space
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n... [truncated]"

        file_blocks += f"=== {file_path} ===\n{content}\n\n"

    # ── Part 3: Footer (instructions to the LLM) ────────────────────────────
    footer = """Based on the files above, respond ONLY with valid JSON in this exact format (no extra text, no markdown):
{
  "summary": "2-3 sentence description of what this project does and its purpose",
  "technologies": ["actual programming languages, frameworks, databases, tools, and protocols used — NOT concepts like 'containerization' or 'orchestration'"],
  "structure": "1-2 sentence description of the project layout mentioning key top-level folders and their purpose (e.g. src/, tests/, docs/). Do NOT list individual source files."
}"""

    return header + file_blocks + footer