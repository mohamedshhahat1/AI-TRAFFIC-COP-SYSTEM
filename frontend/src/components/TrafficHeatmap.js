import React from 'react';

function TrafficHeatmap({ zones = [] }) {
  // Default zones if none provided (simulated from multi-camera data)
  const defaultZones = [
    { name: 'Main Street Intersection', congestion: 85, vehicles: 34, status: 'heavy' },
    { name: 'Highway Exit 5', congestion: 63, vehicles: 21, status: 'moderate' },
    { name: 'School Zone - Al Azhar', congestion: 42, vehicles: 12, status: 'moderate' },
    { name: 'Downtown Ring Road', congestion: 28, vehicles: 8, status: 'free' },
    { name: 'Industrial Area Gate', congestion: 15, vehicles: 4, status: 'free' },
  ];

  const displayZones = zones.length > 0 ? zones : defaultZones;

  const getColor = (pct) => {
    if (pct >= 80) return '#ea4335';
    if (pct >= 60) return '#fbbc04';
    if (pct >= 40) return '#ff9800';
    return '#34a853';
  };

  const getStatusIcon = (status) => {
    const icons = {
      gridlock: '🔴',
      heavy: '🟠',
      moderate: '🟡',
      free: '🟢',
    };
    return icons[status] || '⚪';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🗺️ Top Congested Zones</h2>
        <span className="count-badge">{displayZones.length} zones</span>
      </div>
      <div className="heatmap-content">
        {displayZones.map((zone, i) => (
          <div key={i} className="heatmap-row">
            <div className="heatmap-rank">#{i + 1}</div>
            <div className="heatmap-info">
              <div className="heatmap-name">
                {getStatusIcon(zone.status)} {zone.name}
              </div>
              <div className="heatmap-bar-container">
                <div 
                  className="heatmap-bar" 
                  style={{
                    width: `${zone.congestion}%`,
                    background: `linear-gradient(90deg, ${getColor(zone.congestion)}88, ${getColor(zone.congestion)})`,
                  }}
                />
              </div>
            </div>
            <div className="heatmap-stats">
              <span className="heatmap-pct" style={{color: getColor(zone.congestion)}}>
                {zone.congestion}%
              </span>
              <span className="heatmap-vehicles">{zone.vehicles} vehicles</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TrafficHeatmap;
