import React, { useState, useEffect, useRef } from 'react';
import { startCamera, stopCamera, fetchCameraStats, fetchCameraInfo, API_BASE } from '../services/api';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);
  const [status, setStatus] = useState('');
  const [stats, setStats] = useState({ fps: 0, objects: 0, tracks: 0, frame: 0, violations: 0 });
  const [uploading, setUploading] = useState(false);
  const [cameraInfo, setCameraInfo] = useState({});
  const pollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isLive) {
      fetchCameraInfo().then(setCameraInfo);

      pollRef.current = setInterval(async () => {
        const data = await fetchCameraStats();
        setStats(data);
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
      const res = await fetch(`${API_BASE}/camera/upload`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.status === 'uploaded') {
        const startRes = await startCamera(data.path);
        if (startRes.status === 'started') {
          setIsLive(true);
          setStatus(`🟢 Processing ${file.name}`);
        }
      } else {
        setStatus(`❌ ${data.message || 'Upload failed'}`);
      }
    } catch (err) {
      setStatus(`❌ Upload error: ${err.message}`);
    }
    setUploading(false);
  };

  const handleStart = async () => {
    setStatus('Starting AI pipeline...');
    const result = await startCamera();
    if (result.status === 'started' || result.status === 'already_running') {
      setIsLive(true);
      setStatus('🟢 Processing video frames');
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
            {/* MJPEG Video Stream with bounding boxes */}
            <img
              src={`${API_BASE}/camera/feed`}
              alt="AI Traffic Detection"
              className="video-stream"
            />
            {/* Overlay stats */}
            <div className="feed-overlay">
              <span className="live-badge">● LIVE</span>
              <div className="feed-stats-overlay">
                <span>FPS: {stats.fps}</span>
                <span>Objects: {stats.objects}</span>
                <span>Tracked: {stats.tracks}</span>
                <span>Violations: {stats.violations}</span>
                <span>Frame: #{stats.frame}</span>
              </div>
            </div>
            {/* Camera info bar */}
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
            <small>AI will show: Bounding Boxes • Vehicle IDs • Speed • Violations</small>
            {status && <p style={{color: '#fbbc04', marginTop: 10}}>{status}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
