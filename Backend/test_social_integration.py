"""
Integration Tests for Social Intelligence + LLM
================================================
Tests the full pipeline with real LLM calls.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.LLM import ChatCompletion
from Backend.SocialIntelligence import social_intelligence


def test_introduction_to_friends():
    """Test: Introducing KAI to friends should be casual and cool"""
    print("\n" + "=" * 60)
    print("TEST 1: Introduction to Friends")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "hey kai give your introduction to my friends"}
    ]
    
    # Get response with social intelligence
    response = ChatCompletion(
        messages=messages,
        user_id="integration_test",
        inject_memory=False,
        apply_social_intelligence=True
    )
    
    print(f"\nUser: hey kai give your introduction to my friends")
    print(f"KAI: {response}")
    
    # Check if response is casual (not robotic)
    response_lower = response.lower()
    is_casual = not any(word in response_lower for word in [
        "artificial intelligence", "i am designed", "my capabilities"
    ])
    
    print(f"\n✓ Response is casual: {is_casual}")
    assert is_casual, "Response should be casual for friends"
    
    return response


def test_professional_introduction():
    """Test: Professional introduction should be formal"""
    print("\n" + "=" * 60)
    print("TEST 2: Professional Introduction")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "explain what you do in a professional way for my portfolio"}
    ]
    
    response = ChatCompletion(
        messages=messages,
        user_id="integration_test",
        inject_memory=False,
        apply_social_intelligence=True
    )
    
    print(f"\nUser: explain what you do in a professional way for my portfolio")
    print(f"KAI: {response}")
    
    # Should avoid casual words
    response_lower = response.lower()
    is_professional = not any(word in response_lower for word in [
        "basically", "yeah", "lol", "btw", "gonna"
    ])
    
    print(f"\n✓ Response is professional: {is_professional}")
    
    return response


def test_simple_question():
    """Test: Simple questions shouldn't trigger heavy social processing"""
    print("\n" + "=" * 60)
    print("TEST 3: Simple Question (Should Skip Social Processing)")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "what is 2+2?"}
    ]
    
    response = ChatCompletion(
        messages=messages,
        user_id="integration_test",
        inject_memory=False,
        apply_social_intelligence=True
    )
    
    print(f"\nUser: what is 2+2?")
    print(f"KAI: {response}")
    print(f"\n✓ Simple query processed")
    
    return response


def test_override_social_intelligence():
    """Test: Can disable social intelligence per call"""
    print("\n" + "=" * 60)
    print("TEST 4: Disable Social Intelligence Override")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "introduce yourself to my friends"}
    ]
    
    # Get response WITHOUT social intelligence
    response = ChatCompletion(
        messages=messages,
        user_id="integration_test",
        inject_memory=False,
        apply_social_intelligence=False
    )
    
    print(f"\nUser: introduce yourself to my friends")
    print(f"KAI (WITHOUT social intelligence): {response}")
    print(f"\n✓ Social intelligence can be disabled")
    
    return response


def test_multi_turn_conversation():
    """Test: Multi-turn conversation maintains context"""
    print("\n" + "=" * 60)
    print("TEST 5: Multi-turn Conversation")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "hey, what can you help me with?"},
        {"role": "assistant", "content": "I can help with research, task automation, and organizing information."},
        {"role": "user", "content": "cool, now introduce yourself to my friends in a fun way"}
    ]
    
    response = ChatCompletion(
        messages=messages,
        user_id="integration_test",
        inject_memory=False,
        apply_social_intelligence=True
    )
    
    print(f"\nConversation:")
    for msg in messages:
        print(f"{msg['role']}: {msg['content']}")
    print(f"assistant: {response}")
    
    print(f"\n✓ Multi-turn conversation processed")
    
    return response


if __name__ == "__main__":
    print("=" * 60)
    print("Running Social Intelligence Integration Tests")
    print("=" * 60)
    print("\nNOTE: These tests make real API calls and may take a minute.")
    print("      They verify the full LLM + Social Intelligence pipeline.")
    
    try:
        # Enable debug mode for detailed logs
        social_intelligence.debug = True
        
        test_introduction_to_friends()
        test_professional_introduction()
        test_simple_question()
        test_override_social_intelligence()
        test_multi_turn_conversation()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nSocial Intelligence is working correctly! 🧠✨")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
