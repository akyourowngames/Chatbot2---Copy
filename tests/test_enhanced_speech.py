#!/usr/bin/env python3
"""
Test script for enhanced speech recognition capabilities
This script tests the improved low voice detection and incomplete sentence handling
"""

import sys
import os

# Add the project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from Backend.SpeechToText import SpeechRecognition, intelligent_sentence_completion, QueryModifier
from Backend.Chatbot import analyze_query_context

def test_sentence_completion():
    """Test the intelligent sentence completion feature"""
    print("Testing intelligent sentence completion...")
    
    test_cases = [
        "what",
        "how",
        "open",
        "play",
        "search",
        "hello",
        "time",
        "help",
        "i",
        "you",
        "can"
    ]
    
    for test_case in test_cases:
        result = intelligent_sentence_completion(test_case)
        print(f"Input: '{test_case}' -> Output: '{result}'")
    
    print("\n" + "="*50 + "\n")

def test_query_modification():
    """Test the enhanced query modification"""
    print("Testing enhanced query modification...")
    
    test_cases = [
        "what",
        "how can you help",
        "open",
        "play music",
        "search for",
        "hello there",
        "what time is it",
        "help me with",
        "i need",
        "you are"
    ]
    
    for test_case in test_cases:
        result = QueryModifier(test_case)
        print(f"Input: '{test_case}' -> Output: '{result}'")
    
    print("\n" + "="*50 + "\n")

def test_context_analysis():
    """Test the context analysis for unclear speech"""
    print("Testing context analysis...")
    
    # Mock chat history
    mock_history = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me with something?"},
        {"role": "assistant", "content": "Of course! What do you need help with?"}
    ]
    
    test_cases = [
        "what",  # Very short
        "how",   # Very short
        "open",  # Very short
        "um uh like you know",  # Unclear speech
        "hello there how are you doing today",  # Clear speech
        "",  # Empty
        "a"  # Too short
    ]
    
    for test_case in test_cases:
        result = analyze_query_context(test_case, mock_history)
        print(f"Input: '{test_case}' -> Output: '{result}'")
    
    print("\n" + "="*50 + "\n")

def test_speech_recognition():
    """Test the enhanced speech recognition (requires microphone)"""
    print("Testing enhanced speech recognition...")
    print("This will attempt to listen for speech with improved low voice detection.")
    print("Speak softly or with incomplete sentences to test the improvements.")
    print("Press Ctrl+C to stop testing.\n")
    
    try:
        while True:
            print("Listening... (speak now)")
            result = SpeechRecognition()
            if result:
                print(f"Recognized: '{result}'")
            else:
                print("No speech detected or recognition failed")
            print("-" * 30)
    except KeyboardInterrupt:
        print("\nSpeech recognition test stopped.")

def main():
    """Run all tests"""
    print("Enhanced Speech Recognition Test Suite")
    print("=" * 50)
    
    # Test sentence completion
    test_sentence_completion()
    
    # Test query modification
    test_query_modification()
    
    # Test context analysis
    test_context_analysis()
    
    # Test speech recognition (interactive)
    print("Would you like to test live speech recognition? (y/n): ", end="")
    choice = input().lower().strip()
    if choice in ['y', 'yes']:
        test_speech_recognition()
    else:
        print("Skipping live speech recognition test.")
    
    print("\nTest suite completed!")

if __name__ == "__main__":
    main()
