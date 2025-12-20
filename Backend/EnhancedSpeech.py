"""
Enhanced Speech Recognition - No FFmpeg Required
=================================================
Fallback to high-quality Google Speech with optimizations
"""

import speech_recognition as sr
import threading
import queue
import time
from typing import Optional

class EnhancedSpeechRecognition:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Optimize settings for better accuracy
        self.recognizer.energy_threshold = 300  # Lower for better sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # Faster response
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        
        # Background listening
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Thread safety lock to prevent concurrent microphone access
        self._mic_lock = threading.Lock()
        
    def calibrate(self):
        """Calibrate microphone for ambient noise"""
        print("🎤 Calibrating microphone...")
        with self._mic_lock:
            mic = sr.Microphone()
            with mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"✅ Calibrated! Energy threshold: {self.recognizer.energy_threshold}")
    
    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen for a single phrase"""
        # Acquire lock to prevent concurrent microphone access
        with self._mic_lock:
            try:
                # Create a fresh microphone instance for each call to avoid 
                # "audio source is already inside a context manager" error
                mic = sr.Microphone()
                with mic as source:
                    # Quick ambient noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    print("🎤 Listening...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                    
                    # Try Google Speech Recognition
                    try:
                        text = self.recognizer.recognize_google(audio)
                        print(f"✅ Recognized: {text}")
                        return text
                    except sr.UnknownValueError:
                        print("❌ Could not understand audio")
                        return None
                    except sr.RequestError as e:
                        print(f"❌ Google Speech error: {e}")
                        return None
                        
            except sr.WaitTimeoutError:
                print("⏱️ Listening timed out")
                return None
            except Exception as e:
                print(f"❌ Error: {e}")
                return None
    
    def start_background_listening(self, callback):
        """Start continuous background listening"""
        def listen_worker():
            # Create a fresh microphone instance for background listening
            mic = sr.Microphone()
            with mic as source:
                # Adjust for ambient noise once at the start
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        pass
                    except Exception as e:
                        print(f"[Background Listen] Error: {e}")
                        pass
        
        def recognize_worker():
            while self.is_listening:
                try:
                    audio = self.audio_queue.get(timeout=1)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        callback(text)
                    except:
                        pass
                except queue.Empty:
                    pass
        
        self.is_listening = True
        threading.Thread(target=listen_worker, daemon=True).start()
        threading.Thread(target=recognize_worker, daemon=True).start()
    
    def stop_background_listening(self):
        """Stop background listening"""
        self.is_listening = False

# Global instance
enhanced_speech = EnhancedSpeechRecognition()

if __name__ == "__main__":
    # Test
    enhanced_speech.calibrate()
    print("\nSpeak something...")
    result = enhanced_speech.listen_once()
    print(f"Result: {result}")
