"""
Frame Processor Module
Preprocesses video frames for optimal AI model inference.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from loguru import logger


class FrameProcessor:
    """
    Handles frame preprocessing operations including:
    - Resizing
    - Normalization
    - Color space conversion
    - Region of Interest (ROI) extraction
    - Frame enhancement
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        normalize: bool = True,
        enhance: bool = False
    ):
        """
        Initialize frame processor.
        
        Args:
            target_size: Target size for model input (width, height)
            normalize: Whether to normalize pixel values to [0, 1]
            enhance: Whether to apply image enhancement
        """
        self.target_size = target_size
        self.normalize = normalize
        self.enhance = enhance
        
        logger.info(f"FrameProcessor initialized: target={target_size}")
    
    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline to a frame.
        
        Args:
            frame: Input BGR frame from OpenCV
            
        Returns:
            Preprocessed frame ready for model inference
        """
        processed = frame.copy()
        
        # Apply enhancement if enabled
        if self.enhance:
            processed = self._enhance_frame(processed)
        
        # Resize to target size
        processed = self.resize(processed, self.target_size)
        
        # Normalize if enabled
        if self.normalize:
            processed = self._normalize(processed)
        
        return processed
    
    def resize(
        self, 
        frame: np.ndarray, 
        size: Tuple[int, int],
        keep_aspect: bool = True
    ) -> np.ndarray:
        """
        Resize frame with optional aspect ratio preservation.
        
        Args:
            frame: Input frame
            size: Target size (width, height)
            keep_aspect: Whether to preserve aspect ratio with padding
            
        Returns:
            Resized frame
        """
        if not keep_aspect:
            return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
        
        # Letterbox resize (preserve aspect ratio with padding)
        h, w = frame.shape[:2]
        target_w, target_h = size
        
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Create padded image
        padded = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
        
        # Center the resized image
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        
        return padded
    
    def extract_roi(
        self, 
        frame: np.ndarray, 
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Extract Region of Interest from frame.
        
        Args:
            frame: Input frame
            roi: Region coordinates (x1, y1, x2, y2)
            
        Returns:
            Cropped ROI frame
        """
        x1, y1, x2, y2 = roi
        h, w = frame.shape[:2]
        
        # Clamp coordinates
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        return frame[y1:y2, x1:x2]
    
    def _normalize(self, frame: np.ndarray) -> np.ndarray:
        """Normalize pixel values to [0, 1] range."""
        return frame.astype(np.float32) / 255.0
    
    def _enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance frame quality for better detection.
        Applies CLAHE for contrast enhancement.
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def denoise(self, frame: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Apply denoising to frame.
        
        Args:
            frame: Input frame
            strength: Denoising strength
            
        Returns:
            Denoised frame
        """
        return cv2.fastNlMeansDenoisingColored(frame, None, strength, strength, 7, 21)
    
    def apply_mask(
        self, 
        frame: np.ndarray, 
        mask_points: list
    ) -> np.ndarray:
        """
        Apply polygon mask to frame (for defining monitoring zones).
        
        Args:
            frame: Input frame
            mask_points: List of (x, y) polygon points
            
        Returns:
            Masked frame
        """
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        points = np.array(mask_points, dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)
        
        return cv2.bitwise_and(frame, frame, mask=mask)
    
    def get_frame_info(self, frame: np.ndarray) -> dict:
        """Get frame metadata."""
        return {
            "height": frame.shape[0],
            "width": frame.shape[1],
            "channels": frame.shape[2] if len(frame.shape) > 2 else 1,
            "dtype": str(frame.dtype),
            "mean_brightness": float(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))),
        }
