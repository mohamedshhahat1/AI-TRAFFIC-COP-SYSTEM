import React, { useState, useEffect } from 'react';

function MultiCameraGrid() {
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);

  useEffect(() => {
    // Load camera config from backend
    const loadCameras = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/cameras');
        const data = await res.json();
        setCameras(data.cameras || []);
      } catch (e) {
        // Fallback demo cameras
        setCameras([
          { id: 'cam_01', location: 'Main Street Intersection', status: 'active', vehicles: 12, congestion: 'heavy', fps: 5.4 },
          { id: 'cam_02', location: 'Highway Exit 5', status: 'active', vehicles: 8, congestion: 'moderate', fps: 5.1 },
          { id: 'cam_03', location: 'School Zone - Al Azhar', status: 'active', vehicles: 4, congestion: 'free', fps: 5.6 },
          { id: 'cam_04', location: 'Downtown Ring Road', status: 'offline', vehicles: 0, congestion: 'unknown', fps: 0 },
        ]);
      }
    };
    loadCameras();
    const interval = setInterval(loadCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    return status === 'active' ? '#34a853' : status === 'offline' ? '#ea4335' : '#fbbc04';
  };

  const getCongestionColor = (c) => {
    if (c === 'heavy' || c === 'gridlock') return '#ea4335';
    if (c === 'moderate') return '#fbbc04';
    if (c === 'free') return '#34a853';
    return '#888';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📷 Multi-Camera Network</h2>
        <span className="count-badge">{cameras.filter(c => c.status === 'active').length}/{cameras.length} active</span>
      </div>
      
      <div className="camera-grid">
        {cameras.map((cam, i) => (
          <div 
            key={i} 
            className={`camera-tile ${cam.status} ${selectedCamera === cam.id ? 'selected' : ''}`}
            onClick={() => setSelectedCamera(cam.id === selectedCamera ? null : cam.id)}
          >
            {/* Camera feed thumbnail or placeholder */}
            <div className="camera-tile-feed">
              {cam.status === 'active' ? (
                selectedCamera === cam.id ? (
                  <img 
                    src="http://localhost:8000/api/camera/feed" 
                    alt={cam.location}
                    className="camera-tile-stream"
                  />
                ) : (
                  <div className="camera-tile-preview">
                    <span className="camera-tile-icon">📹</span>
                    <span className="camera-tile-vehicles">{cam.vehicles} vehicles</span>
                  </div>
                )
              ) : (
                <div className="camera-tile-offline">
                  <span>📵</span>
                  <span>OFFLINE</span>
                </div>
              )}
            </div>
            
            {/* Camera info */}
            <div className="camera-tile-info">
              <div className="camera-tile-header">
                <span className="camera-tile-status" style={{color: getStatusColor(cam.status)}}>●</span>
                <span className="camera-tile-id">{cam.id}</span>
              </div>
              <span className="camera-tile-location">{cam.location}</span>
              <div className="camera-tile-stats">
                <span className="camera-tile-congestion" style={{color: getCongestionColor(cam.congestion)}}>
                  {cam.congestion?.toUpperCase()}
                </span>
                {cam.status === 'active' && <span className="camera-tile-fps">{cam.fps} FPS</span>}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Network Summary */}
      <div className="camera-network-summary">
        <div className="network-stat">
          <span className="network-stat-value">{cameras.length}</span>
          <span className="network-stat-label">Total Cameras</span>
        </div>
        <div className="network-stat">
          <span className="network-stat-value" style={{color: '#34a853'}}>{cameras.filter(c => c.status === 'active').length}</span>
          <span className="network-stat-label">Active</span>
        </div>
        <div className="network-stat">
          <span className="network-stat-value" style={{color: '#ea4335'}}>{cameras.filter(c => c.status === 'offline').length}</span>
          <span className="network-stat-label">Offline</span>
        </div>
        <div className="network-stat">
          <span className="network-stat-value">{cameras.reduce((sum, c) => sum + (c.vehicles || 0), 0)}</span>
          <span className="network-stat-label">Total Vehicles</span>
        </div>
      </div>
    </div>
  );
}

export default MultiCameraGrid;
