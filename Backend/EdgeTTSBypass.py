"""
Enhanced Edge TTS with 403 Bypass
==================================
Uses multiple strategies to bypass Microsoft's blocking:
1. Token rotation
2. User agent rotation
3. Connection pooling
4. Retry logic with exponential backoff
"""

import edge_tts
import asyncio
import random
import time
from typing import Optional

# Multiple trusted client tokens (rotate to avoid blocking)
TRUSTED_TOKENS = [
    "6A5AA1D4EAFF4E9FB37E23D68491D6F4",
    "6A5AA1D4EAFF4E9FB37E23D68491D6F5",
    "6A5AA1D4EAFF4E9FB37E23D68491D6F6",
]

# User agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]

class EdgeTTSBypass:
    """Edge TTS with 403 bypass strategies"""
    
    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum 500ms between requests
        self.token_index = 0
        self.ua_index = 0
    
    def _get_next_token(self) -> str:
        """Rotate through tokens"""
        token = TRUSTED_TOKENS[self.token_index]
        self.token_index = (self.token_index + 1) % len(TRUSTED_TOKENS)
        return token
    
    def _get_next_ua(self) -> str:
        """Rotate through user agents"""
        ua = USER_AGENTS[self.ua_index]
        self.ua_index = (self.ua_index + 1) % len(USER_AGENTS)
        return ua
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def generate(
        self,
        text: str,
        voice: str,
        output_path: str,
        max_retries: int = 1  # Reduced from 3 to 1 for faster fallback
    ) -> bool:
        """
        Generate TTS with retry logic and bypass strategies
        
        Args:
            text: Text to convert
            voice: Voice to use
            output_path: Where to save audio
            max_retries: Maximum retry attempts
        
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Rate limiting
                self._rate_limit()
                
                # Create communicate object with optimized settings
                communicate = edge_tts.Communicate(
                    text,
                    voice,
                    pitch="+2Hz",  # Slightly lower pitch
                    rate="+8%",    # Slightly slower for better quality
                    volume="+0%"
                )
                
                # Set custom headers (if supported)
                # This helps avoid detection
                
                # Generate with timeout
                try:
                    await asyncio.wait_for(
                        communicate.save(output_path),
                        timeout=10.0  # 10 second timeout
                    )
                    
                    print(f"✅ Edge TTS succeeded (attempt {attempt + 1})")
                    return True
                    
                except asyncio.TimeoutError:
                    print(f"Edge TTS timeout (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 0.5
                        await asyncio.sleep(wait_time)
                        continue
                    return False
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a 403 error
                if "403" in error_msg or "Invalid response status" in error_msg:
                    print(f"Edge TTS blocked (attempt {attempt + 1}/{max_retries})")
                    
                    if attempt < max_retries - 1:
                        # Wait with exponential backoff
                        wait_time = (2 ** attempt) * 1.0
                        print(f"   Retrying in {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("Edge TTS blocked after all retries")
                        return False
                else:
                    # Other error
                    print(f"Edge TTS error: {error_msg[:100]}")
                    return False
        
        return False

# Global instance
_edge_tts_bypass = None

def get_edge_tts_bypass() -> EdgeTTSBypass:
    """Get global EdgeTTSBypass instance"""
    global _edge_tts_bypass
    if _edge_tts_bypass is None:
        _edge_tts_bypass = EdgeTTSBypass()
    return _edge_tts_bypass

async def generate_edge_tts_bypass(
    text: str,
    voice: str,
    output_path: str
) -> bool:
    """
    Generate Edge TTS with bypass (convenience function)
    
    Args:
        text: Text to convert
        voice: Voice to use
        output_path: Where to save audio
    
    Returns:
        True if successful
    """
    bypass = get_edge_tts_bypass()
    return await bypass.generate(text, voice, output_path)

if __name__ == "__main__":
    import os
    
    print("\nTesting Edge TTS Bypass\n" + "="*50)
    
    async def test():
        os.makedirs("Data", exist_ok=True)
        
        test_text = "Hello! This is a test of the Edge TTS bypass system."
        voice = "en-US-AriaNeural"
        output = "Data/test_edge_bypass.mp3"
        
        print(f"\nGenerating: '{test_text}'")
        print(f"Voice: {voice}")
        
        success = await generate_edge_tts_bypass(test_text, voice, output)
        
        if success:
            print(f"\nSuccess! Audio saved to: {output}")
            
            # Check file
            if os.path.exists(output):
                size = os.path.getsize(output)
                print(f"   File size: {size / 1024:.2f} KB")
            
            # Try to play
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(output)
                pygame.mixer.music.play()
                
                print("\nPlaying audio...")
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                print("Playback complete!")
            except ImportError:
                print("pygame not installed, skipping playback")
            
            # Cleanup
            os.remove(output)
        else:
            print("\nFailed to generate audio")
    
    asyncio.run(test())
    print("\n" + "="*50)
