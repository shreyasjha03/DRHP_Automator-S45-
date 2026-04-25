import logging

from app.utils.llm_client import call_llm
from app.extraction.prompts import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


def classify_document(text: str):
    text_upper = text.upper()

    if "SH-7" in text_upper:
        result = {"document_type": "SH7", "confidence": "high"}
        logger.debug("Classification result: %s", result)
        return result
    if "PAS-3" in text_upper:
        result = {"document_type": "PAS3", "confidence": "high"}
        logger.debug("Classification result: %s", result)
        return result
    if "BOARD OF DIRECTORS" in text_upper:
        result = {"document_type": "BOARD_RESOLUTION", "confidence": "high"}
        logger.debug("Classification result: %s", result)
        return result
    if "EXTRA ORDINARY GENERAL MEETING" in text_upper:
        result = {"document_type": "EGM", "confidence": "high"}
        logger.debug("Classification result: %s", result)
        return result
    if "MEMORANDUM OF ASSOCIATION" in text_upper:
        result = {"document_type": "MOA", "confidence": "high"}
        logger.debug("Classification result: %s", result)
        return result

    result = call_llm(CLASSIFICATION_PROMPT.replace("{{document_text}}", text))
    if not isinstance(result, dict):
        result = {}

    normalized = {
        "document_type": result.get("document_type", "UNKNOWN"),
        "confidence": result.get("confidence", "low"),
    }
    logger.debug("Classification result: %s", normalized)
    return normalized
