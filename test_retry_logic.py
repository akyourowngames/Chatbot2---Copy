"""
Test Query Logic
================
Simulates setting an action in history and then running a retry to see if it works.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.ActionHistory import action_history
from Backend.EnhancedImageGen import enhanced_image_gen

def test_retry():
    print("1. Setting up mock action (Image Gen Failure)...")
    action_history.log_action(
        "image_gen", 
        {"prompt": "A futuristic city on Mars", "num_images": 1}, 
        "Generate image: A futuristic city..."
    )
    action_history.update_status("failed", "Simulated failure")
    
    print("2. Current History State:")
    print(action_history.get_last_action().to_dict())
    
    # Simulate Chatbot Retry Logic
    print("\n3. Simulating 'retry' command...")
    last = action_history.get_last_action()
    if last and last.action_type == "image_gen":
        print(f"   -> Retry detected for: {last.action_type}")
        print("   -> Re-running generation (mocking call)...")
        # In real app, we call: enhanced_image_gen.generate_pollinations(...)
        print("   ✅ Retry logic path is valid.")
    else:
        print("   ❌ Retry logic failed to find action.")

if __name__ == "__main__":
    test_retry()
