# System Design Note

## Objective

The assignment asks for a system that can read corporate filings and draft an authorised share capital change table for DRHP preparation. The key requirement is not just extraction accuracy. It is evidentiary honesty. Every row should be traceable to source documents, and uncertainty should be exposed rather than hidden.

## How I Thought About the Problem

I treated the problem as an event-reconstruction task, not a single-document extraction task.

An authorised capital increase usually appears in multiple records:

- a board resolution proposing the increase
- an EGM notice
- the EGM resolution passed by members
- the amended MOA
- the SH-7 filed with ROC

These documents overlap, but they are not identical. Some contain the date but not the final filed value. Some contain the revised capital clause but not the old capital explicitly. Some are more authoritative than others. So the right design is to extract partial facts from each document and merge them into one dated event.

## Information I Wanted the System to Capture

For each authorised share capital change, the important fields are:

- event date
- event type
- old authorised capital
- new authorised capital
- old number of shares
- new number of shares
- face value per share
- source documents used
- confidence level
- notes on missing or conflicting evidence

The final assignment output only requires:

- `Date`
- `Old Capital`
- `New Capital`
- `Sources`
- `Confidence`
- `Notes`

But I kept the richer internal structure so the pipeline can validate and reason properly before collapsing into a flat table.

## Core Design Choice

The central design decision was to separate the system into five layers:

1. ingestion
2. classification
3. extraction
4. event building
5. validation and output

This keeps the code modular and makes failure modes easier to isolate.

## Why I Did Not Rely Only on the LLM

At first glance, it is tempting to let Gemini read every document and return JSON. But this is risky for production-style workflows because:

- model responses are not always valid JSON
- API models change over time
- quota limits can break runs
- structured legal filings often follow highly regular patterns that are better parsed deterministically

So I used a hybrid approach:

- use classification heuristics where obvious
- use deterministic extraction for strongly structured authorised-capital documents
- keep Gemini as a fallback for less structured cases

This makes the system more reliable and easier to explain.

## Event Building Logic

The output row should represent a capital change event, not a document.

So I grouped extracted records by:

- `date`
- `event_type`

Then I merged all documents in the group. When multiple records disagreed, I did not silently overwrite values. Instead:

- conflicts are recorded explicitly
- confidence drops to `low`
- a preferred source is chosen using a simple rule:
  - `SH7 > PAS3 > others`

This is important because a DRHP drafting assistant should not invent certainty where the filings disagree.

## Confidence Philosophy

I wanted confidence to be interpretable, not abstract.

- `high` means multiple documents agree
- `medium` means only one source supports the event
- `low` means there is a conflict across sources

This maps closely to how a human reviewer would think about documentary support.

## Handling Missing Information

Missing values are normal in legal/compliance workflows. One attachment may show only the revised clause. Another may show only the meeting date. So the system should not fail just because a field is absent in one document.

That is why:

- Pydantic models allow nulls
- extraction defaults are safe
- missing fields are collected explicitly
- notes explain what the system could not confirm

This matches the assignment’s requirement that the system should say when it does not know something.

## Sample Dataset Strategy

The assignment required 4 SH-7 documents with 3 attachment documents each.

I used the provided SH-7 and PAS-3 files mainly as structure references, then created a synthetic but realistic timeline for one company:

- `22/03/2018`: `150,000 -> 300,000`
- `15/07/2019`: `300,000 -> 750,000`
- `12/01/2021`: `750,000 -> 1,500,000`
- `30/08/2023`: `1,500,000 -> 3,000,000`

I intentionally made the documents explicit and internally consistent so the pipeline could be evaluated on reconstruction logic rather than OCR noise.

## Gemini Findings

I also checked the live Gemini setup instead of assuming it worked.

What I found:

- the client wiring was present
- the old configured model name was invalid for the SDK/API route
- a supported Gemini route was reachable
- the current API project is quota-limited, so live extraction cannot be relied on consistently

That is exactly the sort of real-world failure a production pipeline has to survive. So I made the system degrade gracefully rather than stop entirely.

## If I Had More Time

The next improvements I would make are:

1. Add unit tests for the extraction and merge rules.
2. Normalize dates into a single output format.
3. Add per-field provenance, not just event-level source aggregation.
4. Add a second event family for share allotments using PAS-3.
5. Separate official filing detection from document-type detection more clearly.

## Final Thought

The most important thing in this assignment is not whether an LLM can extract a number. It is whether the system behaves responsibly when documents overlap, disagree, or fail to parse. I designed the solution so that it can still produce a useful DRHP drafting table while remaining explicit about its evidence and its uncertainty.
