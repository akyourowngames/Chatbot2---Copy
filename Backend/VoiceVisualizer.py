"""
Reactive Voice Visualizer
=========================
Monitors microphone input and provides real-time volume levels
for the GUI to create reactive animations.
"""

import pyaudio
import numpy as np
import threading
import time

class VoiceVisualizer:
    def __init__(self):
        self.is_running = False
        self.current_volume = 0.0
        self.thread = None
        self.p = None
        self.stream = None
        
    def get_volume(self):
        """Get current normalized volume (0.0 to 1.0)"""
        return min(self.current_volume, 1.0)
    
    def start(self):
        """Start monitoring microphone"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_audio, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                print(f"[VoiceVisualizer] Stream close error: {e}")
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                print(f"[VoiceVisualizer] PyAudio terminate error: {e}")
    
    def _monitor_audio(self):
        """Background thread to monitor audio levels"""
        try:
            self.p = pyaudio.PyAudio()
            
            # Open stream
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            while self.is_running:
                try:
                    # Read audio data
                    data = self.stream.read(1024, exception_on_overflow=False)
                    
                    # Convert to numpy array
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate RMS (Root Mean Square) for volume
                    # Add safety check to prevent invalid values
                    if len(audio_data) > 0:
                        mean_square = np.mean(audio_data.astype(np.float64)**2)
                        if mean_square >= 0 and not np.isnan(mean_square):
                            rms = np.sqrt(mean_square)
                            # Normalize to 0-1 range (adjust 3000 based on your mic sensitivity)
                            self.current_volume = min(rms / 3000.0, 1.0)
                        else:
                            self.current_volume = 0.0
                    else:
                        self.current_volume = 0.0
                    
                    time.sleep(0.05)  # Update 20 times per second
                    
                except Exception as e:
                    # If error, set volume to 0 (silent failure)
                    self.current_volume = 0.0
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Voice Visualizer Error: {e}")
            self.current_volume = 0.0

# Global instance
visualizer = VoiceVisualizer()

if __name__ == "__main__":
    # Test
    visualizer.start()
    try:
        while True:
            vol = visualizer.get_volume()
            bar = "█" * int(vol * 50)
            print(f"\rVolume: {bar:<50} {vol:.2f}", end="")
            time.sleep(0.05)
    except KeyboardInterrupt:
        visualizer.stop()
