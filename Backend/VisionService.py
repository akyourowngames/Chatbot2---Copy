"""
Vision Analysis Service - Multi-Key Gemini
==========================================
Robust image analysis using Google Gemini 2.0 Flash with smart key rotation.
"""

import os
import time
import requests
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from dotenv import dotenv_values

# Load env
env_path = ".env"
if not os.path.exists(env_path):
    env_path = "../.env"
env_vars = dotenv_values(env_path)

class VisionService:
    def __init__(self):
        self.models = ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest", "models/gemini-pro-latest"]
        self.api_keys = self._load_api_keys()
        self.current_key_idx = 0
        
        if self.api_keys:
            self._configure_genai(self.api_keys[0])
            print(f"[VisionService] Online with {len(self.api_keys)} Gemini Keys")
        else:
            print("[VisionService] WARNING: No Gemini API keys found!")

    def _load_api_keys(self) -> List[str]:
        keys = []
        # Check standard names
        candidates = [
            os.environ.get("GEMINI_API_KEY"),
            env_vars.get("GeminiAPIKey"),
            env_vars.get("GEMINI_API_KEY"),
            env_vars.get("GOOGLE_API_KEY")
        ]
        # Check rotation names (1-5)
        for i in range(1, 6):
            k = os.environ.get(f"GEMINI_API_KEY_{i}") or env_vars.get(f"GEMINI_API_KEY_{i}")
            if k: candidates.append(k)
            
        # Filter valid keys (unique, non-empty, valid length)
        valid_keys = []
        seen = set()
        for k in candidates:
            if k and len(k) > 10 and k not in seen:
                valid_keys.append(k)
                seen.add(k)
        
        return valid_keys

    def _configure_genai(self, key: str):
        try:
            genai.configure(api_key=key)
        except Exception as e:
            print(f"[VisionService] Config Error: {e}")

    def _rotate_key(self) -> bool:
        """Switch to next available key. Returns True if rotated, False if exhausted cycle."""
        if len(self.api_keys) <= 1:
            return False
            
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_idx]
        print(f"[VisionService] Rotating to Key #{self.current_key_idx + 1}...")
        self._configure_genai(new_key)
        return True

    def analyze(self, image_source: str, prompt: str = "Describe this image.") -> Dict[str, Any]:
        if not self.api_keys:
            return {"success": False, "error": "No API keys available"}
            
        # Try up to (Number of keys * 2) or max 5 attempts to find a working key/model
        max_attempts = max(3, len(self.api_keys) * 2)
        errors = []
        
        print(f"[VisionService] Analyzing image: {image_source[:100]}...")
        
        # Prepare Image Once
        image_part = self._prepare_image(image_source)
        if not image_part:
            return {"success": False, "error": "Failed to load/download image"}

        for attempt in range(max_attempts):
            # Try each model in priority order for the CURRENT key
            for model_name in self.models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([prompt, image_part])
                    
                    if response.text:
                        print(f"[VisionService] Analysis complete using {model_name}")
                        return {
                            "success": True, 
                            "description": response.text, 
                            "model": model_name,
                            "key_idx": self.current_key_idx
                        }
                except Exception as e:
                    error_msg = str(e)
                    # If 429 (Rate Limit) on this specific model, we can try the NEXT model in the list
                    # on the SAME key (as they might have separate quotas).
                    if "429" in error_msg or "quota" in error_msg.lower():
                        print(f"[VisionService] Key #{self.current_key_idx + 1} hit limit on {model_name}...")
                        continue # Try next model
                    
                    if "404" in error_msg: # Model not found
                        continue
                        
                    # Other errors might be fatal for this key or global
                    errors.append(f"{model_name}: {error_msg}")
            
            # If we are here, ALL models failed for the current key (or skipped).
            # So we rotate the key.
            print(f"[VisionService] Key #{self.current_key_idx + 1} exhausted. Rotating...")
            if not self._rotate_key():
                # We cycled through all keys
                time.sleep(2) # Wait a bit before retrying the loop (which will retry Key #1)
        
        return {
            "success": False, 
            "error": "All attempts failed (Rate Limits or API Errors)", 
            "last_error": errors[-1] if errors else "Unknown"
        }

    def _prepare_image(self, image_source: str):
        import PIL.Image
        import io
        
        print(f"[VisionService] Preparing image from: {image_source[:80]}...")
        
        try:
            # Handle URLs (Firebase Storage, etc.)
            if image_source.startswith(("http://", "https://")):
                print(f"[VisionService] Downloading image from URL...")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"} 
                response = requests.get(image_source, headers=headers, timeout=15)
                response.raise_for_status()
                content = response.content
                print(f"[VisionService] Downloaded {len(content)} bytes")
                return PIL.Image.open(io.BytesIO(content))
            else:
                # Local file path
                if not os.path.exists(image_source):
                    print(f"[VisionService] ERROR: File not found: {image_source}")
                    return None
                return PIL.Image.open(image_source)
        except requests.exceptions.RequestException as e:
            print(f"[VisionService] URL Download Error: {e}")
            return None
        except Exception as e:
            print(f"[VisionService] Image Load Error: {e}")
            return None

    # --- Convenience Methods ---
    def describe(self, img): 
        res = self.analyze(img, "Describe this image in detail using structured Markdown. Use Bold Headers and Bullet Points.")
        return res.get("description", res.get("error"))

    def generate_caption(self, img): 
        res = self.analyze(img, "Write a short, engaging social media caption with hashtags.")
        return res.get("description", res.get("error"))

    def extract_text(self, img): 
        res = self.analyze(img, "Extract all text from this image exactly as it appears. Preserve layout if possible.")
        return res.get("description", res.get("error"))

    def answer_question(self, img, q): 
        res = self.analyze(img, f"{q} (Provide a structured answer with clear points)")
        return res.get("description", res.get("error"))

    def get_mood(self, img): 
        res = self.analyze(img, "What is the mood/atmosphere? Use descriptive adjectives.")
        return res.get("description", res.get("error"))

vision_service = VisionService()
def get_vision_service(): return vision_service
