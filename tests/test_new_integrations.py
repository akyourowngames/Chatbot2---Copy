
import pytest
import sys
from unittest.mock import patch, MagicMock
from Backend.SmartTrigger import SmartTrigger
import json

# Mock dependencies that might not be fully configured in test env
sys.modules['Backend.EnhancedImageGen'] = MagicMock()
sys.modules['Backend.InstagramAutomation'] = MagicMock()
sys.modules['Backend.MathSolver'] = MagicMock()
sys.modules['Backend.Translator'] = MagicMock()

def test_smart_trigger_detections():
    st = SmartTrigger()
    
    # Test Image Gen
    trigger, cmd, _ = st.detect("generate an image of a cybernetic city")
    assert trigger == "image"
    assert "cybernetic city" in cmd
    
    # Test Instagram
    trigger, cmd, _ = st.detect("post on instagram hello world")
    assert trigger == "instagram"
    
    # Test Math
    trigger, cmd, _ = st.detect("calculate 50 * 20")
    assert trigger == "math"
    
    # Test Translate
    trigger, cmd, _ = st.detect("translate hello to french")
    assert trigger == "translate"
    assert "hello" in cmd

if __name__ == "__main__":
    test_smart_trigger_detections()
    print("All SmartTrigger tests passed!")
