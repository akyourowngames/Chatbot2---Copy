"""
Wake Word Listener - "Hey KAI" Activation
==========================================
Background voice activation that listens for wake word
"""

import speech_recognition as sr
import threading
import time
from typing import Callable, Optional
import queue

class WakeWordListener:
    """
    Always-on wake word detection for voice activation.
    Listens for "Hey KAI" or similar phrases, then activates.
    """
    
    def __init__(self, wake_words: list = None, callback: Callable = None):
        self.wake_words = wake_words or [
            "hey kai", "ok kai", "hi kai", "kai", 
            "hey jerry", "jarvis", "hey jarvis"
        ]
        self.callback = callback
        self.is_listening = False
        self.listener_thread = None
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.command_queue = queue.Queue()
        
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
    
    def start(self):
        """Start background wake word listening"""
        if self.is_listening:
            return {"status": "already_running"}
        
        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
        print("[WAKE] Wake word listener started. Say 'Hey KAI' to activate!")
        return {"status": "started", "wake_words": self.wake_words}
    
    def stop(self):
        """Stop background listening"""
        self.is_listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        print("[WAKE] Wake word listener stopped.")
        return {"status": "stopped"}
    
    def _listen_loop(self):
        """Main listening loop running in background"""
        try:
            self.microphone = sr.Microphone()
            
            with self.microphone as source:
                # Calibrate for ambient noise once
                print("[WAKE] Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("[WAKE] Ready! Listening for wake word...")
            
            while self.is_listening:
                try:
                    with self.microphone as source:
                        # Listen for a short phrase
                        audio = self.recognizer.listen(
                            source, 
                            timeout=5,
                            phrase_time_limit=5
                        )
                    
                    # Recognize speech
                    text = self._recognize(audio)
                    
                    if text:
                        text_lower = text.lower()
                        print(f"[WAKE] Heard: {text}")
                        
                        # Check for wake word
                        wake_detected = False
                        for wake_word in self.wake_words:
                            if wake_word in text_lower:
                                wake_detected = True
                                # Extract command after wake word
                                command_start = text_lower.find(wake_word) + len(wake_word)
                                command = text[command_start:].strip()
                                
                                if not command:
                                    # Just wake word, wait for command
                                    print("[WAKE] Activated! Listening for command...")
                                    command = self._get_follow_up_command()
                                
                                if command:
                                    print(f"[WAKE] Command: {command}")
                                    self.command_queue.put(command)
                                    
                                    if self.callback:
                                        self.callback(command)
                                break
                        
                except sr.WaitTimeoutError:
                    continue  # No speech detected, keep listening
                except sr.UnknownValueError:
                    continue  # Could not understand, keep listening
                except Exception as e:
                    print(f"[WAKE] Error: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"[WAKE] Listener error: {e}")
            self.is_listening = False
    
    def _recognize(self, audio) -> Optional[str]:
        """Recognize speech from audio"""
        try:
            # Try Google first (free, no API key needed)
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            # Fallback to offline if available
            try:
                return self.recognizer.recognize_sphinx(audio)
            except:
                return None
    
    def _get_follow_up_command(self) -> Optional[str]:
        """Listen for follow-up command after wake word"""
        try:
            with self.microphone as source:
                print("[WAKE] Say your command...")
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=7
                )
                return self._recognize(audio)
        except:
            return None
    
    def get_pending_command(self) -> Optional[str]:
        """Get any pending command from queue (non-blocking)"""
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_callback(self, callback: Callable):
        """Set callback function for when command is detected"""
        self.callback = callback


# Global instance
wake_listener = WakeWordListener()


if __name__ == "__main__":
    def on_command(cmd):
        print(f"[TEST] Received command: {cmd}")
    
    wake_listener.set_callback(on_command)
    wake_listener.start()
    
    print("Listening... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wake_listener.stop()
