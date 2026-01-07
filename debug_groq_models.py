import requests
import os
from dotenv import dotenv_values

# Load env from parent directory if needed
env_path = ".env"
if not os.path.exists(env_path):
    env_path = "../.env"
env_vars = dotenv_values(env_path)

GROQ_API_KEYS = [
    os.environ.get("GROQ_API_KEY_1") or env_vars.get("GROQ_API_KEY_1", ""),
    os.environ.get("GROQ_API_KEY_2") or env_vars.get("GROQ_API_KEY_2", ""),
    os.environ.get("GROQ_API_KEY") or env_vars.get("GroqAPIKey", ""),
    env_vars.get("GROQ_API_KEY", "") 
]
key = next((k for k in GROQ_API_KEYS if k and len(k) > 10), None)

if not key:
    print("No Groq Key found in .env or env vars!")
    exit()

print(f"Checking models with key: {key[:10]}...")

try:
    resp = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print("\nAvailable Models:")
        for model in data.get('data', []):
            mid = model['id']
            if 'vision' in mid.lower() or 'llama' in mid.lower():
                print(f" - {mid}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

except Exception as e:
    print(f"Exception: {e}")
