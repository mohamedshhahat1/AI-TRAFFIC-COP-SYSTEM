import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';

function TrafficHeatmap() {
  const [zones, setZones] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadZones = async () => {
      try {
        const res = await fetch(`${API_BASE}/analytics/heatmap`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.zones && data.zones.length > 0) {
          setZones(data.zones);
          setError(null);
        }
      } catch (e) {
        setError('Unable to load zone data');
      }
    };
    loadZones();
    const interval = setInterval(loadZones, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fallback demo data if backend returns empty
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
      {error && <p style={{color: '#ea4335', fontSize: '0.8em', padding: '0 16px'}}>{error}</p>}
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
