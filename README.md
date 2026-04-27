# DRHP Capital Structure Extraction

A modular pipeline for extracting authorised share capital changes from Indian corporate filings and generating a DRHP-style capital structure table.

The core constraint: **no single document is treated as ground truth — all outputs are traceable and verifiable across sources.**

---

## Problem Overview

A Draft Red Herring Prospectus (DRHP) requires a clear history of how a company's authorised share capital evolved over time. In practice, this information is scattered across multiple documents:

- SH-7 (official filing with ROC)
- Board resolutions
- EGM notices and resolutions
- MOA amendments

Each document contains only partial information. A reliable system must combine these into a single event, preserve source traceability, avoid hallucinating missing values, and flag conflicts explicitly.

---

## What This System Does

The pipeline:

- Loads corporate filing documents from `data/sample_docs`
- Classifies each document (SH7, PAS3, BOARD_RESOLUTION, EGM, MOA)
- Extracts structured capital change data
- Groups related documents into events
- Merges values across sources
- Detects conflicts and missing fields
- Assigns confidence scores
- Generates DRHP-style output

---

## Repository Structure

```
app/
  ingestion/        # document loading
  classification/   # document type detection
  extraction/       # data extraction logic
  processing/       # event building + validation
  output/           # CSV + markdown generation
  models/           # Pydantic schemas
  utils/            # LLM client (Groq)

data/
  sample_docs/      # input dataset
  outputs/          # generated outputs

PROMPTS_USED.md
SYSTEM_DESIGN.md
README.md
requirements.txt
```

---

## Pipeline Flow

1. **Ingestion** — Load `.txt` / `.md` documents from `data/sample_docs`
2. **Classification** — Rule-based classification (keyword matching) with optional LLM fallback
3. **Extraction** — Deterministic parsing (regex) for structured documents; LLM fallback (Groq) for weaker/unstructured documents
4. **Event Building** — Group documents by `(date, event_type)` and merge into a single event
5. **Validation** — Detect missing fields, detect conflicting values, assign confidence score
6. **Output Generation** — Structured CSV (`result.csv`) and event-level markdown summary (`CAPITAL_STRUCTURE.md`)

---

## Sample Dataset

The dataset contains **4 authorised capital change events**, each supported by multiple documents:

- 1 SH-7
- 1 board resolution
- 1 EGM-related document
- 1 additional supporting file (MOA / notice)

The dataset intentionally includes missing values, conflicting values across documents, and formatting variations to ensure the system handles real-world inconsistencies.

---

## Output Files

### `data/outputs/result.csv`

| Column | Description |
|--------|-------------|
| Date | Date of the capital change |
| From (Previous) | Authorised capital before the change |
| To (Revised) | Authorised capital after the change |
| Particulars of Change | Share count and face value details |
| Source Documents | Documents used to derive this event |
| Confidence | HIGH / MEDIUM / LOW |
| Remarks | Conflicts, missing fields, caveats |

**Sample output (Apex Corporation Private Limited):**

| Date | From | To | Confidence | Remarks |
|------|------|----|------------|---------|
| 01/01/2015 | Rs. 0 | Rs. 1,00,000 | HIGH | Three or more sources agree |
| 17/11/2016 | Rs. 1,00,000 | Rs. 2,00,000 | HIGH | Three or more sources agree |
| 15/07/2021 | Rs. 2,00,000 | Rs. 3,00,000 | MEDIUM | Single source only |
| 22/07/2021 | Rs. 2,00,000 | Rs. 3,00,000 | LOW | Conflicting values detected |
| 29/09/2025 | Rs. 3,00,000 | Rs. 110,00,00,000 | LOW | Conflicting values detected |

> Note: Events on 15/07/2021 and 22/07/2021 represent the same capital change reported across documents with a date discrepancy. The system surfaces this as a conflict rather than silently merging or dropping either record.

### `data/outputs/CAPITAL_STRUCTURE.md`

Event-by-event breakdown with full source traceability. For each event:

- old and new authorised capital
- share count and face value
- list of source documents with specific line references
- confidence level with reasoning
- conflicts and missing fields flagged explicitly

**Example entry (Event 2 -- 17/11/2016):**

```
Old Authorised Capital: Rs. 1,00,000
New Authorised Capital: Rs. 2,00,000
Particulars: 10,000 shares @ Rs. 10 each -> 20,000 shares @ Rs. 10 each

Source Documents:
- 2016-11-17_BoardMeeting.md (lines 2, 7, 8, 9, 11, 12)
- 2016-11-17_EGM.md
- 2016-11-17_MOA.md (lines 16112016, 17112016)
- 2016-11-17_SH7.md

Confidence: HIGH
Remarks: Three or more supporting sources agree on the event.
```

---

## LLM Backend

This system uses **Groq** as the LLM backend.

- Model: `llama-3.1-8b-instant`
- Used only when deterministic extraction is insufficient
- The pipeline still runs without it (LLM fallback is optional)

The system was initially built using Gemini but moved to Groq due to quota limitations, inconsistent JSON formatting, and model availability issues. Groq offers faster inference, more stable structured outputs, and simpler integration.

---

## Confidence Logic

| Condition | Confidence |
|-----------|------------|
| Multiple sources agree | HIGH |
| Single source only | MEDIUM |
| Conflicting values | LOW |

Confidence is reflected in both output files and is intended to guide human review. LOW confidence events should always be manually verified before inclusion in a final DRHP.

---

## Design Principles

**Traceability first** — every output links back to its source documents with line-level references where available.

**No hallucination** — missing values are never guessed; they are explicitly marked.

**Event-centric design** — the system reconstructs events, not individual documents.

**Deterministic + LLM hybrid** — use regex/code when structure exists; use LLM only when necessary.

**Explicit conflict handling** — conflicting values are preserved and reflected in confidence scoring, not silently resolved.

---

## Setup & Run

**1. Create environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add API key (optional)**

```
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

**3. Run pipeline**

```bash
python3 app/main.py
```

If the API key is not set, the pipeline still runs with LLM fallback disabled.

---

## Limitations

- Focused only on authorised share capital changes
- Regex extraction assumes reasonably structured documents
- No OCR support for scanned PDFs
- Limited handling of complex financial edge cases

---

## Future Improvements

- Unit tests for extraction and event builder
- Normalize all dates to ISO format
- Improve field-level provenance
- Extend to issued / paid-up capital
- Better handling of noisy or unstructured documents

---

This system was built to reflect how DRHP drafting actually works in practice -- not by trusting a single document, but by reconciling multiple sources into a consistent, traceable financial narrative.
