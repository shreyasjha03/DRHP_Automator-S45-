import logging
import os
import sys

if __package__ in {None, ""}:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.loader import load_documents
from app.classification.classifier import classify_document
from app.extraction.extractor import extract_data
from app.processing.event_builder import build_event, group_by_date
from app.processing.validator import validate_event
from app.processing.timeline import build_timeline
from app.output.generator import generate_output


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    docs = load_documents("data/sample_docs")
    if not docs:
        logger.warning("No documents found. Writing empty result set.")
        df = generate_output([])
        print(df.to_string(index=False))
        return df

    extracted_records = []

    for doc in docs:
        try:
            classification = classify_document(doc.content)
            doc.type = classification.get("document_type", "UNKNOWN")

            extracted = extract_data(doc.content)
            extracted.source_file = doc.source_file
            extracted.document_type = doc.type

            if extracted.event_type.value:
                extracted_records.append(extracted)
            else:
                logger.debug("Skipping document without event_type: %s", doc.source_file)
        except Exception as exc:
            logger.exception("Failed to process document %s: %s", doc.source_file, exc)

    if not extracted_records:
        logger.warning("No extractable events found. Writing empty result set.")
        df = generate_output([])
        print(df.to_string(index=False))
        return df

    grouped = group_by_date(extracted_records)

    events = []
    for key, records in grouped.items():
        try:
            logger.debug("Building grouped event for %s", key)
            event = build_event(records)
            event = validate_event(event)
            events.append(event)
        except Exception as exc:
            logger.exception("Failed to build event for group %s: %s", key, exc)

    timeline = build_timeline(events)
    logger.debug(
        "Final events: %s",
        [
            event.model_dump() if hasattr(event, "model_dump") else event.dict()
            for event in timeline
        ],
    )

    df = generate_output(timeline)
    if df.empty:
        print(df.to_string(index=False))
    else:
        print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    main()
