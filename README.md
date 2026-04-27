# DRHP Capital Structure Extraction

This repository contains a modular Python pipeline for extracting authorised share capital changes from Indian corporate filings and generating a DRHP-style capital structure summary.

## What the project does

- Loads document files from `data/sample_docs`
- Classifies each document into `SH7`, `PAS3`, `BOARD_RESOLUTION`, `EGM`, or `MOA`
- Extracts structured authorised capital change data
- Groups related documents into corporate events by date and event type
- Merges values across sources, preserves provenance, and flags conflicts
- Produces a clean CSV at `data/outputs/result.csv`
- Produces detailed event analysis markdown at `data/outputs/CAPITAL_STRUCTURE.md`

## Why this approach

Corporate filings are rarely clean enough for a single document to be the entire truth. A DRHP drafting system should:

- preserve source traceability
- avoid hallucinating unconfirmed values
- identify missing or conflicting evidence
- merge supporting documents into a single event

This pipeline is built around that idea.

## Pipeline architecture

1. **Ingestion** - read markdown/text files from `data/sample_docs`
2. **Classification** - use rule-based logic first, fallback to LLM if needed
3. **Extraction** - use deterministic regex extraction for structured capital records, with Groq fallback for weaker documents
4. **Event building** - group by `(date, event_type)` and merge multiple documents into one event
5. **Validation** - track missing fields, detect conflicts, and assign confidence
6. **Output** - write a structured CSV and a markdown event summary with exact source 

## LLM backend

This project now uses **Groq** as the primary LLM backend.

- The Groq client is configured in `app/utils/llm_client.py`
- The default model is `llama-3.1-8b-instant`
- The code uses deterministic extraction where possible and Groq only as a fallback
- The pipeline is designed to survive unsupported model errors and missing responses

## Output files

- `data/outputs/result.csv` - structured table with columns:
  - `Date`
  - `From (Previous)`
  - `To (Revised)`
  - `Particulars of Change`
  - `Source Documents`
  - `Confidence`
  - `Remarks`
- `data/outputs/CAPITAL_STRUCTURE.md` - event-by-event analysis with source evidence

## Sample dataset

The sample dataset includes 4 authorised share capital change events, each represented by multiple supporting files.

The dummy dataset intentionally includes edge cases such as:

- missing information in one or more supporting documents
- conflicting values across attachments
- preference share introductions
- line-level evidence extraction where possible

## Running the pipeline

Create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your Groq key in `.env`:

```bash
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Run the pipeline:

```bash
python3 app/main.py
```

## Notes on file provenance

The pipeline now attempts to capture line-level provenance for deterministic extraction. The final CSV includes source document names and evidence line numbers when available.

## How to inspect the outputs

- `data/outputs/result.csv` is the structured table
- `data/outputs/CAPITAL_STRUCTURE.md` is the event-based narrative with sources and confidence

## Troubleshooting

If `python3 app/main.py` fails due to missing dependencies, install them inside the virtual environment:

```bash
pip install -r requirements.txt
```

If `GROQ_API_KEY` is not set, the pipeline will still run but Groq fallback extraction will be disabled.

## Final note

During development, the system was moved from Gemini to Groq to avoid quota limits and inconsistent structured output. The current implementation uses Groq for LLM-based extraction and deterministic parsing for documents that already contain explicit authorised capital language.
