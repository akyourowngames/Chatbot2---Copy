"""
Enhanced Text-to-Speech System
================================
Features:
- Hybrid Engine: Offline (Fast) for short text, Online (High Quality) for long text
- Voice caching
- Async processing
"""

import pyttsx3
import os
import hashlib
import time
import asyncio
import threading
from dotenv import dotenv_values
from pathlib import Path

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural") 

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
CACHE_DIR = os.path.join(project_root, "Data", "tts_cache")

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

# Global TTS engine (Native Windows SAPI5)
engine = pyttsx3.init()
engine.setProperty('rate', 190) # Fast but clear
engine.setProperty('volume', 1.0)
# Select a concise female voice if available
voices = engine.getProperty('voices')
for v in voices:
    if "zira" in v.name.lower():
        engine.setProperty('voice', v.id)
        break

engine_lock = threading.Lock()

def play_audio_file(file_path: str):
    """Play audio file using pygame"""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05) # Lower sleep for faster reaction
    except Exception as e:
        print(f"Audio playback error: {e}")

async def generate_edge_tts(text: str, output_path: str) -> bool:
    """Generate high-quality audio"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, AssistantVoice, rate="+10%")
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"EdgeTTS failed: {e}")
        return False

def get_cache_path(text: str) -> str:
    text_hash = hashlib.md5(f"{text}_{AssistantVoice}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{text_hash}.mp3")

def TextToSpeech(text: str, func=lambda r=None: True) -> bool:
    """
    Hybrid TTS:
    - Short text (< 100 chars): Use Offline pyttsx3 (INSTANT)
    - Long text (> 100 chars): Use EdgeTTS (High Quality)
    """
    if not text: return False
    
    # Clean text
    text = text.strip()
    
    try:
        # STRATEGY 1: CACHE CHECK (Fastest)
        cache_path = get_cache_path(text)
        if os.path.exists(cache_path):
            play_audio_file(cache_path)
            return True

        # STRATEGY 2: OFFLINE TTS (Fast)
        # Use for short commands/confirmations ex: "Opening Chrome", "Time is 5 PM"
        if len(text) < 80: 
            with engine_lock:
                engine.say(text)
                engine.runAndWait()
            return True
        
        # STRATEGY 3: ONLINE TTS (High Quality)
        # Use for detailed answers
        success = asyncio.run(generate_edge_tts(text, cache_path))
        if success:
            play_audio_file(cache_path)
            return True
        else:
            # Fallback to offline if online fails
            with engine_lock:
                engine.say(text)
                engine.runAndWait()
            return True

    except Exception as e:
        print(f"TTS Error: {e}")
        # Ultimate fallback
        try:
            with engine_lock:
                engine.say(text)
                engine.runAndWait()
        except Exception as tts_err:
            print(f"[TTS] Fallback failed: {tts_err}")
        return False
    finally:
        if func: func(True)

if __name__ == "__main__":
    print("Testing Hybrid TTS...")
    TextToSpeech("Opening Google Chrome") # Should be fast/robotic
    TextToSpeech("This is a much longer sentence to test the high quality voice generation capabilities of the system, which should use the cloud engine.") # Should be high quality

