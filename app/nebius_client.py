import json
import os
import re

import httpx

NEBIUS_API_URL = "https://api.studio.nebius.com/v1/chat/completions"
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"


async def call_llm(prompt: str) -> dict:
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise ValueError("NEBIUS_API_KEY environment variable is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": NEBIUS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(NEBIUS_API_URL, headers=headers, json=body)
    except httpx.TimeoutException:
        raise RuntimeError("Nebius API timed out — the model took too long to respond")
    except httpx.RequestError as e:
        raise RuntimeError(f"Nebius API connection error: {e}")

    if response.status_code != 200:
        raise RuntimeError(f"Nebius API error {response.status_code}: {response.text}")

    raw_text = response.json()["choices"][0]["message"]["content"]

    return _parse_llm_json(raw_text)


def _parse_llm_json(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # LLM sometimes wraps JSON in markdown code blocks — strip them
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")
