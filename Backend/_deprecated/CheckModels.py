from groq import Groq
from dotenv import dotenv_values

import os
env_vars = dotenv_values(".env")
api_key = os.getenv("GROQ_API_KEY") or env_vars.get("GroqAPIKey") or env_vars.get("GROQ_API_KEY", "")

try:
    client = Groq(api_key=api_key)
    models = client.models.list()
    print("Available Models:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error: {e}")
