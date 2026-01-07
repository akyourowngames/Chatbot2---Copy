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
        
        # Background listening state
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_paused = False # New flag to pause background for explicit commands
        
        # Thread safety lock to prevent concurrent microphone access
        self._mic_lock = threading.Lock()
        
    def calibrate(self):
        """Calibrate microphone for ambient noise"""
        print("🎤 Calibrating microphone...")
        with self._mic_lock:
            try:
                mic = sr.Microphone()
                with mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"✅ Calibrated! Energy threshold: {self.recognizer.energy_threshold}")
            except Exception as e:
                print(f"⚠️ Calibration failed (no mic?): {e}")
    
    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen for a single phrase (pausing background listener if active)"""
        
        # FAILSAFE: Pause background listener to free up mic
        was_listening = self.is_listening
        if was_listening:
            print("[SPEECH] Pausing background listener for explicit command...")
            self.is_paused = True
            time.sleep(0.5) # Give it time to release
            
        try:
            # Acquire lock to prevent concurrent microphone access
            with self._mic_lock:
                try:
                    # Create a fresh microphone instance for each call
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
        finally:
            # RESUME BACKGROUND LISTENER
            if was_listening:
                print("[SPEECH] Resuming background listener...")
                self.is_paused = False
    
    def start_background_listening(self, callback):
        """Start continuous background listening"""
        if self.is_listening: return
        
        def listen_worker():
            print("[SPEECH] Background listener started")
            while self.is_listening:
                if self.is_paused:
                    time.sleep(0.2)
                    continue

                try:
                    # Use lock but verify we aren't paused before grabbing mic
                    with self._mic_lock: 
                         # We treat each listen chunk as a separate context 
                         # so we can release the mic for 'listen_once'
                        mic = sr.Microphone()
                        with mic as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            try:
                                # Listen with short timeout to allow frequent checks of is_paused
                                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                                self.audio_queue.put(audio)
                            except sr.WaitTimeoutError:
                                pass # Just silence, loop again
                                
                except Exception as e:
                    # print(f"[Background Listen] Error: {e}") 
                    # Don't spam logs
                    time.sleep(1)
        
        def recognize_worker():
            while self.is_listening:
                try:
                    audio = self.audio_queue.get(timeout=0.5)
                    if audio:
                        try:
                            text = self.recognizer.recognize_google(audio)
                            if text: callback(text)
                        except:
                            pass
                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"[BG Recognize] Error: {e}")
        
        self.is_listening = True
        self.is_paused = False
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
