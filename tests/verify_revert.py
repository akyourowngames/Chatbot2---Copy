import requests
import time

url = "http://localhost:5000/api/v1/chat"
headers = {"X-API-Key": "demo_key_12345", "Content-Type": "application/json"}

def test_query(query):
    start = time.time()
    try:
        resp = requests.post(url, json={"query": query}, headers=headers)
        duration = time.time() - start
        print(f"Query: '{query}'")
        print(f"Time: {duration:.2f}s")
        print(f"Response: {resp.json().get('response')}")
        print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

print("Verifying Revert to Legacy Architecture...")
# 1. Smart Trigger Test
test_query("Open Google")

# 2. General LLM Test (Should use standardized LLM but direct path)
test_query("What is the capital of France?")
