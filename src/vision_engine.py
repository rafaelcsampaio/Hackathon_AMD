import time
import base64
import threading
from typing import List, Optional
from mss import mss
from io import BytesIO
from PIL import Image

class VisionEngine:
    """
    Handles real-time screen capture and visual context management.
    Runs asynchronously to avoid blocking the main execution thread.
    """
    
    def __init__(self, memory_limit: int = 5):
        self.memory_limit = memory_limit
        self.visual_memory: List[str] = []
        self.is_running: bool = False
        self.vision_thread: Optional[threading.Thread] = None

    def _capture_frame(self) -> Optional[str]:
        """
        Captures the primary monitor, resizes to save tokens, 
        and returns a base64 encoded JPEG string.
        """
        try:
            with mss() as sct:
                # Index 1 usually refers to the primary monitor in mss
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image and resize for token optimization
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img = img.resize((800, 600)) 
                
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=70)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
        except Exception as e:
            print(f"[VisionEngine] Error capturing frame: {e}")
            return None

    def _observation_loop(self) -> None:
        """
        Background loop that continuously updates the visual memory.
        """
        print("[VisionEngine] Optical nerve activated. Observing screen...")
        
        while self.is_running:
            frame = self._capture_frame()
            if frame:
                self.visual_memory.append(frame)
                
                # Maintain FIFO queue for visual memory
                if len(self.visual_memory) > self.memory_limit:
                    self.visual_memory.pop(0)
                    
            # Defines the AI "FPS". 1 frame every 2 seconds is optimal for context/cost.
            time.sleep(2)

    def start_observation(self) -> None:
        """
        Starts the vision background thread.
        """
        self.is_running = True
        self.vision_thread = threading.Thread(target=self._observation_loop, daemon=True)
        self.vision_thread.start()

    def stop_observation(self) -> None:
        """
        Stops the vision background thread safely.
        """
        self.is_running = False
        if self.vision_thread and self.vision_thread.is_alive():
            self.vision_thread.join()
        print("[VisionEngine] Vision systems deactivated.")

    def get_visual_context(self) -> str:
        """
        Returns the most recent frame for the AI model to analyze.
        Returns an empty string if no frame is available.
        """
        if self.visual_memory:
            return self.visual_memory[-1]
        return ""