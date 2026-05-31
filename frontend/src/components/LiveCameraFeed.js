import React, { useState } from 'react';
import { startCamera, stopCamera } from '../services/api';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);
  const [status, setStatus] = useState('');
  const [stats, setStats] = useState({ fps: 0, objects: 0 });

  const handleStart = async () => {
    setStatus('Starting...');
    const result = await startCamera();
    if (result.status === 'started' || result.status === 'error') {
      setIsLive(true);
      setStatus(result.message || 'Camera feed active');
    } else {
      setStatus('Failed to start - check backend connection');
    }
  };

  const handleStop = async () => {
    setStatus('Stopping...');
    await stopCamera();
    setIsLive(false);
    setStatus('Camera stopped');
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
            </div>
            <p>AI Pipeline processing frames...</p>
            <small style={{color: '#34a853'}}>{status}</small>
          </div>
        ) : (
          <div className="feed-placeholder">
            <p>📷 Click Start to begin monitoring</p>
            <small>Connects to AI Gateway → Event Bus → Dashboard</small>
            {status && <p style={{color: '#fbbc04', marginTop: 10}}>{status}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
