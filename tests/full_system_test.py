import requests
import time
import json

BASE_URL = "http://localhost:5000/api/v1"
HEADERS = {"X-API-Key": "demo_key_12345", "Content-Type": "application/json"}

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_chat_simple():
    log("Testing Chat (Simple)...")
    try:
        payload = {"query": "Hello JARVIS"}
        res = requests.post(f"{BASE_URL}/chat", json=payload, headers=HEADERS)
        if res.status_code == 200:
            log(f"Success: {res.json().get('response')[:50]}...", "PASS")
        else:
            log(f"Failed: {res.text}", "FAIL")
    except Exception as e:
        log(f"Error: {e}", "FAIL")

def test_chat_complex_realtime():
    log("Testing Chat (Complex + Realtime)...")
    try:
        # Asking about Bitcoin to trigger realtime data fetch
        payload = {"query": "What is the detailed price of Bitcoin right now?"}
        start = time.time()
        res = requests.post(f"{BASE_URL}/chat", json=payload, headers=HEADERS)
        duration = time.time() - start
        if res.status_code == 200:
            response = res.json().get('response', '')
            log(f"Response ({duration:.2f}s): {response[:100]}...", "PASS")
            if "$" in response or "USD" in response:
                log("Real-time data detected in response!", "PASS")
            else:
                log("Real-time data might be missing.", "WARN")
        else:
            log(f"Failed: {res.text}", "FAIL")
    except Exception as e:
        log(f"Error: {e}", "FAIL")

def test_automation_trigger():
    log("Testing Automation Trigger (Browser search)...")
    # specific trigger
    try:
        payload = {"query": "search for SpaceX on google"}
        # This might actually open a browser on the user's machine if the backend is running locally.
        # We'll just check if the API acknowledges the command execution.
        res = requests.post(f"{BASE_URL}/chat", json=payload, headers=HEADERS)
        if res.status_code == 200 and res.json().get("command_executed"):
            log("Automation command executed successfully.", "PASS")
        else:
            log(f"Automation failed or not recognized: {res.json()}", "FAIL")
    except Exception as e:
         log(f"Error: {e}", "FAIL")

def test_speech_synthesis():
    log("Testing Text-to-Speech...")
    try:
        payload = {"text": "System check complete.", "mode": "play"}
        # This will play audio on the host
        res = requests.post(f"{BASE_URL}/speech/synthesize", json=payload, headers=HEADERS)
        if res.status_code == 200:
            log("Audio synthesis command sent.", "PASS")
        else:
            log(f"Failed: {res.text}", "FAIL")
    except Exception as e:
        log(f"Error: {e}", "FAIL")

def test_gestures_endpoint():
    log("Testing Gesture Endpoint...")
    try:
        # Just check status or stop (don't start to avoid camera conflict)
        payload = {"action": "stop"}
        res = requests.post(f"{BASE_URL}/gestures/control", json=payload, headers=HEADERS)
        if res.status_code == 200:
             log("Gesture endpoint responded.", "PASS")
        else:
             log(f"Failed: {res.text}", "FAIL")
    except Exception as e:
         log(f"Error: {e}", "FAIL")

def main():
    print("=== JARVIS ULTIMATE SYSTEM TEST ===\n")
    
    # 1. Health Check
    try:
        res = requests.get(f"{BASE_URL}/health")
        if res.status_code == 200:
            print(f"Server Status: {json.dumps(res.json(), indent=2)}\n")
        else:
            print("CRITICAL: Server is down or unhealthy.")
            return
    except:
        print("CRITICAL: Cannot connect to API server. Ensure python api_server.py is running.")
        return

    # 2. Run Tests
    test_chat_simple()
    print("-" * 30)
    test_chat_complex_realtime()
    print("-" * 30)
    test_speech_synthesis()
    print("-" * 30)
    test_gestures_endpoint()
    print("-" * 30)
    test_automation_trigger()
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
