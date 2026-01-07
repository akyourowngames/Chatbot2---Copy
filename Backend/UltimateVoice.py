"""
Ultimate Voice Service for KAI
==============================
Complete voice system with:
- Multi-TTS (Edge TTS → gTTS fallback)
- Hindi + English support
- Groq Whisper for ultra-fast STT
- Barge-in (auto-stop on user speech)
- Conversation mode (auto-listen after response)
"""

import os
import asyncio
import threading
import time
import base64
from typing import Optional, Callable
from io import BytesIO

# ==================== VOICE CONFIGURATION ====================
VOICE_CONFIG = {
    "english": {
        "edge_female": "en-US-AriaNeural",
        "edge_male": "en-US-GuyNeural",
        "default": "en-US-AriaNeural"
    },
    "hindi": {
        "edge_female": "hi-IN-SwaraNeural",
        "edge_male": "hi-IN-MadhurNeural", 
        "default": "hi-IN-SwaraNeural"
    },
    "hinglish": {
        "edge_female": "en-IN-NeerjaNeural",  # Indian English
        "edge_male": "en-IN-PrabhatNeural",
        "default": "en-IN-NeerjaNeural"
    }
}

# Hindi words for language detection
HINDI_INDICATORS = [
    "क", "ख", "ग", "घ", "च", "छ", "ज", "झ", "ट", "ठ", "ड", "ढ", "ण",
    "त", "थ", "द", "ध", "न", "प", "फ", "ब", "भ", "म", "य", "र", "ल",
    "व", "श", "ष", "स", "ह", "ा", "ि", "ी", "ु", "ू", "े", "ै", "ो", "ौ",
    # Common romanized Hindi words
    "aap", "kya", "hai", "hain", "kaise", "kaisa", "theek", "shukriya",
    "namaste", "dhanyavaad", "bahut", "accha", "bhai", "yaar"
]


class UltimateVoice:
    """Ultimate Voice Service with multi-provider TTS and Whisper STT"""
    
    def __init__(self):
        self.is_speaking = False
        self.is_listening = False
        self.should_stop = False
        self.conversation_mode = False
        self.current_audio_file = None
        
        # Callbacks
        self.on_speech_detected: Optional[Callable] = None
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_tts_complete: Optional[Callable] = None
        
        # Get API keys
        self._groq_key = os.getenv('GROQ_API_KEY')
        
        # Data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        print("[UltimateVoice] ✓ Initialized")
    
    # ==================== LANGUAGE DETECTION ====================
    def detect_language(self, text: str) -> str:
        """Detect if text is Hindi, English, or Hinglish"""
        # Check for Devanagari script
        for char in text:
            if '\u0900' <= char <= '\u097F':
                return "hindi"
        
        # Check for romanized Hindi words
        text_lower = text.lower()
        hindi_word_count = sum(1 for word in HINDI_INDICATORS if word in text_lower)
        
        if hindi_word_count >= 2:
            return "hinglish"
        
        return "english"
    
    # ==================== TEXT-TO-SPEECH ====================
    async def speak_async(
        self, 
        text: str, 
        voice: str = None,
        language: str = None,
        speed: str = "+20%",
        save_path: str = None
    ) -> Optional[str]:
        """
        Generate TTS audio and return file path
        
        Args:
            text: Text to speak
            voice: Specific voice to use (or auto-detect)
            language: Force language (english/hindi/hinglish)
            speed: Speed adjustment (e.g., "+10%", "-5%")
            save_path: Custom save path
            
        Returns:
            Path to generated audio file
        """
        if not text or not text.strip():
            return None
            
        self.is_speaking = True
        self.should_stop = False
        
        try:
            # Auto-detect language if not specified
            if not language:
                language = self.detect_language(text)
            
            # Get voice for language
            if not voice:
                voice = VOICE_CONFIG.get(language, VOICE_CONFIG["english"])["default"]
            
            # Generate unique filename
            if not save_path:
                timestamp = int(time.time() * 1000)
                save_path = os.path.join(self.data_dir, f"tts_{timestamp}.mp3")
            
            self.current_audio_file = save_path
            
            # Use gTTS directly (reliable, supports Hindi and English)
            success = await self._generate_gtts(text, save_path, language)
            
            if success and os.path.exists(save_path):
                print(f"[TTS] ✅ Generated: {save_path} (lang={language})")
                return save_path
            else:
                print("[TTS] ❌ gTTS failed")
                return None
                
        except Exception as e:
            print(f"[TTS] Error: {e}")
            return None
        finally:
            self.is_speaking = False
            if self.on_tts_complete and not self.should_stop:
                self.on_tts_complete()
    
    async def _generate_gtts(
        self, 
        text: str, 
        output_path: str,
        language: str = "english"
    ) -> bool:
        """Generate audio using gTTS (Google) - reliable for Hindi and English"""
        try:
            from gtts import gTTS
            
            # Map language to gTTS lang code
            lang_map = {
                "english": "en",
                "hindi": "hi",
                "hinglish": "en"  # Use English for Hinglish
            }
            lang_code = lang_map.get(language, "en")
            
            # Use Indian English TLD for better Hindi name pronunciation
            tld = "co.in" if language in ["hindi", "hinglish"] else "com"
            
            print(f"[gTTS] Generating audio for {language}...")
            tts = gTTS(text=text, lang=lang_code, tld=tld)
            tts.save(output_path)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                print(f"[gTTS] ✅ Generated successfully")
                return True
            return False
            
        except Exception as e:
            print(f"[gTTS] Error: {e}")
            return False
    
    def speak(self, text: str, **kwargs) -> Optional[str]:
        """Synchronous wrapper for speak_async"""
        return asyncio.run(self.speak_async(text, **kwargs))
    
    # ==================== SPEECH-TO-TEXT ====================
    async def transcribe_async(
        self, 
        audio_path: str = None,
        audio_data: bytes = None,
        language: str = None
    ) -> Optional[str]:
        """
        Transcribe audio using Groq Whisper (ultra-fast!)
        
        Args:
            audio_path: Path to audio file
            audio_data: Raw audio bytes
            language: Force language hint
            
        Returns:
            Transcribed text
        """
        if not self._groq_key:
            print("[STT] No Groq API key, falling back to Google Speech")
            return await self._transcribe_google(audio_path, audio_data)
        
        try:
            import requests
            
            # Read audio data
            if audio_path:
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
            
            if not audio_data:
                return None
            
            start_time = time.time()
            
            # Groq Whisper API
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {self._groq_key}"
                },
                files={
                    "file": ("audio.wav", audio_data, "audio/wav")
                },
                data={
                    "model": "whisper-large-v3",
                    "language": language or "en",
                    "response_format": "text"
                },
                timeout=10
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                text = response.text.strip()
                print(f"[STT] ✅ Groq Whisper: '{text[:50]}...' ({elapsed:.2f}s)")
                return text
            else:
                print(f"[STT] Groq error: {response.status_code}")
                return await self._transcribe_google(audio_path, audio_data)
                
        except Exception as e:
            print(f"[STT] Groq error: {e}")
            return await self._transcribe_google(audio_path, audio_data)
    
    async def _transcribe_google(
        self, 
        audio_path: str = None,
        audio_data: bytes = None
    ) -> Optional[str]:
        """Fallback to Google Speech Recognition"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            if audio_path:
                with sr.AudioFile(audio_path) as source:
                    audio = recognizer.record(source)
            elif audio_data:
                # Convert bytes to AudioData
                audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            else:
                return None
            
            text = recognizer.recognize_google(audio)
            print(f"[STT] ✅ Google: '{text[:50]}...'")
            return text
            
        except Exception as e:
            print(f"[STT] Google error: {e}")
            return None
    
    def transcribe(self, audio_path: str = None, audio_data: bytes = None) -> Optional[str]:
        """Synchronous wrapper for transcribe_async"""
        return asyncio.run(self.transcribe_async(audio_path, audio_data))
    
    # ==================== BARGE-IN (INTERRUPT) ====================
    def interrupt(self):
        """Stop current TTS playback (barge-in)"""
        self.should_stop = True
        self.is_speaking = False
        
        # Try to stop pygame mixer if playing
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                print("[Voice] 🛑 TTS interrupted (barge-in)")
        except:
            pass
        
        # Clean up current audio file
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.remove(self.current_audio_file)
            except:
                pass
    
    # ==================== CONVERSATION MODE ====================
    def start_conversation_mode(
        self,
        on_transcription: Callable[[str], None],
        on_speech_detected: Callable = None
    ):
        """
        Start conversation mode - auto-listen after TTS completes
        
        Args:
            on_transcription: Callback when speech is transcribed
            on_speech_detected: Callback when user starts speaking (for barge-in)
        """
        self.conversation_mode = True
        self.on_transcription = on_transcription
        self.on_speech_detected = on_speech_detected
        
        # Set TTS complete callback to start listening
        def on_tts_done():
            if self.conversation_mode and not self.should_stop:
                print("[Voice] 🎤 TTS done, listening for response...")
                # Small delay before listening
                time.sleep(0.3)
                self._listen_once()
        
        self.on_tts_complete = on_tts_done
        print("[Voice] 🔄 Conversation mode ENABLED")
    
    def stop_conversation_mode(self):
        """Stop conversation mode"""
        self.conversation_mode = False
        self.on_tts_complete = None
        print("[Voice] ⏹️ Conversation mode DISABLED")
    
    def _listen_once(self):
        """Listen for a single utterance"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.pause_threshold = 0.8
            
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("[Voice] 🎤 Listening...")
                
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    # Trigger speech detected callback (for barge-in)
                    if self.on_speech_detected:
                        self.on_speech_detected()
                    
                    # Transcribe
                    text = self.transcribe(audio_data=audio.get_wav_data())
                    
                    if text and self.on_transcription:
                        self.on_transcription(text)
                        
                except sr.WaitTimeoutError:
                    print("[Voice] ⏱️ Timeout, no speech detected")
                    
        except Exception as e:
            print(f"[Voice] Listen error: {e}")
    
    # ==================== AVAILABLE VOICES ====================
    def get_available_voices(self) -> dict:
        """Return available voices for each language"""
        return VOICE_CONFIG


# ==================== SINGLETON INSTANCE ====================
_ultimate_voice: Optional[UltimateVoice] = None

def get_ultimate_voice() -> UltimateVoice:
    """Get singleton UltimateVoice instance"""
    global _ultimate_voice
    if _ultimate_voice is None:
        _ultimate_voice = UltimateVoice()
    return _ultimate_voice


# ==================== CONVENIENCE FUNCTIONS ====================
async def speak(text: str, **kwargs) -> Optional[str]:
    """Convenience function to speak text"""
    voice = get_ultimate_voice()
    return await voice.speak_async(text, **kwargs)

async def transcribe(audio_path: str = None, audio_data: bytes = None) -> Optional[str]:
    """Convenience function to transcribe audio"""
    voice = get_ultimate_voice()
    return await voice.transcribe_async(audio_path, audio_data)

def interrupt():
    """Convenience function to interrupt TTS"""
    voice = get_ultimate_voice()
    voice.interrupt()


# ==================== TEST ====================
if __name__ == "__main__":
    import asyncio
    
    async def test():
        voice = get_ultimate_voice()
        
        print("\n" + "="*50)
        print("Testing Ultimate Voice Service")
        print("="*50)
        
        # Test English TTS
        print("\n1. Testing English TTS...")
        path = await voice.speak_async("Hello! This is a test of the Ultimate Voice system.")
        if path:
            print(f"   ✅ Audio saved: {path}")
        
        # Test Hindi TTS
        print("\n2. Testing Hindi TTS...")
        path = await voice.speak_async("नमस्ते! यह हिंदी में एक परीक्षण है।", language="hindi")
        if path:
            print(f"   ✅ Audio saved: {path}")
        
        # Test language detection
        print("\n3. Testing Language Detection...")
        tests = [
            "Hello, how are you?",
            "नमस्ते, कैसे हो?",
            "Aap kaise hain bhai?"
        ]
        for t in tests:
            lang = voice.detect_language(t)
            print(f"   '{t[:30]}...' → {lang}")
        
        print("\n" + "="*50)
        print("Tests complete!")
    
    asyncio.run(test())
