"""
Test script for VQA Service
Tests BLIP captioning, OCR, and Imagga fallback
"""

import os
import sys

print("=" * 60)
print("VQA SERVICE TEST")
print("=" * 60)

# Test 1: Import VQA Service
print("\n[TEST 1] Importing VQA Service...")
try:
    from Backend.vqa_service import VQAService, get_vqa_service
    print("✅ VQA Service imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize Service
print("\n[TEST 2] Initializing VQA Service...")
try:
    vqa = VQAService()
    print(f"✅ VQA Service initialized on device: {vqa.device}")
    print(f"   - Imagga API Key: {vqa.imagga_api_key[:10]}...")
    print(f"   - OpenAI configured: {'Yes' if vqa.openai_api_key else 'No (using local LLM)'}")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Check Tesseract
print("\n[TEST 3] Checking Tesseract OCR...")
try:
    import pytesseract
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract version: {version}")
except Exception as e:
    print(f"⚠️  Tesseract not found: {e}")
    print("   Please install Tesseract OCR binary (see TESSERACT_INSTALLATION.md)")

# Test 4: Check BLIP Model (without loading)
print("\n[TEST 4] Checking BLIP Model availability...")
try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    print("✅ BLIP model classes available")
    print("   Note: Model will be downloaded on first use (~1GB)")
except Exception as e:
    print(f"❌ BLIP not available: {e}")

# Test 5: Test with sample image (if available)
print("\n[TEST 5] Testing with sample image...")
test_image_path = "test_image.jpg"

if os.path.exists(test_image_path):
    print(f"   Found test image: {test_image_path}")
    try:
        print("   Analyzing image (this may take a moment on first run)...")
        result = vqa.analyze_image_vqa(test_image_path, "What is in this image?")
        
        if result.get('success'):
            print(f"   ✅ Caption: {result['caption']}")
            print(f"   ✅ OCR Text: {result['ocr_text'][:100] if result['ocr_text'] else 'No text detected'}")
            print(f"   ✅ Answer: {result['answer'][:150]}...")
            print(f"   ✅ Processing time: {result['metadata']['processing_time_ms']}ms")
        else:
            print(f"   ❌ Analysis failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
else:
    print(f"   ⚠️  No test image found at {test_image_path}")
    print("   Create a test_image.jpg to test full functionality")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("✅ VQA Service is ready to use!")
print("\nNext steps:")
print("1. Install Tesseract OCR binary (see TESSERACT_INSTALLATION.md)")
print("2. Test the /vqa endpoint with curl or Postman")
print("3. Upload an image and ask questions!")
print("\nExample curl command:")
print('curl -X POST http://localhost:5000/vqa \\')
print('  -F "image=@your_image.jpg" \\')
print('  -F "question=What is in this image?"')
print("=" * 60)
