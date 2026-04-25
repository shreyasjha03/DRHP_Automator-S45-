# Prompts Used

This file captures the prompts and instructions used while building and debugging the assignment solution with coding assistance.

The goal is to be transparent about how the code and dataset were produced.

## 1. Core Engineering Prompt

Used to guide debugging and pipeline hardening:

```text
You are a senior Python engineer working on an AI pipeline.

The project is a DRHP Capital Structure Extraction system.

Current status:

* Project structure is already created
* Gemini LLM client is working
* Environment setup is complete

Your task:

1. Debug and fix any issues in the pipeline
2. Ensure the full pipeline runs end-to-end
3. Improve robustness of extraction and parsing

Focus on:

### 1. LLM Client

* Ensure Gemini response parsing is reliable
* Handle invalid JSON safely
* Add retry or fallback logic

### 2. Extraction Layer

* Validate extracted JSON using Pydantic
* Handle missing/null fields correctly
* Ensure no crashes on bad LLM output

### 3. Event Builder

* Properly group records by (date, event_type)
* Merge multiple documents into one event
* Detect conflicts in values
* Prefer SH7 > PAS3 > others

### 4. Validator

* Assign confidence:

  * high → multiple matching sources
  * medium → single source
  * low → conflicts
* Track missing fields explicitly

### 5. Output

* Ensure final output is a clean pandas DataFrame
* Save CSV to data/outputs/result.csv
* Include:
  Date, Old Capital, New Capital, Sources, Confidence, Notes

### 6. Logging (IMPORTANT)

Add debug logs for:

* classification
* extraction output
* grouping
* final events

### 7. Fix main.py

* Ensure pipeline runs correctly
* No crashes even with bad input
* Print final table clearly

Constraints:

* Do NOT rewrite the whole project
* Modify only necessary parts
* Keep code modular and clean
* Avoid unnecessary abstractions
```

## 2. Dataset Creation Prompt

Used to generate the assignment-aligned sample dataset:

```text
Create a dummy sample dataset consisting of 4 SH-7 documents, with 3 attachment
documents for each SH-7, based on the structure of the provided SH-7 and PAS-3
reference files.

The sample data should represent authorised share capital changes over time for a
single company and should be easy to parse by the pipeline.

Each event should include:
- date
- old authorised capital
- new authorised capital
- old number of shares
- new number of shares
- face value per share

Use realistic filing-style language similar to SH-7, board resolutions, EGM notices,
EGM resolutions, and MOA extracts.
```

## 3. Gemini Verification Prompt

Used to validate LLM connectivity and end-to-end behavior:

```text
Check whether Gemini LLM is working and whether the model is properly working
end to end inside the pipeline.

Verify:
- direct LLM JSON response
- pipeline execution against sample docs
- model configuration problems
- quota or API failures

If Gemini is not usable live, make the pipeline degrade gracefully and state the
exact reason honestly.
```

## 4. Documentation Prompt

Used for final repo packaging:

```text
Create:
- a complete README.md with proper detail
- a prompt log
- a handwritten-style system design explanation

The README should explain the problem, architecture, dataset, setup, run steps,
Gemini status, output, and assignment mapping.
```

## How These Prompts Were Used

- The first prompt drove code hardening and bug fixing.
- The second prompt drove generation of a realistic but clean sample dataset.
- The third prompt was used to verify actual Gemini runtime behavior, not just code structure.
- The fourth prompt was used to package the repo into a submission-ready state.

## Important Note

The final implementation was not accepted blindly from prompts. It was iteratively checked by:

- reading the current codebase
- inspecting runtime failures
- patching minimal targeted fixes
- running the pipeline locally
- validating the resulting CSV output
