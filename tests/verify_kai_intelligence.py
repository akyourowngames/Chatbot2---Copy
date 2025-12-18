import sys
import os

# Ensure backend matches path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.Dispatcher import dispatcher

def run_test(query, expected_intent):
    print(f"\n--- TESTING QUERY: '{query}' ---")
    print(f"Expected Intent: {expected_intent}")
    
    # We can't easily assert internal state without modifying Dispatcher to return metadata.
    # But Dispatcher logs to stdout/stderr.
    
    try:
        response = dispatcher.process_query(query, [], "You are KAI.")
        print(f"RESPONSE: {response}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("=== STARTING KAI INTELLIGENCE VERIFICATION ===")
    
    # 1. Vision Test
    run_test("What is on my screen right now?", "vision_analysis")
    
    # 2. System Test
    run_test("Mute the volume", "system_control")
    
    # 3. Simple App Test
    run_test("Open Spotify", "app_control")
    
    # 4. Web Search Test
    run_test("What is the stock price of Apple?", "web_search")
    
    # 5. Multi-step Complex Test
    run_test("Find a pizza place near me and open their website", "multi_step")
    
    print("\n=== VERIFICATION COMPLETE ===")
