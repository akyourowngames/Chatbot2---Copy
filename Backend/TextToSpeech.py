import pyttsx3
import os
import random
import time
import edge_tts
import asyncio
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US")

# Global mixer state
mixer_initialized = False
tts_engine = None

def init_fallback_tts():
    """Initialize fallback TTS engine with optimized settings"""
    global tts_engine
    try:
        tts_engine = pyttsx3.init()
        # Set properties for faster, better voice
        voices = tts_engine.getProperty('voices')
        if voices:
            # Try to find a good English voice
            for voice in voices:
                if 'en' in voice.languages or 'english' in voice.name.lower():
                    tts_engine.setProperty('voice', voice.id)
                    break
            else:
                tts_engine.setProperty('voice', voices[0].id)
        
        tts_engine.setProperty('rate', 180)  # Faster speech rate
        tts_engine.setProperty('volume', 0.9)  # Higher volume
        return True
    except Exception as e:
        print(f"Failed to initialize fallback TTS: {e}")
        return False

# Initialize TTS engine at startup for faster response
print("Initializing TTS engine...")
init_fallback_tts()
print("TTS engine ready!")

async def TextToAudioFile(text: str) -> bool:
    """
    Converts the given text to an audio file using edge_tts and saves it as 'speech.mp3'.
    Returns True if successful, False otherwise.
    """
    # Use dynamic path construction
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "Data", "speech.mp3")

    # Remove existing file if it exists
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except PermissionError:
            # File might be in use, wait a bit and try again
            time.sleep(0.1)
            try:
                os.remove(file_path)
            except PermissionError:
                pass  # Continue anyway

    # Use edge_tts to generate the audio file
    try:
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
        await communicate.save(file_path)
        return True
    except Exception as e:
        print(f"Error generating TTS audio with EdgeTTS: {e}")
        print("Falling back to offline TTS (pyttsx3)...")
        try:
            # Fallback to pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, file_path)
            engine.runAndWait()
            return True
        except Exception as e2:
            print(f"Fallback TTS failed: {e2}")
            return False

def TTS(Text: str, func=lambda r=None: True) -> bool:
    """
    Fast Text-to-Speech functionality using pyttsx3 directly for better performance.
    """
    global tts_engine
    
    try:
        # Use pyttsx3 directly for faster performance
        if tts_engine is None:
            if not init_fallback_tts():
                print("Failed to initialize TTS engine")
                return False
        
        # Clean the text for better speech
        clean_text = Text.strip()
        if not clean_text:
            return True
        
        # Speak directly without file generation
        tts_engine.say(clean_text)
        tts_engine.runAndWait()
        print(f"TTS: Spoke '{clean_text[:50]}...'")  # Debug output
        return True

    except Exception as e:
        print(f"Error in TTS: {e}")
        # Try to reinitialize TTS engine
        try:
            tts_engine = None
            if init_fallback_tts():
                tts_engine.say(Text)
                tts_engine.runAndWait()
                return True
        except Exception as e2:
            print(f"Error in TTS retry: {e2}")
        return False

    finally:
        try:
            func(False)
        except Exception as e:
            print(f"Error in finally block: {e}")

def TextToSpeech(Text: str, func=lambda r=None: True):
    """
    Handles long text input by splitting it and managing playback.
    """
    sentences = Text.split(".")

    # Predefined responses
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see."
    ]

    # Check if the text is long
    if len(sentences) > 4 and len(Text) >= 250:
        TTS(" ".join(sentences[:2]) + ". " + random.choice(responses), func)
    else:
        TTS(Text, func)

if __name__ == "__main__":
    os.makedirs("Data", exist_ok=True)  # Ensure Data directory exists

    while True:
        user_input = input("Enter the text: ")
        TextToSpeech(user_input)
