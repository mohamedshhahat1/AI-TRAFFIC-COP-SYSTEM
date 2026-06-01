import React from 'react';

function StatsCards({ stats, cameraStats = {} }) {
  const cards = [
    { icon: '🚗', label: 'Vehicles Tracked', value: cameraStats.tracks || stats.total_vehicles || 0 },
    { icon: '🚨', label: 'Total Violations', value: cameraStats.violations || stats.total_violations || 0, cls: 'warning' },
    { icon: '⚡', label: 'Avg Speed', value: `${cameraStats.avg_speed || stats.avg_speed || 0} km/h`, cls: 'info' },
    { icon: '🚦', label: 'Congestion', value: (cameraStats.congestion || stats.congestion_level || 'free').toUpperCase(), cls: 'success' },
    { icon: '🔥', label: 'Events/sec', value: cameraStats.fps || 0, cls: 'info' },
    { icon: '❤️', label: 'Health', value: `${cameraStats.health_score || 100}%`, cls: cameraStats.health_score < 80 ? 'warning' : 'success' },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <div key={i} className={`stat-card ${card.cls || ''}`}>
          <span className="stat-icon">{card.icon}</span>
          <div>
            <h3>{card.value}</h3>
            <p>{card.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default StatsCards;
