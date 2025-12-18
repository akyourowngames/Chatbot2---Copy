"""
Enhanced Speech Recognition with Advanced Accuracy Improvements
================================================================
Features:
- Whisper AI integration (Lazy Loaded)
- Advanced noise cancellation (On Demand)
- Voice Activity Detection (VAD)
- Multi-engine fallback system
- Adaptive microphone calibration
"""

import speech_recognition as sr
import os
import time
import threading
import numpy as np
from dotenv import dotenv_values
from typing import Optional

env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")

# Whisper Lazy Loading
WHISPER_MODEL = None
WHISPER_AVAILABLE = False
WHISPER_LOCK = threading.Lock()

def load_whisper():
    global WHISPER_MODEL, WHISPER_AVAILABLE
    if WHISPER_MODEL is None:
        try:
            import whisper
            # Use 'tiny' or 'base' for speed, 'small' for balance. 'base' is good default.
            # Loading on CPU can be slow, so we do this only when needed or in background.
            WHISPER_MODEL = whisper.load_model("base") 
            WHISPER_AVAILABLE = True
            print("Whisper AI loaded successfully!")
        except ImportError:
            print("Whisper not available. Install with: pip install openai-whisper")
        except Exception as e:
            print(f"Error loading Whisper: {e}")

# Start loading Whisper in background to not block startup
threading.Thread(target=load_whisper, daemon=True).start()

# Initialize speech recognition with optimized settings
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Optimized configuration for SPEED and Accuracy
recognizer.energy_threshold = 280 
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_ratio = 1.5
recognizer.pause_threshold = 0.5  # Reduced from 0.8 for faster response
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.4 # Reduced for faster response
recognizer.operation_timeout = None # Removed timeout to prevent cutting off

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
TempDirPath = os.path.join(project_root, "Frontend", "Files")

def SetAssistantStatus(Status):
    """Update assistant status"""
    if not os.path.exists(TempDirPath):
        os.makedirs(TempDirPath, exist_ok=True)
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def advanced_noise_reduction(audio_data, sample_rate=16000):
    """
    Advanced noise reduction - Lazy imports to speed up start
    """
    try:
        # Lazy import heavy libraries
        import  noisereduce as nr
        from scipy import signal
        
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Apply noisereduce library for stationary noise reduction
        reduced_noise = nr.reduce_noise(
            y=audio_float,
            sr=sample_rate,
            stationary=True,
            prop_decrease=0.8
        )
        
        # Apply high-pass filter to remove low-frequency rumble
        sos = signal.butter(4, 100, 'hp', fs=sample_rate, output='sos')
        filtered = signal.sosfilt(sos, reduced_noise)
        
        # Normalize audio levels
        max_val = np.max(np.abs(filtered))
        if max_val > 0:
            filtered = filtered / max_val * 0.9
        
        # Convert back to int16
        cleaned_audio = (filtered * 32767).astype(np.int16)
        
        return sr.AudioData(cleaned_audio.tobytes(), sample_rate, 2)
    
    except ImportError:
        # If libraries missing, return original
        return audio_data
    except Exception as e:
        print(f"Noise reduction failed: {e}")
        return audio_data

def voice_activity_detection(audio_data, sample_rate=16000):
    """
    Simple energy-based voice activity detection
    """
    try:
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        rms_energy = np.sqrt(np.mean(audio_float ** 2))
        
        # Simple fast check
        return rms_energy > 0.005
        
    except Exception as e:
        print(f"VAD failed: {e}")
        return True

def whisper_recognize(audio_data) -> Optional[str]:
    """
    Use Whisper AI for speech recognition (most accurate)
    """
    global WHISPER_AVAILABLE

    # Ensure loaded
    if WHISPER_MODEL is None:
         # Wait a bit if it's still loading? Or skip.
         # For now, let's skip if not ready to avoid lag.
         if not WHISPER_AVAILABLE:
             return None

    try:
        import tempfile
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
        
        with open(temp_filename, "wb") as f:
            f.write(audio_data.get_wav_data())
        
        # Transcribe with Whisper
        result = WHISPER_MODEL.transcribe(
            temp_filename,
            language="en",
            fp16=False
        )
        
        # Clean up
        os.unlink(temp_filename)
        
        text = result["text"].strip()
        if text:
            print(f"Whisper: {text}")
            return text
        
    except FileNotFoundError:
        print("Whisper Error: ffmpeg not found. Disabling Whisper for this session.")
        WHISPER_AVAILABLE = False
        return None
    except Exception as e:
        print(f"Whisper recognition failed: {e}")
        # If it's a DLL load failed or similar persistent error, disable it
        if "DLL load failed" in str(e):
             WHISPER_AVAILABLE = False
    
    return None

def google_recognize(audio_data, language="en-US") -> Optional[str]:
    """
    Use Google Speech Recognition
    """
    try:
        text = recognizer.recognize_google(audio_data, language=language)
        if text:
            print(f"Google: {text}")
            return text
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Google service error: {e}")
    
    return None

def intelligent_sentence_completion(text):
    if not text or len(text.strip()) < 2:
        return text
    text = text.strip().lower()
    completion_patterns = {
        "what": "what do you want to know",
        "how": "how can I help you",
        "where": "where would you like to go",
        "when": "when would you like to",
        "why": "why do you want to know",
        "who": "who are you asking about",
        "open": "open what",
        "play": "play what",
        "search": "search for what",
    }
    for pattern, completion in completion_patterns.items():
        if text == pattern: # Precise match for single words
             return completion
    return text

def QueryModifier(Query):
    """Enhanced query modification"""
    if not Query: return Query
    new_query = Query.strip()
    new_query = intelligent_sentence_completion(new_query)
    question_words = ["how", "what", "who", "where", "when", "why", "which", "can you"]
    if any(new_query.lower().startswith(word) for word in question_words):
        if not new_query.endswith(('?', '.', '!')): new_query += "?"
    else:
        if not new_query.endswith(('.', '?', '!')): new_query += "."
    return new_query.capitalize()

def UniversalTranslator(Text):
    """Translate text to English"""
    try:
        import mtranslate as mt # Lazy import
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    except:
        return Text.capitalize()

def adaptive_microphone_calibration():
    """Adaptive microphone calibration"""
    print("Calibrating microphone...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
    print(f"Microphone calibrated! Threshold: {recognizer.energy_threshold}")

# Initial Calibration
# adaptive_microphone_calibration() # Moved to on-demand or background if needed to save startup time

def SpeechRecognition() -> Optional[str]:
    """
    Advanced speech recognition with multi-engine fallback
    Priority: Google (Fast) -> Whisper (Accurate)
    """
    
    # Quick Ambient Adjust every time? No, takes too long. 
    # Let's rely on dynamic threshold or do it once.
    
    try:
        SetAssistantStatus("Listening...")
        
        with microphone as source:
            print("\nListening...")
            # recognizer.adjust_for_ambient_noise(source, duration=0.2) # Keeping it short
            
            try:
                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10 
                )
            except sr.WaitTimeoutError:
                return None
        
        SetAssistantStatus("Processing...")
        
        if not voice_activity_detection(audio):
             return None

        # 1. Try Google FIRST for speed
        text = google_recognize(audio)
        
        # 2. If Google fails or we want double-check, use Whisper
        if not text and WHISPER_MODEL:
             text = whisper_recognize(audio)
             
        if text:
             # Translate
             text = UniversalTranslator(text)
             final_query = QueryModifier(text)
             return final_query
             
    except Exception as e:
        print(f"Error in speech recognition: {e}")
        
    return None

if __name__ == "__main__":
    print("Testing Speech Recognition...")
    while True:
        res = SpeechRecognition()
        if res: print(res)
