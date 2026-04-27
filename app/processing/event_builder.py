import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.models.schemas import CapitalChangeEvent

logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {
    "SH7": 0,
    "PAS3": 1,
}

EVENT_FIELDS = [
    "old_capital",
    "new_capital",
    "old_shares",
    "new_shares",
    "face_value_per_share",
]


def _priority(record) -> int:
    return SOURCE_PRIORITY.get((record.document_type or "").upper(), 99)


def _group_key(record) -> Tuple[str, str]:
    date = record.date.value or "unknown"
    event_type = record.event_type.value or "unknown"
    return str(date), str(event_type)


def group_by_date(records):
    groups = defaultdict(list)
    undated_records = []

    for record in records:
        key = _group_key(record)
        if key[0] == "unknown":
            undated_records.append(record)
        else:
            groups[key].append(record)

    for record in undated_records:
        matched_key = None
        for key, grouped_records in groups.items():
            if key[1] != (record.event_type.value or "unknown"):
                continue

            old_matches = any(
                record.old_capital.value is not None and record.old_capital.value == grouped.old_capital.value
                for grouped in grouped_records
            )
            new_matches = any(
                record.new_capital.value is not None and record.new_capital.value == grouped.new_capital.value
                for grouped in grouped_records
            )

            if old_matches and new_matches:
                matched_key = key
                break

        if matched_key:
            groups[matched_key].append(record)
        else:
            groups[_group_key(record)].append(record)

    logger.debug(
        "Grouping result: %s",
        {str(key): [r.source_file for r in value] for key, value in groups.items()},
    )
    return groups


def _choose_value(records, field_name: str):
    values: Dict[object, List[str]] = defaultdict(list)
    ranked_candidates = []

    for record in records:
        extracted = getattr(record, field_name)
        value = extracted.value
        if value is None:
            continue

        source_name = record.source_file or "unknown"
        values[value].append(source_name)
        ranked_candidates.append((_priority(record), source_name, value))

    if not ranked_candidates:
        return None, []

    ranked_candidates.sort(key=lambda item: (item[0], item[1]))
    chosen_value = ranked_candidates[0][2]

    conflicts = []
    if len(values) > 1:
        conflicts.append(
            {
                "field": field_name,
                "values": [
                    {"value": value, "sources": sorted(source_list)}
                    for value, source_list in sorted(values.items(), key=lambda item: str(item[0]))
                ],
                "chosen_value": chosen_value,
            }
        )

    return chosen_value, conflicts


def _resolve_event_type(records) -> Optional[str]:
    ranked = [
        (_priority(record), record.source_file or "unknown", record.event_type.value)
        for record in records
        if record.event_type.value
    ]
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]))
    return ranked[0][2]


def _document_line_map(record):
    lines_by_source = {}
    for field_name in ["event_type", "date", "old_capital", "new_capital", "old_shares", "new_shares", "face_value_per_share"]:
        extracted = getattr(record, field_name)
        if getattr(extracted, "source_line", None) is not None:
            source = record.source_file or "unknown"
            lines_by_source.setdefault(source, set()).add(extracted.source_line)
    return lines_by_source


def build_event(records: List):
    if not records:
        raise ValueError("build_event requires at least one record")

    ordered_records = sorted(records, key=lambda record: (_priority(record), record.source_file or ""))
    source_lines = {}
    seen_sources = set()
    for record in ordered_records:
        source = record.source_file or "unknown"
        if source not in source_lines:
            source_lines[source] = set()
        for source_name, lines in _document_line_map(record).items():
            source_lines.setdefault(source_name, set()).update(lines)

    sources = []
    for source_name, lines in sorted(source_lines.items()):
        if lines:
            line_list = ", ".join(str(line) for line in sorted(lines))
            sources.append(f"{source_name} (lines {line_list})")
        else:
            sources.append(source_name)

    conflicts = []
    final = {}
    for field_name in EVENT_FIELDS:
        final[field_name], field_conflicts = _choose_value(ordered_records, field_name)
        conflicts.extend(field_conflicts)

    date = next((record.date.value for record in ordered_records if record.date.value), None)
    event_type = _resolve_event_type(ordered_records)

    event = CapitalChangeEvent(
        date=date,
        event_type=event_type,
        old_capital=final["old_capital"],
        new_capital=final["new_capital"],
        old_shares=final["old_shares"],
        new_shares=final["new_shares"],
        face_value_per_share=final.get("face_value_per_share"),
        sources=sources,
        confidence="medium",
        missing_fields=[],
        conflicts=conflicts,
        notes=[],
    )

    logger.debug(
        "Built event: %s",
        event.model_dump() if hasattr(event, "model_dump") else event.dict(),
    )
    return event
