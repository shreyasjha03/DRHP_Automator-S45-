# DRHP Capital Structure Extraction

This repository contains a compact AI pipeline for extracting authorised share capital change events from Indian corporate filings and generating a DRHP-style capital structure draft table.

The project is designed around the S45 take-home assignment requirements:

- ingest SH-7 and related attachment documents
- classify and extract capital-structure changes
- group multiple supporting documents into one event
- preserve source traceability
- surface missing or conflicting fields honestly
- output a clean draft table suitable for downstream DRHP workflows

## What This Repo Includes

- Sample input dataset with 4 SH-7 events and 3 attachments per event in [data/sample_docs](/Users/shreyasjha/Desktop/S45_Assg/data/sample_docs)
- AI pipeline code under [app](/Users/shreyasjha/Desktop/S45_Assg/app)
- Generated output table at [data/outputs/result.csv](/Users/shreyasjha/Desktop/S45_Assg/data/outputs/result.csv)
- Prompt log in [PROMPTS_USED.md](/Users/shreyasjha/Desktop/S45_Assg/PROMPTS_USED.md)
- System design note in [SYSTEM_DESIGN.md](/Users/shreyasjha/Desktop/S45_Assg/SYSTEM_DESIGN.md)

## Problem Framing

An authorised share capital change records how much capital a company is permitted to issue under its constitutional documents. In practice, the change is usually evidenced across multiple documents:

- `SH-7` filed with ROC
- board resolution approving the proposal
- notice of EGM
- EGM resolution
- amended MOA

No single document should be trusted blindly. A DRHP drafting system should reconcile these documents into one event, preserve traceability, and explicitly mark uncertainty instead of guessing.

## Repository Structure

```text
app/
  classification/
  extraction/
  ingestion/
  models/
  output/
  processing/
  utils/
data/
  outputs/
  sample_docs/
PROMPTS_USED.md
SYSTEM_DESIGN.md
README.md
requirements.txt
```

## Sample Dataset

The dummy dataset contains 4 authorised capital increase events for one company:

1. `22/03/2018`: `Rs. 150,000 -> Rs. 300,000`
2. `15/07/2019`: `Rs. 300,000 -> Rs. 750,000`
3. `12/01/2021`: `Rs. 750,000 -> Rs. 1,500,000`
4. `30/08/2023`: `Rs. 1,500,000 -> Rs. 3,000,000`

Each event contains four documents:

- one `SH-7`
- one board meeting / board resolution document
- one EGM-related document
- one additional supporting document such as `EGM`, `MOA`, or `Notice of EGM`

These files were modeled from the structure of the reference SH-7 and PAS-3 files you provided, but rewritten as a clean dummy dataset suitable for repeatable testing.

## Pipeline Overview

The pipeline entrypoint is [app/main.py](/Users/shreyasjha/Desktop/S45_Assg/app/main.py:1).

High-level flow:

1. Load markdown/text documents from `data/sample_docs`
2. Classify each document by type
3. Extract authorised capital change fields
4. Group records into one event per `(date, event_type)`
5. Merge supporting documents with source preference
6. Validate missing fields and conflicts
7. Build a final pandas DataFrame
8. Save CSV to `data/outputs/result.csv`

## Key Design Decisions

### 1. Gemini plus deterministic extraction

The original pipeline relied entirely on Gemini JSON extraction. That is brittle for highly structured corporate documents, especially when:

- the model wraps JSON in markdown
- the response is malformed
- the configured model is unsupported
- the API key is quota-limited

To make the system robust, I kept the Gemini client but added a deterministic extraction path for structured authorised-capital documents. For SH-7, EGM, board resolutions, notices, and MOA extracts that already contain explicit phrases like `from Rs. X to Rs. Y`, the extractor can parse the values directly without spending LLM calls.

This preserves the AI-first architecture while making the assignment runnable and honest under real API constraints.

### 2. Pydantic-first validation

All extracted payloads flow through Pydantic models so missing fields, null values, malformed JSON, and stringified numbers do not crash the pipeline.

### 3. Event merging over document-level extraction

The correct unit of output is not a single document. It is a corporate event supported by multiple documents. The pipeline therefore groups by `(date, event_type)` and merges values across supporting sources.

### 4. Source preference

When values differ, source priority is:

- `SH7`
- `PAS3`
- all other supporting documents

Conflicts are preserved in metadata and confidence is downgraded instead of silently discarded.

### 5. Honest confidence

Confidence reflects evidentiary quality:

- `high`: multiple supporting sources agree
- `medium`: single source available
- `low`: conflict detected

## Robustness Improvements Implemented

### LLM Client

In [app/utils/llm_client.py](/Users/shreyasjha/Desktop/S45_Assg/app/utils/llm_client.py:1):

- safe extraction of JSON from plain text / fenced responses
- retry logic
- fallback model list
- graceful handling of invalid JSON and request failures
- no crash on unsupported model or quota failure

### Extraction Layer

In [app/extraction/extractor.py](/Users/shreyasjha/Desktop/S45_Assg/app/extraction/extractor.py:1):

- deterministic parsing for structured capital-change documents
- regex fallback when Gemini returns nothing
- safe conversion into Pydantic models
- no crash on bad or empty LLM output

### Event Builder

In [app/processing/event_builder.py](/Users/shreyasjha/Desktop/S45_Assg/app/processing/event_builder.py:1):

- grouping by `(date, event_type)`
- merging multiple documents into one event
- conflict recording
- source-priority-based selection
- attachment merging even when a supporting doc lacks a date but matches the dated event on capital values

### Validator

In [app/processing/validator.py](/Users/shreyasjha/Desktop/S45_Assg/app/processing/validator.py:1):

- explicit missing field tracking
- confidence scoring based on support/conflict rules
- readable notes for output

### Output

In [app/output/generator.py](/Users/shreyasjha/Desktop/S45_Assg/app/output/generator.py:1):

- final DataFrame columns are exactly:
  - `Date`
  - `Old Capital`
  - `New Capital`
  - `Sources`
  - `Confidence`
  - `Notes`
- CSV is always saved to `data/outputs/result.csv`

### Logging

The pipeline emits debug logs for:

- document classification
- extraction output
- grouping behavior
- built events
- validated events
- final event list

## Gemini Status

I explicitly checked whether Gemini is working end to end.

Current findings:

- The API key is being read and requests reach the Gemini API.
- The old default model `gemini-1.5-flash-8b` was not valid for the current SDK/API path and returned `404`.
- A supported model route such as `gemini-2.0-flash` is reachable, but the current project key is blocked by quota and returns `429 quota exceeded`.

What this means in practice:

- Gemini client integration is wired correctly.
- The original model configuration was broken and has been patched.
- Live LLM extraction cannot be fully exercised until quota/billing is available.
- The pipeline still runs end to end because structured capital-change documents are now handled deterministically first.

If Gemini quota is restored, the same pipeline can continue using Gemini as a fallback for less structured documents.

## Setup

Create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your Gemini key to `.env`:

```env
GEMINI_API_KEY=your_key_here
```

Optional:

```env
GEMINI_MODEL=gemini-2.0-flash
```

## Run

```bash
.venv/bin/python app/main.py
```

The output CSV will be written to:

- [data/outputs/result.csv](/Users/shreyasjha/Desktop/S45_Assg/data/outputs/result.csv:1)

## Current Output

Current generated output:

```text
      Date  Old Capital  New Capital                                                                                     Sources Confidence                                         Notes
12/01/2021       750000      1500000         2021-01-12_SH7.md, 2021-01-12_BoardMeeting.md, 2021-01-12_EGM.md, 2021-01-12_MOA.md       high Multiple matching sources support this event.
15/07/2019       300000       750000 2019-07-15_SH7.md, 2019-07-15_BoardMeeting.md, 2019-07-15_MOA.md, 2019-07-15_NoticeOfEGM.md       high Multiple matching sources support this event.
22/03/2018       150000       300000 2018-03-22_SH7.md, 2018-03-22_BoardMeeting.md, 2018-03-22_EGM.md, 2018-03-22_NoticeOfEGM.md       high Multiple matching sources support this event.
30/08/2023      1500000      3000000 2023-08-30_SH7.md, 2023-08-30_BoardMeeting.md, 2023-08-30_EGM.md, 2023-08-30_NoticeOfEGM.md       high Multiple matching sources support this event.
```

## How This Maps to the Assignment

### Requirement 1

Understand authorised share capital change and what should be captured.

Covered by:

- the design note in [SYSTEM_DESIGN.md](/Users/shreyasjha/Desktop/S45_Assg/SYSTEM_DESIGN.md)
- the event schema and merger logic
- the final DRHP-style output table

### Requirement 2

Create a dummy dataset of 4 SH-7 documents with 3 attachments each.

Covered by:

- [data/sample_docs](/Users/shreyasjha/Desktop/S45_Assg/data/sample_docs)

### Requirement 3

System should take 4 SH-7 inputs and generate authorised share capital change draft.

Covered by:

- [app/main.py](/Users/shreyasjha/Desktop/S45_Assg/app/main.py:24)
- [data/outputs/result.csv](/Users/shreyasjha/Desktop/S45_Assg/data/outputs/result.csv:1)

### Requirement 4

Track how capital evolved over time.

Covered by:

- sorted final output table with 4 events

## Limitations

- The current deterministic extractor is tuned for authorised capital change documents, not the full universe of Companies Act filings.
- PAS-3 processing is not the primary target of the current sample output because this assignment slice focuses on authorised share capital change.
- Live Gemini extraction is limited today by quota on the configured API project.

## Next Steps

If this were extended beyond the take-home scope, the next improvements would be:

1. Add unit tests for extractor and event-builder rules.
2. Normalize all dates into ISO format before output.
3. Separate document subtype detection from event detection more cleanly.
4. Add per-field provenance rather than event-level source lists only.
5. Expand support for issued / subscribed / paid-up capital events in addition to authorised capital changes.
