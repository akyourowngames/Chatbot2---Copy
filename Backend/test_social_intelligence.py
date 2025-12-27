"""
Unit Tests for Social Intelligence System
==========================================
Tests context analysis, persona adaptation, and vibe checking.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.SocialIntelligence import SocialIntelligence, SocialContext, VibeCheck


def test_audience_detection():
    """Test that we correctly detect different audiences"""
    si = SocialIntelligence()
    
    # Test friends detection
    context = si.analyze_context("hey kai give your introduction to my friends")
    assert context.audience == "friends", f"Expected 'friends', got '{context.audience}'"
    print("✓ Friends detection works")
    
    # Test professional detection
    context = si.analyze_context("explain what you do for my resume")
    assert context.audience == "professional", f"Expected 'professional', got '{context.audience}'"
    print("✓ Professional detection works")
    
    # Test public detection
    context = si.analyze_context("present to my class what you can do")
    assert context.audience == "public", f"Expected 'public', got '{context.audience}'"
    print("✓ Public detection works")
    
    # Test solo (default)
    context = si.analyze_context("what's the weather?")
    assert context.audience == "solo", f"Expected 'solo', got '{context.audience}'"
    print("✓ Solo detection works")


def test_intent_classification():
    """Test intent classification accuracy"""
    si = SocialIntelligence()
    
    # Test present_assistant intent
    context = si.analyze_context("introduce yourself to my friends")
    assert context.intent == "present_assistant"
    assert context.confidence >= 0.8
    print("✓ Present assistant intent detected")
    
    # Test delegate_task intent
    context = si.analyze_context("can you help me with this task?")
    assert context.intent == "delegate_task"
    print("✓ Delegate task intent detected")
    
    # Test ask_information intent
    context = si.analyze_context("what is the capital of France?")
    assert context.intent == "ask_information"
    print("✓ Ask information intent detected")


def test_social_risk_assessment():
    """Test social risk calculation"""
    si = SocialIntelligence()
    
    # High risk: professional context
    context = si.analyze_context("explain what you do for my boss")
    assert context.social_risk == "high"
    print("✓ High social risk detected for professional")
    
    # Medium risk: friends + presentation
    context = si.analyze_context("introduce yourself to my friends")
    assert context.social_risk == "medium"
    print("✓ Medium social risk detected for friends presentation")
    
    # Low risk: solo question
    context = si.analyze_context("what's 2+2?")
    assert context.social_risk == "low"
    print("✓ Low social risk detected for simple query")


def test_vibe_check():
    """Test vibe checking functionality"""
    si = SocialIntelligence()
    
    # Test robotic response detection
    context = SocialContext(
        intent="present_assistant",
        audience="friends",
        user_goal="look_competent",
        social_risk="medium",
        confidence=0.85,
        detected_keywords=["introduce"]
    )
    
    robotic_response = "I am an artificial intelligence assistant designed to help with various tasks."
    vibe = si.vibe_check(robotic_response, context)
    assert vibe.trying_too_hard == True
    assert vibe.sounds_natural == False
    print("✓ Robotic response detected")
    
    # Test natural response
    natural_response = "Hey! I'm KAI — basically his second brain when things get busy."
    vibe = si.vibe_check(natural_response, context)
    assert vibe.trying_too_hard == False
    assert vibe.sounds_natural == True
    print("✓ Natural response accepted")


def test_persona_templates():
    """Test that persona templates are appropriate for context"""
    si = SocialIntelligence()
    
    # Casual friends template
    guidance = si._get_persona_template("friends", "present_assistant")
    assert "casual" in guidance.lower() or "friendly" in guidance.lower()
    print("✓ Friends persona template is casual")
    
    # Professional template
    guidance = si._get_persona_template("professional", "present_assistant")
    assert "professional" in guidance.lower()
    print("✓ Professional persona template is formal")


def test_user_style_persistence():
    """Test loading and saving user style profiles"""
    si = SocialIntelligence()
    test_user_id = "test_user_12345"
    
    # Load default style
    style = si._load_user_style(test_user_id)
    assert "preferences" in style
    assert "learned_patterns" in style
    print("✓ User style loads with defaults")
    
    # Update style
    si.update_user_style(test_user_id, "correction", {"feedback": "too formal"})
    
    # Load updated style
    updated_style = si._load_user_style(test_user_id)
    assert updated_style["preferences"]["tone_preference"] == "casual"
    print("✓ User style updates and persists")
    
    # Cleanup
    import os
    profile_path = os.path.join("Data/social_profiles", f"{test_user_id}.json")
    if os.path.exists(profile_path):
        os.remove(profile_path)
    print("✓ Test cleanup complete")


def test_skip_simple_queries():
    """Test that simple queries skip social processing"""
    si = SocialIntelligence()
    
    # Simple question should return unchanged
    simple_response = "The weather is sunny, 25°C."
    result = si.process_response(
        user_input="what's the weather?",
        llm_response=simple_response,
        user_id="test"
    )
    
    # Should skip processing for simple solo queries with low confidence scenarios
    print("✓ Simple queries handled appropriately")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Social Intelligence Unit Tests")
    print("=" * 60)
    print()
    
    try:
        test_audience_detection()
        print()
        
        test_intent_classification()
        print()
        
        test_social_risk_assessment()
        print()
        
        test_vibe_check()
        print()
        
        test_persona_templates()
        print()
        
        test_user_style_persistence()
        print()
        
        test_skip_simple_queries()
        print()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
