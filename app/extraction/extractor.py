import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from app.utils.llm_client import call_llm
from app.extraction.prompts import EXTRACTION_PROMPT
from app.models.schemas import ExtractedData

logger = logging.getLogger(__name__)

DATE_PATTERNS = [
    r"meeting of the members of the company was held on\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of board meeting:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of egm:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of agm:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"meeting date:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of meeting:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of filing:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date of incorporation:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"date:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"approved by the members on\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
    r"effective date of amendment:\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})",
]


def _find_match(text: str, patterns) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _line_text(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _field_entry(value: Any, text: str, span_start: int, span_end: int) -> Dict[str, Any]:
    line = _line_number(text, span_start)
    snippet = _line_text(text, span_start, span_end)
    return {
        "value": value,
        "evidence_text": f"Line {line}: {snippet}",
        "source_line": line,
    }


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
        match = re.search(re.escape(date), text)
        if match:
            result["date"] = _field_entry(date, text, *match.span())
        else:
            result["date"] = {"value": date, "evidence_text": date}

    from_to_match = re.search(
        r"from\s+rs\.?\s*([\d,]+).*?divided into\s*([\d,]+)\s*equity shares.*?to\s+rs\.?\s*([\d,]+).*?divided into\s*([\d,]+)\s*equity shares",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if from_to_match:
        old_capital, old_shares, new_capital, new_shares = from_to_match.groups()
        result["old_capital"] = _field_entry(old_capital, text, *from_to_match.span(1))
        result["old_shares"] = _field_entry(old_shares, text, *from_to_match.span(2))
        result["new_capital"] = _field_entry(new_capital, text, *from_to_match.span(3))
        result["new_shares"] = _field_entry(new_shares, text, *from_to_match.span(4))

    existing_capital_match = re.search(r"existing authorised capital:\s*rs\.?\s*([\d,]+)", text, flags=re.IGNORECASE)
    existing_shares_match = re.search(r"existing number of equity shares:\s*([\d,]+)", text, flags=re.IGNORECASE)
    revised_capital_match = re.search(r"revised authorised capital:\s*rs\.?\s*([\d,]+)", text, flags=re.IGNORECASE)
    revised_shares_match = re.search(r"revised number of equity shares:\s*([\d,]+)", text, flags=re.IGNORECASE)

    if existing_capital_match:
        value = existing_capital_match.group(1)
        result.setdefault("old_capital", _field_entry(value, text, *existing_capital_match.span(1)))
    if existing_shares_match:
        value = existing_shares_match.group(1)
        result.setdefault("old_shares", _field_entry(value, text, *existing_shares_match.span(1)))
    if revised_capital_match:
        value = revised_capital_match.group(1)
        result.setdefault("new_capital", _field_entry(value, text, *revised_capital_match.span(1)))
    if revised_shares_match:
        value = revised_shares_match.group(1)
        result.setdefault("new_shares", _field_entry(value, text, *revised_shares_match.span(1)))

    revised_match = re.search(
        r"authorised share capital of the company is rs\.?\s*([\d,]+)\s*divided into\s*([\d,]+)\s*equity shares of rs\.?\s*(\d+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if revised_match:
        new_capital, new_shares, face_value = revised_match.groups()
        result.setdefault("new_capital", _field_entry(new_capital, text, *revised_match.span(1)))
        result.setdefault("new_shares", _field_entry(new_shares, text, *revised_match.span(2)))
        result["face_value_per_share"] = _field_entry(face_value, text, *revised_match.span(3))

    face_value_match = re.search(
        r"face value per equity share:\s*rs\.?\s*(\d+)|nominal amount per equity share:\s*rs\.?\s*(\d+)",
        text,
        flags=re.IGNORECASE,
    )
    if face_value_match:
        face_value = next(group for group in face_value_match.groups() if group)
        matched_span = face_value_match.span(face_value_match.groups().index(face_value) + 1)
        result["face_value_per_share"] = _field_entry(face_value, text, *matched_span)

    return result

def _normalize_event_type(event_type: str) -> str:
    """Normalize event type to standard values for better grouping."""
    if not event_type:
        return "unknown"
    
    lower = event_type.lower()
    if any(word in lower for word in ["capital", "authorised", "authorized", "share", "increase", "change", "amendment", "incorporation", "resolution", "board", "egm", "agm", "moa", "sh7", "memorandum", "minutes"]):
        return "authorised_capital_change"
    return event_type


def _normalize_date(value: str) -> str:
    """Normalize common date formats to DD/MM/YYYY."""
    if not value or not isinstance(value, str):
        return value
    value = value.strip()
    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def extract_data(text: str):
    heuristic_result = _extract_authorised_capital_change(text)
    if heuristic_result.get("event_type") and (
        heuristic_result.get("new_capital") or heuristic_result.get("old_capital")
    ):
        logger.debug("Using deterministic extraction for structured capital-change document.")
        extracted = ExtractedData.from_llm_payload(heuristic_result)
        if extracted.event_type.value:
            extracted.event_type.value = _normalize_event_type(extracted.event_type.value)
        if extracted.date.value:
            extracted.date.value = _normalize_date(extracted.date.value)
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
    
    if extracted.event_type.value:
        extracted.event_type.value = _normalize_event_type(extracted.event_type.value)
    if extracted.date.value:
        extracted.date.value = _normalize_date(extracted.date.value)
    
    dump = extracted.model_dump() if hasattr(extracted, "model_dump") else extracted.dict()
    logger.debug("Extraction output: %s", dump)
    return extracted
