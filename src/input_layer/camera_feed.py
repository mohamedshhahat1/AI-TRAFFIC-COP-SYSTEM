"""
Camera Feed Module
Manages video input from multiple sources: RTSP, video files, webcam.
"""

import cv2
import numpy as np
from typing import Optional, Generator, Tuple
from loguru import logger
import threading
import queue
import time


class CameraFeed:
    """
    Handles video capture from various sources with buffering and error recovery.
    
    Supports:
    - Local video files (.mp4, .avi, .mkv)
    - RTSP streams (IP cameras)
    - USB webcams (device index)
    """
    
    def __init__(
        self,
        source: str = "0",
        resolution: Tuple[int, int] = (1280, 720),
        fps: int = 30,
        buffer_size: int = 10
    ):
        """
        Initialize camera feed.
        
        Args:
            source: Video source - file path, RTSP URL, or camera index
            resolution: Target resolution (width, height)
            fps: Target frames per second
            buffer_size: Frame buffer size for smooth processing
        """
        self.source = source
        self.resolution = resolution
        self.fps = fps
        self.buffer_size = buffer_size
        
        self.capture: Optional[cv2.VideoCapture] = None
        self.frame_buffer: queue.Queue = queue.Queue(maxsize=buffer_size)
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info(f"CameraFeed initialized with source: {source}")
    
    def start(self) -> bool:
        """
        Start the camera feed capture.
        
        Returns:
            True if successfully started, False otherwise
        """
        try:
            # Determine source type
            if self.source.isdigit():
                source = int(self.source)
            else:
                source = self.source
            
            self.capture = cv2.VideoCapture(source)
            
            if not self.capture.isOpened():
                logger.error(f"Failed to open video source: {self.source}")
                return False
            
            # Set capture properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # Get actual properties
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            logger.info(
                f"Camera started: {actual_width}x{actual_height} @ {actual_fps}fps"
            )
            
            self.is_running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False
    
    def stop(self):
        """Stop the camera feed and release resources."""
        self.is_running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # Clear buffer
        while not self.frame_buffer.empty():
            try:
                self.frame_buffer.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Camera feed stopped")
    
    def _capture_loop(self):
        """Background thread for continuous frame capture."""
        frame_interval = 1.0 / self.fps
        
        while self.is_running:
            start_time = time.time()
            
            with self._lock:
                if self.capture is None or not self.capture.isOpened():
                    logger.warning("Camera disconnected, attempting reconnect...")
                    self._reconnect()
                    continue
                
                ret, frame = self.capture.read()
            
            if not ret:
                if self._is_video_file():
                    logger.info("Video file ended")
                    self.is_running = False
                    break
                else:
                    logger.warning("Frame capture failed, retrying...")
                    time.sleep(0.1)
                    continue
            
            # Resize frame if needed
            if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
                frame = cv2.resize(frame, self.resolution)
            
            # Add timestamp
            timestamp = time.time()
            
            # Put frame in buffer (drop oldest if full)
            if self.frame_buffer.full():
                try:
                    self.frame_buffer.get_nowait()
                except queue.Empty:
                    pass
            
            self.frame_buffer.put((frame, timestamp))
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def read_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """
        Read the next frame from the buffer.
        
        Returns:
            Tuple of (frame, timestamp) or None if no frame available
        """
        try:
            return self.frame_buffer.get(timeout=1.0)
        except queue.Empty:
            return None
    
    def get_frames(self) -> Generator[Tuple[np.ndarray, float], None, None]:
        """
        Generator that yields frames continuously.
        
        Yields:
            Tuple of (frame, timestamp)
        """
        while self.is_running:
            result = self.read_frame()
            if result is not None:
                yield result
    
    def _reconnect(self, max_attempts: int = 5):
        """Attempt to reconnect to the video source."""
        for attempt in range(max_attempts):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}")
            
            if self.capture:
                self.capture.release()
            
            source = int(self.source) if self.source.isdigit() else self.source
            self.capture = cv2.VideoCapture(source)
            
            if self.capture.isOpened():
                logger.info("Reconnection successful")
                return
            
            time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Failed to reconnect after all attempts")
        self.is_running = False
    
    def _is_video_file(self) -> bool:
        """Check if source is a video file."""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        return any(self.source.lower().endswith(ext) for ext in video_extensions)
    
    def get_info(self) -> dict:
        """Get camera/video information."""
        if not self.capture:
            return {}
        
        return {
            "source": self.source,
            "width": int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.capture.get(cv2.CAP_PROP_FPS)),
            "frame_count": int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            "is_running": self.is_running,
            "buffer_size": self.frame_buffer.qsize(),
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __del__(self):
        """Destructor to ensure resources are released."""
        self.stop()
