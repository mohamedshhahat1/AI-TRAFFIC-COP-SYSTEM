import React, { useState, useEffect, useRef } from 'react';
import { startCamera, stopCamera } from '../services/api';

const API_BASE = 'http://localhost:8000/api';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);
  const [status, setStatus] = useState('');
  const [stats, setStats] = useState({ fps: 0, objects: 0, tracks: 0, frame: 0, violations: 0 });
  const [uploading, setUploading] = useState(false);
  const [cameraInfo, setCameraInfo] = useState({});
  const pollRef = useRef(null);
  const fileInputRef = useRef(null);

  // Poll /api/camera/stats every 500ms when live
  useEffect(() => {
    if (isLive) {
      // Fetch camera info once
      fetch(`${API_BASE}/camera/info`).then(r => r.json()).then(setCameraInfo).catch(() => {});
      
      pollRef.current = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/camera/stats`);
          const data = await res.json();
          setStats(data);
        } catch (e) {}
      }, 500);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isLive]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setStatus(`Uploading ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/camera/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.status === 'uploaded') {
        setStatus(`✅ ${file.name} uploaded! Click Start to process.`);
        // Auto-start processing with uploaded video
        const startRes = await startCamera(data.path);
        if (startRes.status === 'started') {
          setIsLive(true);
          setStatus(`🟢 Processing ${file.name}`);
        }
      } else {
        setStatus(`❌ Upload failed: ${data.message || 'Unknown error'}`);
      }
    } catch (err) {
      setStatus(`❌ Upload error: ${err.message}`);
    }
    setUploading(false);
  };

  const handleStart = async () => {
    setStatus('Starting AI pipeline...');
    const result = await startCamera();
    if (result.status === 'started') {
      setIsLive(true);
      setStatus('🟢 Processing video frames');
    } else if (result.status === 'already_running') {
      setIsLive(true);
      setStatus('🟢 Already running');
    } else {
      setStatus(result.message || 'Failed to start');
    }
  };

  const handleStop = async () => {
    await stopCamera();
    setIsLive(false);
    setStats({ fps: 0, objects: 0, tracks: 0, frame: 0, violations: 0 });
    setStatus('Stopped');
    setTimeout(() => setStatus(''), 2000);
  };

  return (
    <div className="camera-panel">
      <div className="panel-header">
        <h2>📷 Live Camera Feed</h2>
        <div className="camera-controls">
          <button className="btn btn-success" onClick={handleStart} disabled={isLive}>▶ Start</button>
          <button className="btn btn-danger" onClick={handleStop} disabled={!isLive}>⬛ Stop</button>
          <button 
            className="btn" 
            onClick={() => fileInputRef.current.click()} 
            disabled={uploading}
            style={{background: '#4285f4', color: '#fff'}}
          >
            📁 Upload Video
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleUpload}
            style={{display: 'none'}}
          />
        </div>
      </div>
      <div className="camera-feed">
        {isLive ? (
          <div className="feed-active">
            <span className="live-badge">● LIVE</span>
            <div className="feed-stats">
              <span>FPS: {stats.fps}</span>
              <span>Objects: {stats.objects}</span>
              <span>Tracked: {stats.tracks}</span>
              <span>Violations: {stats.violations}</span>
            </div>
            <p>Frame #{stats.frame}</p>
            <small style={{color: '#34a853'}}>{status}</small>
            {stats.congestion && (
              <p style={{color: stats.congestion === 'gridlock' ? '#ea4335' : '#fbbc04'}}>
                Congestion: {stats.congestion.toUpperCase()}
              </p>
            )}
            {/* Camera Source Info */}
            <div className="camera-info-bar">
              <span>📹 {cameraInfo.name || 'Unknown'}</span>
              <span>🖥️ {cameraInfo.resolution || '—'}</span>
              <span>🎬 {cameraInfo.fps || 0} FPS</span>
              <span style={{color: cameraInfo.status === 'Connected' ? '#34a853' : '#ea4335'}}>
                ● {cameraInfo.status || 'Disconnected'}
              </span>
            </div>
          </div>
        ) : (
          <div className="feed-placeholder">
            <p>📷 Upload a traffic video or click Start</p>
            <small>Supports: .mp4, .avi, .mkv</small>
            {status && <p style={{color: '#fbbc04', marginTop: 10}}>{status}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
