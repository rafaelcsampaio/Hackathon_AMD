import time
import queue
import threading
import os
import warnings
from collections import deque
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import pygame

# Ignore warnings from Whisper model loading
warnings.filterwarnings("ignore")

class AudioListener:
    """
    Handles continuous background audio recording and voice-to-text transcription.
    Includes voice-activity detection to interrupt the AI when the user speaks.
    """
    
    def __init__(self):
        # Audio configuration constants
        self.THRESHOLD: float = 5.0
        self.SILENCE_LIMIT: float = 1.5  # Seconds of silence to trigger processing
        self.CHANNELS: int = 1
        self.RATE: int = 44100
        
        self.command_queue: queue.Queue = queue.Queue()
        self.is_running: bool = False
        self.is_recording: bool = False
        
        # Cross-reference to the SpeechEngine for queue management
        self.speaker_ref = None 
        
        self._audio_buffer: list = []
        self._pre_buffer = deque(maxlen=25)
        self._silence_start_time: Optional[float] = None
        
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Loads the Whisper model, preferring GPU execution if available."""
        print("[AudioListener] Initializing continuous listening system...")
        try:
            self.whisper_model = whisper.load_model("base", device="cpu")
            print("[AudioListener] Hardware acceleration (GPU) engaged.")
        except Exception:
            self.whisper_model = whisper.load_model("base", device="cpu")
            print("[AudioListener] Warning: Falling back to CPU processing.")

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
        """
        Real-time audio stream callback. Monitors volume and manages the audio buffer.
        """
        if not self.is_running:
            return
            
        volume_norm = np.linalg.norm(indata) * 10
        
        if not self.is_recording:
            self._pre_buffer.append(indata.copy())
            
        # Voice activity detected
        if volume_norm > self.THRESHOLD:
            if not self.is_recording:
                self.is_recording = True
                
                # PLAYBACK INTERRUPTION: User input detected. Interrupt AI speech.
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    print("\n[AudioListener] User input detected. Interrupting AI speech.")
                    
                    # Purge pending audio files from disk and clear the playback queue
                    if getattr(self, 'speaker_ref', None):
                        with self.speaker_ref.audio_queue.mutex:
                            for temp_file in list(self.speaker_ref.audio_queue.queue):
                                try:
                                    if os.path.exists(temp_file):
                                        os.remove(temp_file)
                                except Exception:
                                    pass
                            self.speaker_ref.audio_queue.queue.clear()
            
            self._audio_buffer.extend(self._pre_buffer)
            self._pre_buffer.clear()
            
            self._audio_buffer.append(indata.copy())
            self._silence_start_time = None
            
        # Silence detected while recording
        elif self.is_recording:
            self._audio_buffer.append(indata.copy())
            if self._silence_start_time is None:
                self._silence_start_time = time.time()

    def _recording_loop(self) -> None:
        """
        Background thread loop that manages the audio stream and triggers transcription
        when a command is completed.
        """
        temp_audio_file = "temp_user_command.wav"
        
        with sd.InputStream(callback=self._audio_callback, channels=self.CHANNELS, samplerate=self.RATE):
            while self.is_running:
                if self.is_recording and self._silence_start_time:
                    # Check if silence duration exceeds the limit
                    if (time.time() - self._silence_start_time) > self.SILENCE_LIMIT:
                        
                        # Process the captured audio segment
                        audio_full = np.concatenate(self._audio_buffer, axis=0)
                        self._audio_buffer = []
                        self.is_recording = False
                        self._silence_start_time = None
                        
                        # Save and transcribe
                        write(temp_audio_file, self.RATE, audio_full)
                        transcription_result = self.whisper_model.transcribe(temp_audio_file)
                        text = transcription_result["text"].strip()
                        
                        if text:
                            self.command_queue.put(text)
                            
                time.sleep(0.1)

    def start_listening(self) -> None:
        """Activates the background audio listening thread."""
        self.is_running = True
        threading.Thread(target=self._recording_loop, daemon=True).start()
        
    def stop_listening(self) -> None:
        """Safely deactivates the audio listener."""
        self.is_running = False
        print("[AudioListener] Listening systems deactivated.")

    def get_next_command(self) -> Optional[str]:
        """
        Retrieves the next transcribed voice command from the queue.
        This is a blocking call that waits until a command is available.
        """
        return self.command_queue.get()