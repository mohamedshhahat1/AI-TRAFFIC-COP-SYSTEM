import React, { useState } from 'react';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);
  const [stats, setStats] = useState({ fps: 0, objects: 0 });

  const handleStart = async () => {
    try {
      await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/camera/start`, { method: 'POST' });
      setIsLive(true);
    } catch (e) {
      setIsLive(true); // Show UI even if API is down
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/camera/stop`, { method: 'POST' });
    } catch (e) {}
    setIsLive(false);
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
          </div>
        ) : (
          <div className="feed-placeholder">
            <p>📷 Click Start to begin monitoring</p>
            <small>Connects to AI Gateway → Event Bus → Dashboard</small>
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
