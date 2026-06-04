import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';

function MultiCamera() {
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [networkStats, setNetworkStats] = useState({ total: 0, active: 0 });

  useEffect(() => {
    const loadCameras = async () => {
      try {
        const res = await fetch(`${API_BASE}/cameras`);
        const data = await res.json();
        setCameras(data.cameras || []);
        setNetworkStats({ total: data.total || 0, active: data.active || 0 });
      } catch (e) {
        setCameras([
          { id: 'cam_01', location: 'Main Street Intersection', status: 'active', vehicles: 12, congestion: 'heavy', fps: 5.4, coordinates: [30.04, 31.23] },
          { id: 'cam_02', location: 'Highway Exit 5', status: 'active', vehicles: 8, congestion: 'moderate', fps: 5.1, coordinates: [30.06, 31.22] },
          { id: 'cam_03', location: 'School Zone - Al Azhar', status: 'active', vehicles: 4, congestion: 'free', fps: 5.6, coordinates: [30.05, 31.26] },
          { id: 'cam_04', location: 'Downtown Ring Road', status: 'offline', vehicles: 0, congestion: 'unknown', fps: 0, coordinates: [30.05, 31.24] },
        ]);
        setNetworkStats({ total: 4, active: 3 });
      }
    };
    loadCameras();
    const interval = setInterval(loadCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    if (status === 'active') return '#34a853';
    if (status === 'offline') return '#ea4335';
    return '#fbbc04';
  };

  const getCongestionColor = (c) => {
    if (c === 'heavy' || c === 'gridlock') return '#ea4335';
    if (c === 'moderate') return '#fbbc04';
    if (c === 'free') return '#34a853';
    return '#666';
  };

  const getCongestionLabel = (c) => {
    if (c === 'heavy') return 'Heavy Traffic';
    if (c === 'gridlock') return 'Gridlock';
    if (c === 'moderate') return 'Moderate';
    if (c === 'free') return 'Free Flow';
    return 'Unknown';
  };

  const selectedCam = cameras.find((c) => c.id === selectedCamera);
  const activeCameras = cameras.filter((c) => c.status === 'active');
  const totalVehicles = cameras.reduce((sum, c) => sum + (c.vehicles || 0), 0);
  const avgFps = activeCameras.length > 0
    ? (activeCameras.reduce((sum, c) => sum + (c.fps || 0), 0) / activeCameras.length).toFixed(1)
    : 0;

  return (
    <div className="multicamera-page">
      <div className="page-header-row">
        <div>
          <h1>📷 Multi-Camera Network</h1>
          <p className="page-subtitle">Centralized monitoring of all traffic cameras</p>
        </div>
        <div className="view-toggle">
          <button className={viewMode === 'grid' ? 'active' : ''} onClick={() => setViewMode('grid')}>Grid View</button>
          <button className={viewMode === 'list' ? 'active' : ''} onClick={() => setViewMode('list')}>List View</button>
        </div>
      </div>

      {/* Network Overview */}
      <section className="panel">
        <div className="panel-header">
          <h2>🌐 Network Overview</h2>
          <span className="system-pulse active">● LIVE</span>
        </div>
        <div className="network-overview-grid">
          <div className="network-stat-card">
            <span className="network-stat-icon">📷</span>
            <span className="network-stat-value">{networkStats.total}</span>
            <span className="network-stat-label">Total Cameras</span>
          </div>
          <div className="network-stat-card">
            <span className="network-stat-icon" style={{ color: '#34a853' }}>●</span>
            <span className="network-stat-value">{networkStats.active}</span>
            <span className="network-stat-label">Active</span>
          </div>
          <div className="network-stat-card">
            <span className="network-stat-icon" style={{ color: '#ea4335' }}>●</span>
            <span className="network-stat-value">{networkStats.total - networkStats.active}</span>
            <span className="network-stat-label">Offline</span>
          </div>
          <div className="network-stat-card">
            <span className="network-stat-icon">🚗</span>
            <span className="network-stat-value">{totalVehicles}</span>
            <span className="network-stat-label">Vehicles Tracked</span>
          </div>
          <div className="network-stat-card">
            <span className="network-stat-icon">⚡</span>
            <span className="network-stat-value">{avgFps}</span>
            <span className="network-stat-label">Avg FPS</span>
          </div>
          <div className="network-stat-card">
            <span className="network-stat-icon">📡</span>
            <span className="network-stat-value">
              {networkStats.total > 0 ? Math.round((networkStats.active / networkStats.total) * 100) : 0}%
            </span>
            <span className="network-stat-label">Uptime</span>
          </div>
        </div>
      </section>

      {/* Camera Grid / List */}
      {viewMode === 'grid' ? (
        <section className="panel">
          <div className="panel-header">
            <h2>📹 Camera Feeds</h2>
            <span className="count-badge">
              {networkStats.active}/{networkStats.total} active
            </span>
          </div>
          <div className="mc-camera-grid">
            {cameras.map((cam) => (
              <div
                key={cam.id}
                className={`mc-camera-tile ${cam.status} ${selectedCamera === cam.id ? 'selected' : ''}`}
                onClick={() => setSelectedCamera(cam.id === selectedCamera ? null : cam.id)}
              >
                <div className="mc-camera-feed">
                  {cam.status === 'active' ? (
                    selectedCamera === cam.id ? (
                      <img
                        src={`${API_BASE}/camera/feed`}
                        alt={cam.location}
                        className="mc-camera-stream"
                      />
                    ) : (
                      <div className="mc-camera-preview">
                        <span className="mc-camera-icon">📹</span>
                        <span className="mc-vehicle-count">{cam.vehicles} vehicles</span>
                        <span className="mc-fps-badge">{cam.fps} FPS</span>
                      </div>
                    )
                  ) : (
                    <div className="mc-camera-offline">
                      <span className="mc-offline-icon">📵</span>
                      <span>OFFLINE</span>
                    </div>
                  )}
                </div>
                <div className="mc-camera-info">
                  <div className="mc-camera-header">
                    <span className="mc-status-dot" style={{ color: getStatusColor(cam.status) }}>●</span>
                    <span className="mc-camera-id">{cam.id}</span>
                  </div>
                  <span className="mc-camera-location">{cam.location}</span>
                  <div className="mc-camera-stats">
                    <span className="mc-congestion" style={{ color: getCongestionColor(cam.congestion) }}>
                      {getCongestionLabel(cam.congestion)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="panel">
          <div className="panel-header">
            <h2>📹 Camera List</h2>
          </div>
          <div className="mc-camera-table">
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Camera ID</th>
                  <th>Location</th>
                  <th>Vehicles</th>
                  <th>Congestion</th>
                  <th>FPS</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cameras.map((cam) => (
                  <tr key={cam.id} className={cam.status === 'offline' ? 'row-offline' : ''}>
                    <td>
                      <span className="mc-status-dot" style={{ color: getStatusColor(cam.status) }}>●</span>
                      {cam.status}
                    </td>
                    <td className="mc-id-cell">{cam.id}</td>
                    <td>{cam.location}</td>
                    <td>{cam.vehicles}</td>
                    <td>
                      <span style={{ color: getCongestionColor(cam.congestion) }}>
                        {getCongestionLabel(cam.congestion)}
                      </span>
                    </td>
                    <td>{cam.fps}</td>
                    <td>
                      <button
                        className="btn-view-cam"
                        onClick={() => setSelectedCamera(cam.id === selectedCamera ? null : cam.id)}
                        disabled={cam.status !== 'active'}
                      >
                        {selectedCamera === cam.id ? 'Close' : 'View'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Selected Camera Detail */}
      {selectedCam && (
        <section className="panel mc-detail-panel">
          <div className="panel-header">
            <h2>🔍 {selectedCam.id} — {selectedCam.location}</h2>
            <button className="btn-close" onClick={() => setSelectedCamera(null)}>✕</button>
          </div>
          <div className="mc-detail-content">
            <div className="mc-detail-feed">
              {selectedCam.status === 'active' ? (
                <img
                  src={`${API_BASE}/camera/feed`}
                  alt={selectedCam.location}
                  className="mc-detail-stream"
                />
              ) : (
                <div className="mc-camera-offline large">
                  <span className="mc-offline-icon">📵</span>
                  <span>Camera Offline</span>
                </div>
              )}
            </div>
            <div className="mc-detail-info">
              <div className="mc-detail-row">
                <span className="mc-detail-label">Status</span>
                <span style={{ color: getStatusColor(selectedCam.status) }}>
                  {selectedCam.status.toUpperCase()}
                </span>
              </div>
              <div className="mc-detail-row">
                <span className="mc-detail-label">Vehicles</span>
                <span>{selectedCam.vehicles}</span>
              </div>
              <div className="mc-detail-row">
                <span className="mc-detail-label">Congestion</span>
                <span style={{ color: getCongestionColor(selectedCam.congestion) }}>
                  {getCongestionLabel(selectedCam.congestion)}
                </span>
              </div>
              <div className="mc-detail-row">
                <span className="mc-detail-label">FPS</span>
                <span>{selectedCam.fps}</span>
              </div>
              {selectedCam.coordinates && (
                <div className="mc-detail-row">
                  <span className="mc-detail-label">Coordinates</span>
                  <span>{selectedCam.coordinates[0].toFixed(4)}, {selectedCam.coordinates[1].toFixed(4)}</span>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Congestion Map */}
      <section className="panel">
        <div className="panel-header">
          <h2>🗺️ Congestion Overview</h2>
        </div>
        <div className="congestion-summary">
          {cameras.map((cam) => (
            <div key={cam.id} className="congestion-row">
              <span className="mc-status-dot" style={{ color: getStatusColor(cam.status) }}>●</span>
              <span className="congestion-location">{cam.location}</span>
              <div className="congestion-bar-track">
                <div
                  className="congestion-bar-fill"
                  style={{
                    width: cam.congestion === 'heavy' ? '85%'
                      : cam.congestion === 'gridlock' ? '100%'
                      : cam.congestion === 'moderate' ? '50%'
                      : cam.congestion === 'free' ? '15%'
                      : '0%',
                    backgroundColor: getCongestionColor(cam.congestion),
                  }}
                />
              </div>
              <span className="congestion-label" style={{ color: getCongestionColor(cam.congestion) }}>
                {getCongestionLabel(cam.congestion)}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default MultiCamera;
