# test_llm.py
from app.utils.llm_client import call_llm

response = call_llm('Return ONLY JSON: {"test": 123}')
print(response)