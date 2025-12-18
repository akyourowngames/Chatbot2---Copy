import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_chat(query):
    print(f"\n--- TESTING: '{query}' ---")
    url = f"{BASE_URL}/api/v1/chat"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "pro_key_67890" 
    }
    payload = {"query": query}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("STATUS: SUCCESS")
            print(f"RESPONSE: {data.get('response')}")
            print(f"RAW: {json.dumps(data, indent=2)}")
        else:
            print(f"STATUS: FAILED ({response.status_code})")
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    print("Waiting for server to be fully ready...")
    time.sleep(2) 
    
    # 1. Simple Hello (should be Conversation)
    test_chat("Hello KAI")

    # 2. Complex Multi-Step (The goal!)
    test_chat("Search for a pizza place near me and open their website")
    
    # 3. Document Creation (Legacy preserved via tool?)
    test_chat("Create a PDF about Space")
    test_chat("Calculate the factorial of 10 using python code")
    test_chat("Translate 'Hello friend' to Spanish")
    test_chat("Solve the equation 2x + 10 = 20")
    test_chat("Set a reminder to buy milk at 5pm tomorrow")
