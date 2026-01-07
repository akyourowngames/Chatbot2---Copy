"""
Test Flux Upgrade
=================
Verifies that the default image generation now uses the Flux model.
"""
import sys
import os
import requests
from unittest.mock import MagicMock

# Mock requests to avoid actual network call, just check URL
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.EnhancedImageGen import enhanced_image_gen

def test_flux_default():
    print("Testing Flux Model Integration...")
    
    # Spy on requests.get
    original_get = requests.get
    requests.get = MagicMock()
    requests.get.return_value.status_code = 200
    requests.get.return_value.content = b"fake_image_data"
    
    # Run generation
    enhanced_image_gen.generate_pollinations("Test prompt", num_images=1)
    
    # Check the URL called
    args, _ = requests.get.call_args
    url = args[0]
    print(f"Called URL: {url}")
    
    if "model=flux" in url:
        print("✅ SUCCESS: Flux model parameter found in URL.")
    else:
        print("❌ FAIL: Flux model parameter MISSING.")

    # Restore
    requests.get = original_get

if __name__ == "__main__":
    test_flux_default()
