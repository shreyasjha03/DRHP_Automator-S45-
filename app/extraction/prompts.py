CLASSIFICATION_PROMPT = """
Classify into:
SH7, PAS3, BOARD_RESOLUTION, EGM, MOA, UNKNOWN

Return JSON:
{
  "document_type": "...",
  "confidence": "high | medium | low"
}

Document:
{{document_text}}
"""


EXTRACTION_PROMPT = """
Output ONLY JSON.
Do not wrap the JSON in markdown fences.
Use null for missing values.

Extract authorised capital change:

{
  "event_type": {"value": "...", "evidence_text": "..."},
  "date": {"value": "...", "evidence_text": "..."},
  "old_capital": {"value": ..., "evidence_text": "..."},
  "new_capital": {"value": ..., "evidence_text": "..."},
  "old_shares": {"value": ..., "evidence_text": "..."},
  "new_shares": {"value": ..., "evidence_text": "..."},
  "face_value_per_share": {"value": ..., "evidence_text": "..."}
}

If not present:
{
  "event_type": {"value": null}
}

Document:
{{document_text}}
"""
