import React from 'react';

function StatsCards({ stats }) {
  const cards = [
    { icon: '🚗', label: 'Vehicles Tracked', value: stats.total_vehicles || 0 },
    { icon: '🚨', label: 'Total Violations', value: stats.total_violations || 0, cls: 'warning' },
    { icon: '⚡', label: 'Avg Speed', value: `${stats.avg_speed || 0} km/h`, cls: 'info' },
    { icon: '🚦', label: 'Congestion', value: stats.congestion_level || 'Free', cls: 'success' },
    { icon: '🔥', label: 'Events/sec', value: stats.events_per_second || 0, cls: 'info' },
    { icon: '❤️', label: 'Health', value: `${stats.health_score || 100}%`, cls: stats.health_score < 80 ? 'warning' : 'success' },
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
