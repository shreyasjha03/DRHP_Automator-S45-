import logging
import re
from typing import Any, Dict, Optional

from app.utils.llm_client import call_llm
from app.extraction.prompts import EXTRACTION_PROMPT
from app.models.schemas import ExtractedData

logger = logging.getLogger(__name__)

DATE_PATTERNS = [
    r"meeting of the members of the company was held on\s*(\d{2}/\d{2}/\d{4})",
    r"date of egm:\s*(\d{2}/\d{2}/\d{4})",
    r"meeting date:\s*(\d{2}/\d{2}/\d{4})",
    r"date of filing basis:\s*(\d{2}/\d{2}/\d{4})",
    r"approved by the members on\s*(\d{2}/\d{2}/\d{4})",
    r"effective date of amendment:\s*(\d{2}/\d{2}/\d{4})",
]


def _find_match(text: str, patterns) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def _extract_authorised_capital_change(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    if "authorised share capital" not in lowered and "authorized share capital" not in lowered:
        return {}

    result: Dict[str, Any] = {
        "event_type": {
            "value": "authorised_capital_increase",
            "evidence_text": "authorised share capital",
        }
    }

    date = _find_match(text, DATE_PATTERNS)
    if date:
        result["date"] = {"value": date, "evidence_text": date}

    from_to_match = re.search(
        r"from\s+rs\.?\s*([\d,]+).*?divided into\s*([\d,]+)\s*equity shares.*?to\s+rs\.?\s*([\d,]+).*?divided into\s*([\d,]+)\s*equity shares",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if from_to_match:
        old_capital, old_shares, new_capital, new_shares = from_to_match.groups()
        result["old_capital"] = {"value": old_capital, "evidence_text": old_capital}
        result["old_shares"] = {"value": old_shares, "evidence_text": old_shares}
        result["new_capital"] = {"value": new_capital, "evidence_text": new_capital}
        result["new_shares"] = {"value": new_shares, "evidence_text": new_shares}

    existing_capital_match = re.search(r"existing authorised capital:\s*rs\.?\s*([\d,]+)", text, flags=re.IGNORECASE)
    existing_shares_match = re.search(r"existing number of equity shares:\s*([\d,]+)", text, flags=re.IGNORECASE)
    revised_capital_match = re.search(r"revised authorised capital:\s*rs\.?\s*([\d,]+)", text, flags=re.IGNORECASE)
    revised_shares_match = re.search(r"revised number of equity shares:\s*([\d,]+)", text, flags=re.IGNORECASE)

    if existing_capital_match:
        value = existing_capital_match.group(1)
        result.setdefault("old_capital", {"value": value, "evidence_text": value})
    if existing_shares_match:
        value = existing_shares_match.group(1)
        result.setdefault("old_shares", {"value": value, "evidence_text": value})
    if revised_capital_match:
        value = revised_capital_match.group(1)
        result.setdefault("new_capital", {"value": value, "evidence_text": value})
    if revised_shares_match:
        value = revised_shares_match.group(1)
        result.setdefault("new_shares", {"value": value, "evidence_text": value})

    revised_match = re.search(
        r"authorised share capital of the company is rs\.?\s*([\d,]+)\s*divided into\s*([\d,]+)\s*equity shares of rs\.?\s*(\d+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if revised_match:
        new_capital, new_shares, face_value = revised_match.groups()
        result.setdefault("new_capital", {"value": new_capital, "evidence_text": new_capital})
        result.setdefault("new_shares", {"value": new_shares, "evidence_text": new_shares})
        result["face_value_per_share"] = {"value": face_value, "evidence_text": face_value}

    face_value_match = re.search(
        r"face value per equity share:\s*rs\.?\s*(\d+)|nominal amount per equity share:\s*rs\.?\s*(\d+)",
        text,
        flags=re.IGNORECASE,
    )
    if face_value_match:
        face_value = next(group for group in face_value_match.groups() if group)
        result["face_value_per_share"] = {"value": face_value, "evidence_text": face_value}

    return result

def extract_data(text: str):
    heuristic_result = _extract_authorised_capital_change(text)
    if heuristic_result.get("event_type") and (
        heuristic_result.get("new_capital") or heuristic_result.get("old_capital")
    ):
        logger.debug("Using deterministic extraction for structured capital-change document.")
        extracted = ExtractedData.from_llm_payload(heuristic_result)
        dump = extracted.model_dump() if hasattr(extracted, "model_dump") else extracted.dict()
        logger.debug("Extraction output: %s", dump)
        return extracted

    prompt = EXTRACTION_PROMPT.replace("{{document_text}}", text)
    result = call_llm(prompt)
    if not result:
        result = heuristic_result
        if result:
            logger.debug("Using regex extraction fallback.")

    extracted = ExtractedData.from_llm_payload(result)
    dump = extracted.model_dump() if hasattr(extracted, "model_dump") else extracted.dict()
    logger.debug("Extraction output: %s", dump)
    return extracted
