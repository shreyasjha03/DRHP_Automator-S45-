import logging

logger = logging.getLogger(__name__)


def validate_event(event):
    missing = []

    for field in ["date", "event_type", "old_capital", "new_capital"]:
        if getattr(event, field) is None:
            missing.append(field)

    event.missing_fields = missing
    notes = []

    if event.conflicts:
        event.confidence = "low"
        notes.append("Conflicting values detected across source documents.")
    elif len(event.sources) >= 3:
        event.confidence = "high"
        notes.append("Three or more supporting sources agree on the event.")
    elif len(event.sources) == 2:
        event.confidence = "medium"
        notes.append("Two supporting sources confirm the event.")
    else:
        event.confidence = "medium"
        notes.append("Derived from a single source document.")

    if missing:
        notes.append(f"Missing fields: {', '.join(missing)}")

    event.notes = notes
    logger.debug(
        "Validated event: %s",
        event.model_dump() if hasattr(event, "model_dump") else event.dict(),
    )

    return event
