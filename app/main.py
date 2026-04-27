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


# Suppress verbose logging from external libraries
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("🔍 Loading documents...")
    docs = load_documents("data/sample_docs")
    if not docs:
        logger.warning("No documents found.")
        df = generate_output([])
        print(df.to_string(index=False))
        return df
    
    logger.info(f"✓ Loaded {len(docs)} documents")

    extracted_records = []

    for i, doc in enumerate(docs, 1):
        try:
            logger.info(f"📄 Processing [{i}/{len(docs)}] {doc.source_file}...")
            classification = classify_document(doc.content)
            doc.type = classification.get("document_type", "UNKNOWN")

            extracted = extract_data(doc.content)
            extracted.source_file = doc.source_file
            extracted.document_type = doc.type

            if extracted.event_type.value:
                extracted_records.append(extracted)
        except Exception as exc:
            logger.error(f"  ✗ Failed to process {doc.source_file}")

    if not extracted_records:
        logger.warning("No extractable events found.")
        df = generate_output([])
        print(df.to_string(index=False))
        return df

    logger.info(f"✓ Extracted {len(extracted_records)} events from documents")
    
    logger.info("📊 Grouping events by date...")
    grouped = group_by_date(extracted_records)

    events = []
    for key, records in grouped.items():
        try:
            event = build_event(records)
            event = validate_event(event)
            events.append(event)
        except Exception as exc:
            logger.error(f"  ✗ Failed to build event for group {key}")

    logger.info(f"✓ Built {len(events)} event groups")
    
    logger.info("⏱️  Building timeline...")
    timeline = build_timeline(events)

    logger.info("📝 Generating output...")
    df = generate_output(timeline)
    
    logger.info("✅ Pipeline complete!")
    print("\n" + "="*80)
    print(df.to_string(index=False))
    print("="*80 + "\n")
    
    return df


if __name__ == "__main__":
    main()
