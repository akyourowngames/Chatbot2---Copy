import speech_recognition as sr
import pyttsx3
import os
import time
import mtranslate as mt
import numpy as np
import pyaudio
import wave
import threading
from dotenv import dotenv_values
from scipy import signal
from scipy.io import wavfile
import tempfile

env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")

# Initialize speech recognition with enhanced settings for low voice detection
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Enhanced configuration for low voice sensitivity
recognizer.energy_threshold = 200  # Much lower threshold for quieter speech
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.5  # Shorter pause detection for faster response
recognizer.phrase_threshold = 0.2  # Faster phrase detection
recognizer.non_speaking_duration = 0.3  # Reduced silence detection
recognizer.operation_timeout = 10  # Increased timeout for processing

# Advanced ambient noise adjustment with multiple samples
print("Calibrating microphone for low voice detection...")
with microphone as source:
    # Take multiple samples for better noise calibration
    recognizer.adjust_for_ambient_noise(source, duration=1.0)
    # Additional calibration for low voices
    recognizer.adjust_for_ambient_noise(source, duration=0.5)
print("Microphone calibrated for low voice detection!")

# Use dynamic path construction
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
TempDirPath = os.path.join(project_root, "Frontend", "Files")

def SetAssistantStatus(Status):
    os.makedirs(TempDirPath, exist_ok=True)
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)
        
def intelligent_sentence_completion(text):
    """Intelligently complete incomplete sentences based on context"""
    if not text or len(text.strip()) < 2:
        return text
    
    text = text.strip().lower()
    
    # Common incomplete patterns and their completions
    completion_patterns = {
        # Question completions
        "what": "what do you want to know about",
        "how": "how can I help you with",
        "where": "where would you like to go",
        "when": "when would you like to",
        "why": "why do you want to know about",
        "who": "who are you asking about",
        "which": "which one would you like to know about",
        
        # Action completions
        "open": "open what application or website",
        "play": "play what music or video",
        "search": "search for what",
        "find": "find what information",
        "show": "show what information",
        "tell": "tell you what",
        "explain": "explain what topic",
        "help": "help you with what",
        
        # Greeting completions
        "hello": "hello, how can I help you",
        "hi": "hi, what can I do for you",
        "hey": "hey, what do you need",
        
        # Time-related completions
        "time": "what time is it",
        "date": "what is today's date",
        "weather": "what is the weather like",
        
        # System completions
        "close": "close what application",
        "minimize": "minimize what window",
        "maximize": "maximize what window"
    }
    
    # Check for incomplete patterns
    for pattern, completion in completion_patterns.items():
        if text.startswith(pattern) and len(text.split()) <= 2:
            return completion
    
    # If it's a very short phrase, try to make it more complete
    if len(text.split()) <= 2 and not text.endswith(('?', '.', '!')):
        # Add common context based on the first word
        first_word = text.split()[0]
        if first_word in ["i", "me", "my"]:
            return text + " need help with something"
        elif first_word in ["you", "your"]:
            return text + " capabilities and features"
        elif first_word in ["can", "could", "would"]:
            return text + " help me with something"
    
    return text

def QueryModifier(Query):
    """Enhanced query modification with intelligent completion"""
    if not Query:
        return Query
        
    new_query = Query.lower().strip()
    
    # First, try to complete incomplete sentences
    new_query = intelligent_sentence_completion(new_query)
    
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's", "can you"]
    
    # Enhanced question detection
    if any(word + " " in new_query for word in question_words) or new_query.startswith(tuple(question_words)):
        if not new_query.endswith(('?', '.', '!')):
            new_query += "?"
        elif new_query.endswith(('.', '!')):
            new_query = new_query[:-1] + "?"
    else:
        # For statements, ensure proper punctuation
        if not new_query.endswith(('.', '?', '!')):
            new_query += "."
        elif new_query.endswith(('?', '!')):
            new_query = new_query[:-1] + "."
            
    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

def preprocess_audio(audio_data, sample_rate=16000):
    """Advanced audio preprocessing for better speech recognition"""
    try:
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        
        # Normalize audio
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        # Apply noise reduction using spectral gating
        # This helps with low voice detection
        stft = np.fft.fft(audio_array)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Simple noise gate - amplify frequencies below threshold
        noise_floor = np.percentile(magnitude, 20)  # Bottom 20% as noise floor
        magnitude = np.where(magnitude > noise_floor * 1.5, magnitude, magnitude * 0.1)
        
        # Reconstruct audio
        cleaned_stft = magnitude * np.exp(1j * phase)
        cleaned_audio = np.real(np.fft.ifft(cleaned_stft))
        
        # Apply gentle high-pass filter to remove low-frequency noise
        b, a = signal.butter(4, 80, btype='high', fs=sample_rate)
        cleaned_audio = signal.filtfilt(b, a, cleaned_audio)
        
        # Amplify the signal slightly for low voices
        cleaned_audio = cleaned_audio * 1.5
        
        # Convert back to int16
        cleaned_audio = np.clip(cleaned_audio, -1, 1)
        cleaned_audio = (cleaned_audio * 32767).astype(np.int16)
        
        return cleaned_audio.tobytes()
    except Exception as e:
        print(f"Audio preprocessing error: {e}")
        return audio_data.get_raw_data()

def test_microphone():
    """Enhanced microphone testing with sensitivity analysis"""
    print("Testing microphone levels and sensitivity...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"Energy threshold: {recognizer.energy_threshold}")
        
        # Test with different sensitivity levels
        print("Testing low voice sensitivity...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            print("Low voice test successful!")
        except sr.WaitTimeoutError:
            print("No speech detected in test - this is normal")
        
        print("Microphone calibration complete!")

# Test microphone on startup
test_microphone()

def SpeechRecognition():
    """Advanced speech recognition with multiple fallback strategies for low voices"""
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            SetAssistantStatus("Listening...")
            
            with microphone as source:
                print(f"Attempt {attempt + 1}: Listening for speech...")
                
                # Dynamic noise adjustment based on attempt
                noise_duration = 0.2 + (attempt * 0.1)  # Increase with each attempt
                recognizer.adjust_for_ambient_noise(source, duration=noise_duration)
                
                # Progressive timeout and phrase limits for better low voice detection
                timeout = 3 + (attempt * 2)  # 3, 5, 7 seconds
                phrase_limit = 6 + (attempt * 2)  # 6, 8, 10 seconds
                
                print(f"Listening with timeout: {timeout}s, phrase limit: {phrase_limit}s")
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            
            SetAssistantStatus("Processing...")
            
            # Try multiple recognition strategies
            text = None
            
            # Strategy 1: Google Speech Recognition with auto-detection
            try:
                print("Trying Google Speech Recognition...")
                text = recognizer.recognize_google(audio, language="auto")
                print(f"Google recognition result: {text}")
            except sr.UnknownValueError:
                print("Google recognition failed - trying with preprocessing...")
                
                # Strategy 2: Preprocess audio and try again
                try:
                    # Save audio to temporary file for preprocessing
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_filename = temp_file.name
                    
                    # Save raw audio
                    with open(temp_filename, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    # Preprocess audio
                    sample_rate, audio_data = wavfile.read(temp_filename)
                    processed_audio = preprocess_audio(audio, sample_rate)
                    
                    # Create new audio source from processed data
                    processed_audio_source = sr.AudioData(processed_audio, sample_rate, 2)
                    
                    # Try recognition again with processed audio
                    text = recognizer.recognize_google(processed_audio_source, language="auto")
                    print(f"Processed audio recognition result: {text}")
                    
                    # Clean up temp file
                    os.unlink(temp_filename)
                    
                except Exception as e:
                    print(f"Audio preprocessing failed: {e}")
                    
                    # Strategy 3: Try with different language models
                    try:
                        print("Trying with English-specific model...")
                        text = recognizer.recognize_google(audio, language="en-US")
                        print(f"English model result: {text}")
                    except:
                        print("All recognition strategies failed")
                        text = None
            
            except sr.RequestError as e:
                print(f"Speech recognition service error: {e}")
                SetAssistantStatus("Speech recognition service error")
                return None
            
            # Process the recognized text
            if text and text.strip():
                print(f"Final recognized text: {text}")
                
                # Translate to English if needed
                english_text = UniversalTranslator(text)
                print(f"Translated to English: {english_text}")
                
                # Apply intelligent query modification
                final_query = QueryModifier(english_text)
                print(f"Final processed query: {final_query}")
                
                SetAssistantStatus("Ready")
                return final_query
            else:
                print(f"Attempt {attempt + 1} failed - no text recognized")
                attempt += 1
                if attempt < max_attempts:
                    print("Trying again with adjusted settings...")
                    # Adjust settings for next attempt
                    recognizer.energy_threshold = max(100, recognizer.energy_threshold - 50)
                    time.sleep(0.5)  # Brief pause between attempts
                else:
                    print("All attempts failed - please speak louder or clearer")
                    SetAssistantStatus("Could not understand audio")
                    return None
                    
        except sr.WaitTimeoutError:
            print(f"Attempt {attempt + 1}: No speech detected")
            attempt += 1
            if attempt < max_attempts:
                print("Trying again...")
                time.sleep(0.5)
            else:
                print("No speech detected after all attempts")
                SetAssistantStatus("No speech detected")
                return None
                
        except Exception as e:
            print(f"Speech recognition error on attempt {attempt + 1}: {e}")
            attempt += 1
            if attempt < max_attempts:
                print("Trying again...")
                time.sleep(0.5)
            else:
                print("All attempts failed due to errors")
                SetAssistantStatus("Speech recognition error")
                return None
    
    return None

if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)