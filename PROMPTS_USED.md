
```md
# Prompts Used

This file documents the prompts I used while building the DRHP capital structure extraction system.  
These were written over time while understanding the problem, building the pipeline, and debugging issues.


```

explain how authorised share capital works in india, like what exactly changes and what needs to be reported

also what is SH-7 vs PAS-3 im kinda confused between the two

which one actually tells the real capital change?? like source of truth

if i have multiple docs (sh7, egm, board resolution etc) how do i combine them into one final record

also what to do if some values are missing or dont match??

```


```

i want to build a pipeline for this

something like:

* read documents
* classify them
* extract data using LLM
* combine into events
* output table

can you suggest a clean python structure for this? not too overcomplicated but still modular

```

```

help me define pydantic models for this

i need:

* raw document
* extracted fields (with some evidence text maybe?)
* final capital change event

also how to handle null values properly in this case?

```

```

which LLM should i use for structured extraction?

i need:

* good JSON output
* less hallucination
* cheap/free ideally

compare gemini vs groq (llama/mixtral etc)

```
```

im using gemini rn but:

* hitting quota issues
* output format sometimes messy

is groq better for this kind of task??

```



```

ok lets switch to groq

can you help me write a python function to call groq api

i just want:

* input prompt
* output json

also handle cases where output is not clean json (this is happening sometimes)

```
```

groq output sometimes has extra text before/after json

how to safely extract only json part from response??

```



```

write a prompt to extract authorised share capital changes from documents

IMPORTANT:

* output should be STRICT JSON
* dont guess values
* if not present → return null
* include some evidence text also

fields:
date, old capital, new capital, shares etc

```
```

the model is still hallucinating sometimes

can you make the prompt stricter? like explicitly say "only extract if clearly mentioned"

```


```

write a function to classify docs into:
SH7, PAS3, BOARD_RESOLUTION, EGM, MOA

i think rule based should work (keywords etc), fallback to LLM only if unsure

```


```

i have extracted data from multiple docs

how do i merge them into ONE event??

requirements:

* group by date
* combine sources
* handle conflicts
* prefer SH7 values over others

```
```

my grouping logic is kinda wrong rn, its mixing events together

how do i fix grouping so that separate events dont get merged??
maybe use date + something else?

```



```

write a function to validate final event

i need:

* missing fields detection
* confidence score

logic:
high → multiple docs agree
medium → only 1 source
low → conflicts

```
```

improve confidence logic a bit

like if 3+ docs support same value then definitely high confidence

```



```

convert final events into pandas dataframe

columns:
date, old capital, new capital, sources, confidence, notes

save as csv also

```


```

write main.py which runs everything:

* load docs
* classify
* extract
* filter relevant ones
* group + merge
* validate
* sort timeline
* output final table

```

## (Errors Encountered)

```

fix this error:
ModuleNotFoundError: No module named 'dotenv'

```
```

llm output is not valid json sometimes

can you help me safely parse it without crashing??

```
```

my pipeline crashes when some fields are missing

how to handle null values properly in pydantic??

```
```

some extracted values look wrong

is this prompt issue or model issue??
how to reduce hallucination here??

```
```

csv is generating but some columns are empty

not sure if issue is extraction or merging logic

how do i debug this??

```
```

add some logging pls

i want to see:

* classification output
* extracted data
* grouped events
* final results

```


```

can you review my overall design?

mainly:

* is it robust enough
* am i handling missing data properly
* does this look like production level or too hacky

```

## Final Note

```

initially i used gemini for this but ran into quota limits + inconsistent formatting issues

switched to groq later which was faster and more stable for json outputs

a lot of time went into debugging parsing issues and fixing grouping logic

final system is a mix of LLM extraction + deterministic python logic for merging and validation

```
```

