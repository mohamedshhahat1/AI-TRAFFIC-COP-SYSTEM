import React from 'react';

function DetectionStats({ counts = {} }) {
  const items = [
    { icon: '🚗', label: 'Cars', key: 'car', color: '#4285f4' },
    { icon: '🚛', label: 'Trucks', key: 'truck', color: '#ea4335' },
    { icon: '🏍️', label: 'Motorcycles', key: 'motorcycle', color: '#fbbc04' },
    { icon: '🚌', label: 'Buses', key: 'bus', color: '#9b59b6' },
    { icon: '🚶', label: 'Pedestrians', key: 'person', color: '#34a853' },
    { icon: '🚦', label: 'Traffic Lights', key: 'traffic_light', color: '#ff6b6b' },
    { icon: '🚲', label: 'Bicycles', key: 'bicycle', color: '#00bcd4' },
  ];

  const total = Object.values(counts).reduce((sum, v) => sum + v, 0);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🎯 Vehicle Detection Statistics</h2>
        <span className="count-badge">{total} total</span>
      </div>
      <div className="detection-grid">
        {items.map(item => (
          <div key={item.key} className="detection-item">
            <span className="detection-icon">{item.icon}</span>
            <div className="detection-info">
              <span className="detection-count" style={{color: item.color}}>
                {counts[item.key] || 0}
              </span>
              <span className="detection-label">{item.label}</span>
            </div>
            {total > 0 && (
              <div className="detection-bar">
                <div 
                  className="detection-bar-fill" 
                  style={{
                    width: `${((counts[item.key] || 0) / total) * 100}%`,
                    background: item.color,
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default DetectionStats;
