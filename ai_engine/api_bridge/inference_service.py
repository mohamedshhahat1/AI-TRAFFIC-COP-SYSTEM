"""
Inference Service
Provides a clean API layer between the AI Engine and Backend.
Makes the AI system independent, scalable, and deployable as a microservice.

Architecture:
    Backend → InferenceService → AI Pipeline → Results
    
Benefits:
- AI engine can run on a separate GPU server
- Backend remains lightweight (CPU only)
- Supports async/batch processing
- Easy to scale horizontally
- Clean separation of concerns
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
try:
    logger = SystemLogger("inference_service")
except ImportError:
    from loguru import logger
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

# AIPipeline imported lazily in start() to avoid circular imports
from ..monitoring.logger import SystemLogger
from ..monitoring.metrics import MetricsCollector


class JobStatus(Enum):
    """Inference job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class InferenceJob:
    """Represents a single inference request."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: JobStatus = JobStatus.PENDING
    frame: Optional[np.ndarray] = None
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    results: Optional[Dict] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0


class InferenceService:
    """
    AI Inference Service - Gateway between Backend and AI Engine.
    
    Provides:
    - Synchronous inference (single frame)
    - Asynchronous inference (non-blocking)
    - Batch inference (multiple frames)
    - Job queue management
    - Health monitoring
    - Performance metrics
    
    Usage:
        service = InferenceService(config)
        service.start()
        
        # Sync inference
        results = service.infer(frame)
        
        # Async inference
        job_id = service.submit(frame)
        results = service.get_result(job_id)
        
        # Batch inference
        results = service.infer_batch([frame1, frame2, frame3])
    """
    
    def __init__(self, config: dict = None, max_workers: int = 2):
        """
        Initialize the inference service.
        
        Args:
            config: AI pipeline configuration
            max_workers: Thread pool size for async processing
        """
        self.config = config or {}
        self.max_workers = max_workers
        
        # Monitoring
        self._log = SystemLogger("inference_service")
        self._metrics = MetricsCollector()
        
        # AI Pipeline (the actual brain)
        self._pipeline = None  # Type: Optional[AIPipeline] (lazy imported)
        
        # Job management
        self._job_queue: Queue = Queue(maxsize=100)
        self._jobs: Dict[str, InferenceJob] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # State (thread-safe)
        self._is_running = False
        self._total_inferences = 0
        self._total_time_ms = 0.0
        self._start_time = 0.0
        self._counter_lock = threading.Lock()
        self._max_jobs = 1000  # Prevent unbounded growth
        
        # Callbacks for real-time events
        self._on_violation_callbacks = []
        self._on_accident_risk_callbacks = []
        
        logger.info(f"InferenceService initialized | workers={max_workers}")
    
    def start(self):
        """Start the inference service and load AI models."""
        logger.info("🚀 Starting Inference Service...")
        
        try:
            from ..pipeline import AIPipeline  # Lazy import to avoid circular deps
            self._pipeline = AIPipeline(self.config)
            self._is_running = True
            self._start_time = time.time()
            logger.info("✅ Inference Service ready")
        except Exception as e:
            logger.error(f"Failed to start inference service: {e}")
            raise
    
    def stop(self):
        """Stop the inference service and release resources."""
        self._is_running = False
        self._executor.shutdown(wait=False)
        self._pipeline = None
        logger.info("🛑 Inference Service stopped")
    
    # ==================== Synchronous API ====================
    
    def infer(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Run synchronous inference on a single frame.
        Blocks until processing is complete.
        
        Args:
            frame: BGR image (numpy array)
            
        Returns:
            Dictionary with detection, tracking, violation results
        """
        if not self._is_running or self._pipeline is None:
            return {"error": "Service not running"}
        
        t_start = time.time()
        
        try:
            results = self._pipeline.process_frame(frame)
            
            proc_time = (time.time() - t_start) * 1000
            with self._counter_lock:
                self._total_inferences += 1
                self._total_time_ms += proc_time
            
            # Trigger callbacks for violations
            if results.get("violations"):
                self._notify_violations(results["violations"])
            
            if results.get("accident_risks"):
                self._notify_accident_risks(results["accident_risks"])
            
            # Format response
            return self._format_response(results, proc_time)
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {"error": str(e), "processing_time_ms": 0}
    
    def infer_batch(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Run inference on multiple frames.
        
        Args:
            frames: List of BGR images
            
        Returns:
            List of result dictionaries
        """
        results = []
        for frame in frames:
            result = self.infer(frame)
            results.append(result)
        return results
    
    # ==================== Asynchronous API ====================
    
    def submit(self, frame: np.ndarray, source: str = "") -> str:
        """
        Submit a frame for async inference.
        Returns immediately with a job ID.
        
        Args:
            frame: BGR image
            source: Source identifier (camera ID, etc.)
            
        Returns:
            Job ID string
        """
        job = InferenceJob(frame=frame, source=source)
        self._jobs[job.job_id] = job
        
        # Submit to thread pool
        self._executor.submit(self._process_job, job)
        
        return job.job_id
    
    def get_result(self, job_id: str) -> Optional[Dict]:
        """
        Get the result of an async job.
        
        Args:
            job_id: Job identifier from submit()
            
        Returns:
            Results dict if completed, None if still processing
        """
        job = self._jobs.get(job_id)
        if job is None:
            return {"error": "Job not found"}
        
        if job.status == JobStatus.COMPLETED:
            return job.results
        elif job.status == JobStatus.FAILED:
            return {"error": job.error}
        else:
            return None  # Still processing
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get status of an inference job."""
        job = self._jobs.get(job_id)
        if job is None:
            return {"error": "Job not found"}
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "source": job.source,
            "submitted_at": job.timestamp,
            "processing_time_ms": job.processing_time_ms,
        }
    
    def _process_job(self, job: InferenceJob):
        """Process a single inference job (runs in thread pool)."""
        job.status = JobStatus.PROCESSING
        t_start = time.time()
        
        try:
            if job.frame is not None and self._pipeline is not None:
                results = self._pipeline.process_frame(job.frame)
                job.results = self._format_response(results, 0)
                job.status = JobStatus.COMPLETED
            else:
                job.error = "Invalid frame or pipeline not ready"
                job.status = JobStatus.FAILED
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            logger.error(f"Job {job.job_id} failed: {e}")
        
        job.processing_time_ms = (time.time() - t_start) * 1000
        with self._counter_lock:
            self._total_inferences += 1
            self._total_time_ms += job.processing_time_ms
        
        # Cleanup old completed jobs (prevent memory leak)
        if len(self._jobs) > self._max_jobs:
            completed = [jid for jid, j in self._jobs.items() 
                        if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)]
            for jid in completed[:len(completed)//2]:
                del self._jobs[jid]
    
    # ==================== Stream API ====================
    
    def process_stream(self, frame_generator, callback=None):
        """
        Process a continuous stream of frames.
        
        Args:
            frame_generator: Generator yielding (frame, timestamp) tuples
            callback: Function called with results for each frame
        """
        if not self._is_running:
            logger.error("Service not running")
            return
        
        for frame, ts in frame_generator:
            results = self.infer(frame)
            if callback:
                callback(results)
    
    # ==================== Event Callbacks ====================
    
    def on_violation(self, callback):
        """Register callback for violation events."""
        self._on_violation_callbacks.append(callback)
    
    def on_accident_risk(self, callback):
        """Register callback for accident risk events."""
        self._on_accident_risk_callbacks.append(callback)
    
    def _notify_violations(self, violations: list):
        """Notify registered callbacks about new violations."""
        for cb in self._on_violation_callbacks:
            try:
                for v in violations:
                    cb(v.to_dict())
            except Exception as e:
                logger.error(f"Violation callback error: {e}")
    
    def _notify_accident_risks(self, risks: list):
        """Notify registered callbacks about accident risks."""
        for cb in self._on_accident_risk_callbacks:
            try:
                for r in risks:
                    cb(r)
            except Exception as e:
                logger.error(f"Risk callback error: {e}")
    
    # ==================== Utility ====================
    
    def _format_response(self, results: Dict, proc_time: float) -> Dict:
        """Format pipeline results into a clean API response."""
        tracks = results.get("tracks", [])
        violations = results.get("violations", [])
        congestion = results.get("congestion")
        risks = results.get("accident_risks", [])
        
        return {
            "frame_number": results.get("frame_number", 0),
            "processing_time_ms": round(proc_time, 1),
            "detections": {
                "count": results["stats"]["detected_objects"],
                "objects": [
                    {
                        "class": d.class_name,
                        "confidence": round(d.confidence, 2),
                        "bbox": d.bbox,
                    }
                    for d in results.get("detections", [])[:20]
                ],
            },
            "tracking": {
                "active_vehicles": len(tracks),
                "vehicles": [t.to_dict() for t in tracks[:30]],
            },
            "violations": {
                "new_count": len(violations),
                "items": [v.to_dict() for v in violations],
            },
            "congestion": {
                "level": congestion.level if congestion else "unknown",
                "density": congestion.density if congestion else 0,
                "avg_speed": congestion.avg_speed if congestion else 0,
                "prediction": congestion.prediction if congestion else "stable",
            },
            "accident_risks": {
                "count": len(risks),
                "items": [
                    {
                        "level": r.risk_level,
                        "score": r.risk_score,
                        "vehicles": r.involved_vehicles,
                        "ttc": r.time_to_collision,
                        "description": r.description,
                    }
                    for r in risks
                ],
            },
        }
    
    # ==================== Monitoring ====================
    
    def health(self) -> Dict:
        """Get service health status."""
        return {
            "status": "healthy" if self._is_running else "stopped",
            "pipeline_loaded": self._pipeline is not None,
            "uptime_seconds": round(time.time() - self._start_time, 1) if self._start_time else 0,
            "total_inferences": self._total_inferences,
            "avg_latency_ms": round(
                self._total_time_ms / self._total_inferences, 1
            ) if self._total_inferences > 0 else 0,
            "pending_jobs": sum(
                1 for j in self._jobs.values() if j.status == JobStatus.PENDING
            ),
            "max_workers": self.max_workers,
        }
    
    def metrics(self) -> Dict:
        """Get detailed performance metrics."""
        pipeline_summary = self._pipeline.get_summary() if self._pipeline else {}
        
        return {
            "service": self.health(),
            "pipeline": pipeline_summary,
            "throughput_fps": round(
                self._total_inferences / (time.time() - self._start_time), 1
            ) if self._start_time and (time.time() - self._start_time) > 0 else 0,
        }
    
    def reset_metrics(self):
        """Reset performance counters."""
        self._total_inferences = 0
        self._total_time_ms = 0.0
        self._start_time = time.time()
    
    # ==================== Context Manager ====================
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
