"""Test Vision Service with a sample image"""
from Backend.VisionService import get_vision_service

if __name__ == "__main__":
    vision = get_vision_service()
    
    # Test with Wikipedia image
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"
    
    print("🔍 Testing Vision Service with Van Gogh's Starry Night...\n")
    
    # Test 1: Describe
    print("=== TEST 1: Describe ===")
    description = vision.describe(test_url)
    print(f"Description: {description[:500]}...\n")
    
    # Test 2: Generate Caption
    print("=== TEST 2: Caption ===")
    caption = vision.generate_caption(test_url)
    print(f"Caption: {caption}\n")
    
    # Test 3: Answer Question
    print("=== TEST 3: Visual Q&A ===")
    answer = vision.answer_question(test_url, "Who painted this and what style is it?")
    print(f"Q: Who painted this?\nA: {answer}\n")
    
    # Test 4: Mood
    print("=== TEST 4: Mood ===")
    mood = vision.get_mood(test_url)
    print(f"Mood: {mood}\n")
    
    print("✅ Vision Service working!")
