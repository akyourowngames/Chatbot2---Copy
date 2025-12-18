import google.generativeai as genai
from dotenv import dotenv_values
import os

env_vars = dotenv_values(".env")
GEMINI_API_KEY = env_vars.get("GeminiAPIKey", "") or env_vars.get("GEMINI_API_KEY")

print(f"Checking Key: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:] if GEMINI_API_KEY else 'None'}")

if not GEMINI_API_KEY:
    print("❌ No Gemini API Key found in .env")
    exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # List models to debug
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")

    # Try alias
    print("Testing gemini-flash-latest...")
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content("Say 'Gemini is working'")
    print(f"[SUCCESS] Response: {response.text}")

except Exception as e:
    # Use ascii compliant print
    print(f"[ERROR] {e}")
    exit(1)
