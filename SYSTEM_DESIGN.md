# System Design Note

## Objective

Build a system that can read corporate filings and draft an authorised share capital change table for DRHP preparation. The key requirement is document reconciliation and evidence transparency, not just number extraction.

## Problem framing

An authorised capital change is usually captured across multiple documents:

- SH-7 filed with the ROC
- board resolution approving the proposal
- notice of EGM or AGM
- EGM/AGM minutes
- amended MOA

The right design is to treat the task as event reconstruction rather than as single-document extraction.

## Core fields to capture

For each capital change event:

- date
- event type
- old authorised capital
- new authorised capital
- old number of shares
- new number of shares
- face value per share
- source documents used
- confidence score
- notes on missing or conflicting evidence

The final table collapses this into the DRHP-friendly fields, but the pipeline keeps richer source internally.

## Modular pipeline design

The system is organized into layers:

1. ingestion
2. classification
3. deterministic extraction + LLM fallback
4. event grouping
5. conflict resolution and validation
6. output generation

That keeps the code clean and makes failure points easy to isolate.

## LLM design choice

The project now uses **Groq** as the primary LLM integration.

Why Groq?

- more stable structured JSON output in the current environment
- the API is easier to integrate with the current Python SDK
- it is better suited to fallback extraction when deterministic parsing does not apply

The pipeline does not rely on Groq for every document. It first uses deterministic pattern extraction for strongly structured records, then falls back to Groq only when the document is less explicit.

## Extraction strategy

- use rule-based classification for obvious document types
- use regex extraction for strong capital-change language
- fallback to Groq for documents that still need parsing
- normalize values through Pydantic models
- preserve evidence text and line numbers when available

This hybrid approach reduces hallucination and makes the output more defensible.

## Event building logic

Events are built from grouped records, not from individual documents.

Grouping keys:

- `date`
- `event_type`

Merge rules:

- prefer `SH7` values over others
- record conflicting values instead of overwriting silently
- maintain a list of source documents and evidence line numbers

## Confidence scoring

- `high` when three or more supporting documents agree
- `medium` when one or two sources support the event
- `low` when there are conflicts across sources

Missing field detection is explicit and is reflected in the output notes.

## Handling missing or conflicting data

The system is designed to be honest about uncertainty:

- missing fields are allowed and tracked explicitly
- if a value cannot be confirmed, the event is still built but marked appropriately
- conflicts are surfaced in notes rather than hidden

This is critical for a DRHP drafting assistant, because the reviewer must know what is verified and what is uncertain.

## Sample dataset design

The sample documents were created to show both normal and edge-case behavior:

- clean SH-7 events with supporting attachments
- missing fields in one or more documents
- conflicting values across attachments
- preference share introduction event

This helps verify that the pipeline is not just extracting numbers, but is also handling real-world document ambiguity.

## Practical behavior

The pipeline now writes two outputs:

- `data/outputs/result.csv` for the structured table
- `data/outputs/CAPITAL_STRUCTURE.md` for event-level narrative and provenance

This makes it easy to inspect both the raw extract and the reasoned summary.
