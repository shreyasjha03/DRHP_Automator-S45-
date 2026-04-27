# System Design Note

## Objective

Create a way to review business filings and produce an authorised share capital change table to assist in drafting DRHPs. While it would be great to have a high level of extraction accuracy for this system, there is another layer of importance: being honest about what you know and don't know. Every single line item needs to be able to be tied back to the source documents. Uncertainty or ambiguity needs to be shown instead of assumed away.


## How I Viewed This as an Event Reconstruction Task

Instead of viewing this as extracting information out of a single document, I viewed this as reconstructing an event based upon information extracted from multiple documents. A company authorises an increase in their issued and outstanding shares over several records including: the board resolution, the EGM notice to members, the EGM resolution adopted by the members, the amended articles of association (MOA), and the SH-7 filed with the ROC.

Each record contains overlapping data, however, no two documents are identical. Many records will include the date(s) associated with the increase in authorised shares, however, none will include the final amount of authorised shares. Some records will include the newly created section of the articles which lists the new authorised amount of shares, however, many records do not provide explicit details regarding the previous authorised amount of shares. Additionally, some records may carry more weight than others.

Therefore, the correct method to implement would be to extract partial facts from each document and create a merged document representing a single event in time. Using a single filing as definitive is incorrect.


## Why I Didn't Just Point an LLM at All My Documents and Ask for JSON Back

While it is attractive to point an LLM at all my documents and then request JSON output, this is also brittle for a number of reasons. API quotas can cause your pipeline to fail partway through. Models and/or routes can change within a given SDK version. Structured legal filings such as SH-7 follow specific patterns that can be easily identified using regex, and thus can be more accurately extracted than with an LLM.

Ultimately, I chose a hybrid solution:

- Use classification heuristics to identify obvious document types
- Use deterministic extraction techniques to extract capital-change language where possible (i.e., where there is a known/standardised structure)
- Use Groq only if necessary (where the document cannot be processed via regex)

This creates a much simpler process for explaining and debugging the system.


## Why Groq

The project began with Gemini. During testing, I ran into a few issues. First, the model name I had set up was not valid for the SDK route I was using. Then, I found out that the API project had hit its quota limit. And to make things more complicated, the JSON output was not consistent across different calls.

Groq was a better fit for this pipeline:

- faster inference
- more stable structured output
- simpler Python SDK integration

The pipeline is set up in a way that makes Groq optional. If you don't have an API key, the system will still work but it will only use deterministic extraction.


## Event Building Logic

The output row represents a capital change event, not a document. So I grouped the extracted records by date and event type, then merged all the documents in each group together.

When multiple records disagreed, I did not silently overwrite values. Instead:

- conflicts are recorded explicitly
- confidence drops to LOW
- a preferred source is chosen using a simple rule: SH7 first, then PAS3, then all others

This is important because a DRHP drafting assistant should not invent certainty where the underlying filings disagree. The reviewer needs to know what is verified and what is not.


## Handling Missing Information

In legal and compliance workflows, it is common to come across missing values. For instance, one attachment might only include the revised capital clause, while another might only show the meeting date. The system should be able to handle this and not crash just because a field is missing from one document.

To handle this:

- Pydantic models allow nulls throughout
- extraction functions return safe defaults
- missing fields are collected explicitly per event
- the output notes explain what the system could not confirm

This decision was made on purpose. If we had filled in the missing information with guesses, the table would look nicer, but it would not be entirely truthful.


## Sample Dataset Design

The dataset covers one company across five capital change events, with each event supported by multiple documents. The documents are designed to include a range of scenarios:

- clean events where all sources agree (HIGH confidence)
- events with a single supporting document (MEDIUM confidence)
- events with date or value conflicts across sources (LOW confidence)

This makes sure the pipeline is tested on its ability to handle problems, not just straightforward situations where the information is easy to extract.


## If I Had More Time

1. Add unit tests for the extraction functions and merge rules
2. Normalize all dates to ISO format before grouping
3. Add per-field provenance rather than just event-level source aggregation
4. Extend the event model to cover share allotments using PAS-3 documents
5. Separate official filing detection from document-type classification more cleanly


## Final Thought

What really matters here is not just about a model being able to extract a number from a document. It is about how the system acts when documents don't match up, contradict each other, or can't be understood. I set up the pipeline so it can still create a useful DRHP drafting table even in those tough situations, and it is clear about what it is based on and where it is unsure.
