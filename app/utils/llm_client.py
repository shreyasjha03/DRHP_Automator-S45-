import json
import logging
import os
import time
from json import JSONDecodeError
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - fallback if Groq not installed
    Groq = None

load_dotenv()

logger = logging.getLogger(__name__)
_API_KEY = os.getenv("GROQ_API_KEY")
_DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_MODEL_FALLBACKS = [
    _DEFAULT_MODEL,
    "llama-3.1-8b-instant",
    "llama3-70b-8000-token-preview",
    "llama-3.2-3b-preview",
]

client = Groq(api_key=_API_KEY) if Groq and _API_KEY else None


def _extract_json_candidate(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    if cleaned.startswith("```"):
        parts = [part.strip() for part in cleaned.split("```") if part.strip()]
        for part in parts:
            if part.startswith("json"):
                return part[4:].strip()
            if part.startswith("{") or part.startswith("["):
                return part

    start = min(
        [idx for idx in (cleaned.find("{"), cleaned.find("[")) if idx != -1],
        default=-1,
    )
    if start == -1:
        return cleaned

    open_char = cleaned[start]
    close_char = "}" if open_char == "{" else "]"
    end = cleaned.rfind(close_char)
    if end == -1 or end < start:
        return cleaned[start:]

    return cleaned[start : end + 1]


def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    candidate = _extract_json_candidate(text)
    if not candidate:
        return None

    try:
        parsed = json.loads(candidate)
    except JSONDecodeError:
        repaired = candidate.replace("\n", " ").replace("\t", " ").strip()
        try:
            parsed = json.loads(repaired)
        except JSONDecodeError:
            logger.debug("Failed to parse LLM JSON candidate: %s", candidate)
            return None

    return parsed if isinstance(parsed, dict) else {"data": parsed}


def _call_llm(prompt: str, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def call_llm(prompt: str, retries: int = 2, model: Optional[str] = None) -> Dict[str, Any]:
    if not _API_KEY:
        logger.warning("GROQ_API_KEY is not configured. Returning empty payload.")
        return {}

    if not client:
        logger.warning("Groq SDK is unavailable. Returning empty payload.")
        return {}

    model_candidates = []
    preferred = model or _DEFAULT_MODEL
    for candidate in [preferred, *_MODEL_FALLBACKS]:
        if candidate and candidate not in model_candidates:
            model_candidates.append(candidate)

    last_error: Optional[Exception] = None

    for model_name in model_candidates:
        for attempt in range(retries + 1):
            try:
                text = _call_llm(prompt, model_name)

                payload = _safe_json_loads(text)
                if payload is not None:
                    return payload

                last_error = ValueError("LLM returned invalid JSON")
                logger.warning(
                    "Invalid JSON from Groq model %s on attempt %s/%s",
                    model_name,
                    attempt + 1,
                    retries + 1,
                )
            except Exception as exc:  # pragma: no cover - network/SDK failures
                last_error = exc
                error_text = str(exc)
                logger.warning(
                    "Groq call failed for model %s on attempt %s/%s: %s",
                    model_name,
                    attempt + 1,
                    retries + 1,
                    exc,
                )

                if "404" in error_text or "not found" in error_text.lower():
                    logger.warning("Switching Groq model fallback after unsupported model: %s", model_name)
                    break

            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

    logger.error("Groq call exhausted retries: %s", last_error)
    return {}
