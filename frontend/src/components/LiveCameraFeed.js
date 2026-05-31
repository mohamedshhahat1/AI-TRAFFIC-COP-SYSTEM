import React, { useState } from 'react';

function LiveCameraFeed() {
  const [isLive, setIsLive] = useState(false);

  return (
    <div className="camera-panel">
      <div className="panel-header">
        <h2>📷 Live Camera Feed</h2>
        <div>
          <button className="btn btn-success" onClick={() => setIsLive(true)}>▶ Start</button>
          <button className="btn btn-danger" onClick={() => setIsLive(false)}>⬛ Stop</button>
        </div>
      </div>
      <div className="camera-feed">
        {isLive ? (
          <div className="feed-active">
            <span className="live-badge">● LIVE</span>
            <p>Camera feed streaming...</p>
          </div>
        ) : (
          <div className="feed-placeholder">
            <p>📷 Click Start to begin monitoring</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveCameraFeed;
