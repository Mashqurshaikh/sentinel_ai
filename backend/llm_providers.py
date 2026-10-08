"""
LLM forwarding.

This is the piece that closes the loop the rest of the gateway sets up:
once a prompt is sanitized (and, for high-risk ones, approved), it
actually gets sent to a real external model and the response comes back
through the same UI - instead of making the person copy/paste the
sanitized text into a separate chat window themselves.

Each provider needs its own API key, supplied via environment variable:
    ANTHROPIC_API_KEY   - for Claude
    OPENAI_API_KEY      - for ChatGPT
    GOOGLE_API_KEY       - for Gemini

If a key isn't set, calling that provider raises LLMError with a message
explaining what to set - the caller is expected to surface that to the
user rather than crash, since "no API key configured" is an expected
state for a fresh checkout of this project, not a bug.
"""

import os
import httpx

REQUEST_TIMEOUT = 60.0


class LLMError(Exception):
    pass


async def _call_anthropic(prompt: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set. Add it to your environment to enable live Claude responses.")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)

    if resp.status_code != 200:
        raise LLMError(f"Claude API error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


async def _call_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set. Add it to your environment to enable live ChatGPT responses.")

    headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if resp.status_code != 200:
        raise LLMError(f"OpenAI API error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def _call_gemini(prompt: str, model: str = "gemini-3.6-flash") -> str:
    # Google retired the old generateContent model (e.g. gemini-2.0-flash)
    # and now recommends the Interactions API, which is a single shared
    # endpoint (not one URL per model) that takes the model name in the body.
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise LLMError("GOOGLE_API_KEY is not set. Add it to your environment to enable live Gemini responses.")

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {"x-goog-api-key": api_key, "content-type": "application/json"}
    payload = {"model": model, "input": prompt}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        raise LLMError(f"Gemini API error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    try:
        # Response is a "steps" timeline; the answer lives in the
        # model_output step's text content block.
        for step in data.get("steps", []):
            if step.get("type") == "model_output":
                for block in step.get("content", []):
                    if block.get("type") == "text":
                        return block.get("text", "")
        raise LLMError("Gemini response had no model_output text step.")
    except (KeyError, IndexError):
        raise LLMError("Gemini returned an unexpected response shape.")


PROVIDERS = {
    "claude": _call_anthropic,
    "chatgpt": _call_openai,
    "gemini": _call_gemini,
}

ENV_VAR_BY_PROVIDER = {
    "claude": "ANTHROPIC_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


def provider_status() -> dict:
    """Returns which providers have a key configured, without exposing the
    key itself - the frontend uses this to gray out unavailable options."""
    return {name: bool(os.environ.get(env_var)) for name, env_var in ENV_VAR_BY_PROVIDER.items()}


async def forward_to_llm(prompt: str, provider: str) -> str:
    fn = PROVIDERS.get(provider)
    if not fn:
        raise LLMError(f"Unknown provider '{provider}'. Choose one of: {', '.join(PROVIDERS)}.")
    return await fn(prompt)
