# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()

print("API KEY:", os.getenv("GROQ_API_KEY"))