import React, { useState, useEffect, useRef } from 'react';
import { startCamera, stopCamera } from '../services/api';

const API_BASE = '/api';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);
  const [status, setStatus] = useState('');
  const [stats, setStats] = useState({ fps: 0, objects: 0, tracks: 0, frame: 0, violations: 0 });
  const pollRef = useRef(null);

  // Poll /api/camera/stats every 500ms when live
  useEffect(() => {
    if (isLive) {
      pollRef.current = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/camera/stats`);
          const data = await res.json();
          setStats(data);
          if (!data.running) {
            setStatus('Video ended');
          }
        } catch (e) {}
      }, 500);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isLive]);

  const handleStart = async () => {
    setStatus('Starting AI pipeline...');
    const result = await startCamera();
    if (result.status === 'started') {
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
          </div>
        ) : (
          <div className="feed-placeholder">
            <p>📷 Click Start to begin monitoring</p>
            <small>AI Gateway → YOLOv8 → Event Bus → Dashboard</small>
            {status && <p style={{color: '#fbbc04', marginTop: 10}}>{status}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
