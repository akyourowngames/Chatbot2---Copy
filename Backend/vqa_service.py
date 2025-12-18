"""
Production-Ready Visual Question Answering (VQA) Service
=========================================================
Combines BLIP image captioning, Tesseract OCR, and LLM reasoning
with Imagga API as fallback for robust image analysis.

Author: AI Assistant
Date: 2025-12-12
"""

import os
import base64
import logging
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

import torch
from PIL import Image
import pytesseract
import requests
from transformers import BlipProcessor, BlipForConditionalGeneration
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class VQAService:
    """
    Visual Question Answering service combining multiple AI technologies:
    - BLIP for image captioning
    - Tesseract for OCR
    - Imagga API for fallback
    - LLM for reasoning
    """
    
    def __init__(self):
        """Initialize VQA service with all components"""
        self.device = self._detect_device()
        self.blip_model = None
        self.blip_processor = None
        self.imagga_api_key = os.getenv('IMAGGA_API_KEY', 'acc_57d477254c5a425')
        self.imagga_api_secret = os.getenv('IMAGGA_API_SECRET', 'df1a08909930157e5e5ded60fdb8416a')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        
        logger.info(f"VQA Service initialized on device: {self.device}")
        
    def _detect_device(self) -> str:
        """Auto-detect CPU/GPU for optimal performance"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        elif torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon
            logger.info("Apple Silicon GPU detected")
        else:
            device = "cpu"
            logger.info("Using CPU (GPU not available)")
        return device
    
    def load_blip_model(self) -> bool:
        """
        Load BLIP model for image captioning
        Returns True if successful, False otherwise
        """
        try:
            if self.blip_model is not None:
                return True  # Already loaded
                
            logger.info("Loading BLIP model (Salesforce/blip-image-captioning-base)...")
            start_time = time.time()
            
            model_name = "Salesforce/blip-image-captioning-base"
            self.blip_processor = BlipProcessor.from_pretrained(model_name)
            
            # Load model with proper device handling
            if self.device == "cpu":
                self.blip_model = BlipForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32
                )
            else:
                self.blip_model = BlipForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
            
            self.blip_model = self.blip_model.to(self.device)
            self.blip_model.eval()  # Set to evaluation mode
            
            load_time = time.time() - start_time
            logger.info(f"BLIP model loaded successfully in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load BLIP model: {e}")
            return False
    
    def generate_caption(self, image_path: str) -> Optional[str]:
        """
        Generate image caption using BLIP
        
        Args:
            image_path: Path to image file
            
        Returns:
            Caption string or None if failed
        """
        try:
            # Load model if not already loaded
            if not self.load_blip_model():
                return None
            
            # Load and process image
            image = Image.open(image_path).convert('RGB')
            
            # Generate caption
            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                output = self.blip_model.generate(**inputs, max_length=50)
            
            caption = self.blip_processor.decode(output[0], skip_special_tokens=True)
            logger.info(f"BLIP caption: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"BLIP captioning failed: {e}")
            return None
    
    def extract_ocr_text(self, image_path: str) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text (empty string if no text found)
        """
        try:
            # Check if Tesseract is available
            try:
                import pytesseract
                image = Image.open(image_path)
                
                # Perform OCR
                text = pytesseract.image_to_string(image)
                text = text.strip()
                
                if text:
                    logger.info(f"OCR extracted {len(text)} characters")
                else:
                    logger.info("No text detected in image")
                    
                return text
            except (ImportError, pytesseract.TesseractNotFoundError):
                logger.warning("Tesseract OCR not available, skipping text extraction")
                return ""
            
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def analyze_with_imagga(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyze image using Imagga API (fallback method)
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with tags and description, or None if failed
        """
        try:
            logger.info("Using Imagga API for image analysis...")
            
            # Read image and encode to base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Call Imagga API for tagging
            url = 'https://api.imagga.com/v2/tags'
            auth = (self.imagga_api_key, self.imagga_api_secret)
            
            response = requests.post(
                url,
                auth=auth,
                data={'image_base64': image_data},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                tags = result.get('result', {}).get('tags', [])
                
                # Extract top tags
                top_tags = [tag['tag']['en'] for tag in tags[:10]]
                confidence_scores = [tag['confidence'] for tag in tags[:10]]
                
                logger.info(f"Imagga tags: {', '.join(top_tags[:5])}")
                
                return {
                    'tags': top_tags,
                    'confidence': confidence_scores,
                    'description': f"Image contains: {', '.join(top_tags[:5])}"
                }
            else:
                logger.error(f"Imagga API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Imagga analysis failed: {e}")
            return None
    
    def build_vqa_prompt(self, caption: str, ocr_text: str, question: str) -> str:
        """
        Build comprehensive prompt for LLM reasoning
        
        Args:
            caption: Image caption from BLIP
            ocr_text: OCR text from Tesseract
            question: User's question
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are an AI assistant analyzing an image to answer a user's question.

IMAGE ANALYSIS:
Caption: {caption if caption else 'Not available'}
Text in Image (OCR): {ocr_text if ocr_text else 'No text detected'}

USER QUESTION: {question}

Based on the image analysis above, provide a clear, accurate, and helpful answer to the user's question. If the available information is insufficient, acknowledge this and provide the best possible answer based on what you can see."""

        return prompt
    
    def get_llm_answer(self, prompt: str, caption: str = "", ocr_text: str = "") -> str:
        """
        Get answer from LLM (OpenAI or local fallback)
        
        Args:
            prompt: Formatted prompt with image context
            caption: Image caption for fallback
            ocr_text: OCR text for fallback
            
        Returns:
            LLM's answer
        """
        try:
            # Try OpenAI first if API key is available
            if self.openai_api_key:
                return self._get_openai_answer(prompt, caption, ocr_text)
            else:
                return self._get_local_llm_answer(prompt, caption, ocr_text)
                
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            # Fallback to caption-based answer
            if caption:
                return f"This image shows: {caption}"
            return "I encountered an error while processing your question."
    
    def _get_openai_answer(self, prompt: str, caption: str = "", ocr_text: str = "") -> str:
        """Get answer from OpenAI API"""
        try:
            import openai
            
            # Use new OpenAI client (v1.0+)
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant analyzing images."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            logger.info("Answer generated using OpenAI GPT-4")
            return answer
            
        except Exception as e:
            logger.warning(f"OpenAI API failed, falling back to local LLM: {e}")
            return self._get_local_llm_answer(prompt, caption, ocr_text)
    
    def _get_local_llm_answer(self, prompt: str, caption: str = "", ocr_text: str = "") -> str:
        """Get answer from local LLM or fallback to caption-based answer"""
        try:
            # Try to use Groq directly
            from groq import Groq
            
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant analyzing images."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            answer = response.choices[0].message.content
            logger.info("Answer generated using Groq LLM")
            return answer
            
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}")
            # Fallback: Create answer from caption and OCR
            parts = []
            if caption:
                parts.append(f"This image shows: {caption}")
            if ocr_text:
                parts.append(f"Text detected: {ocr_text}")
            
            if parts:
                return ". ".join(parts) + "."
            else:
                return "I can see the image but couldn't generate a detailed description."
    
    def analyze_image_vqa(self, image_path: str, question: str) -> Dict[str, Any]:
        """
        Main VQA function: Analyze image and answer question
        
        Args:
            image_path: Path to image file
            question: User's question about the image
            
        Returns:
            Dictionary with caption, OCR text, answer, and metadata
        """
        start_time = time.time()
        
        try:
            # Validate image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Step 1: Generate caption with BLIP
            caption = self.generate_caption(image_path)
            
            # Step 2: Extract text with OCR
            ocr_text = self.extract_ocr_text(image_path)
            
            # Step 3: Use Imagga as fallback if BLIP failed
            imagga_result = None
            if not caption:
                logger.warning("BLIP failed, using Imagga fallback...")
                imagga_result = self.analyze_with_imagga(image_path)
                if imagga_result:
                    caption = imagga_result['description']
            
            # Step 4: Build prompt and get LLM answer
            prompt = self.build_vqa_prompt(caption or "Unable to generate caption", ocr_text, question)
            answer = self.get_llm_answer(prompt, caption or "", ocr_text)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Determine which model was used
            model_used = "blip-base" if caption and not imagga_result else "imagga-fallback"
            llm_used = "openai-gpt-4" if self.openai_api_key else "local-llm"
            
            return {
                "success": True,
                "caption": caption or "Unable to generate caption",
                "ocr_text": ocr_text,
                "answer": answer,
                "metadata": {
                    "model": model_used,
                    "ocr_engine": "tesseract",
                    "llm": llm_used,
                    "processing_time_ms": processing_time,
                    "device": self.device,
                    "imagga_tags": imagga_result['tags'] if imagga_result else None
                }
            }
            
        except Exception as e:
            logger.error(f"VQA analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "caption": None,
                "ocr_text": None,
                "answer": f"I encountered an error analyzing the image: {str(e)}"
            }


# Global instance
_vqa_service = None

def get_vqa_service() -> VQAService:
    """Get or create global VQA service instance"""
    global _vqa_service
    if _vqa_service is None:
        _vqa_service = VQAService()
    return _vqa_service


# Convenience function for easy import
def analyze_image_vqa(image_path: str, question: str) -> Dict[str, Any]:
    """
    Analyze image and answer question (convenience function)
    
    Args:
        image_path: Path to image file
        question: User's question about the image
        
    Returns:
        VQA result dictionary
    """
    service = get_vqa_service()
    return service.analyze_image_vqa(image_path, question)


if __name__ == "__main__":
    # Test the VQA service
    print("VQA Service Test")
    print("=" * 50)
    
    service = VQAService()
    
    # Test with a sample image (if available)
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        result = service.analyze_image_vqa(test_image, "What is in this image?")
        print(f"\nCaption: {result['caption']}")
        print(f"OCR Text: {result['ocr_text']}")
        print(f"Answer: {result['answer']}")
        print(f"Processing Time: {result['metadata']['processing_time_ms']}ms")
    else:
        print(f"Test image not found: {test_image}")
        print("VQA service initialized successfully!")
