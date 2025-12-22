import google.generativeai as genai
import os
from dotenv import dotenv_values

env = dotenv_values(".env")
key = os.getenv("GEMINI_API_KEY") or env.get("GeminiAPIKey") or env.get("GEMINI_API_KEY")

print(f"Key found: {'Yes' if key else 'No'}")
if key:
    genai.configure(api_key=key)
    try:
        print("Available Models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
