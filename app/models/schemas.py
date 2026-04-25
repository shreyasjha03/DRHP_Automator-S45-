from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Document(BaseModel):
    id: str
    type: Optional[str]
    content: str
    source_file: str


class ExtractedField(BaseModel):
    value: Optional[Any] = None
    evidence_text: Optional[str] = None

    @validator("value", pre=True)
    def normalize_value(cls, value):
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned or cleaned.lower() in {"null", "none", "n/a", "unknown"}:
                return None

            numeric = cleaned.replace(",", "")
            if numeric.isdigit():
                try:
                    return int(numeric)
                except ValueError:
                    return cleaned

            return cleaned

        return value


class ExtractedData(BaseModel):
    event_type: ExtractedField = Field(default_factory=ExtractedField)
    date: ExtractedField = Field(default_factory=ExtractedField)
    old_capital: ExtractedField = Field(default_factory=ExtractedField)
    new_capital: ExtractedField = Field(default_factory=ExtractedField)
    old_shares: ExtractedField = Field(default_factory=ExtractedField)
    new_shares: ExtractedField = Field(default_factory=ExtractedField)
    face_value_per_share: ExtractedField = Field(default_factory=ExtractedField)
    source_file: Optional[str] = None
    document_type: Optional[str] = None

    @validator(
        "event_type",
        "date",
        "old_capital",
        "new_capital",
        "old_shares",
        "new_shares",
        "face_value_per_share",
        pre=True,
    )
    def coerce_field(cls, value):
        if value is None:
            return {}
        if isinstance(value, ExtractedField):
            return value
        if isinstance(value, dict):
            return value
        return {"value": value}

    @classmethod
    def from_llm_payload(cls, payload: Optional[Dict[str, Any]], **extra_fields):
        payload = payload or {}
        if not isinstance(payload, dict):
            payload = {}
        return cls(**payload, **extra_fields)


class CapitalChangeEvent(BaseModel):
    date: Optional[str]
    event_type: Optional[str]
    old_capital: Optional[int]
    new_capital: Optional[int]
    old_shares: Optional[int]
    new_shares: Optional[int]
    sources: List[str]
    confidence: str
    missing_fields: List[str]
    conflicts: List[Any]
    notes: List[str] = Field(default_factory=list)
