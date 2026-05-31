import React from 'react';

function HealthIndicator({ health, large = false }) {
  const score = health?.score || 0;
  const status = health?.status || 'unknown';
  
  const getColor = () => {
    if (score >= 80) return '#34a853';
    if (score >= 50) return '#fbbc04';
    return '#ea4335';
  };

  const getIcon = () => {
    if (status === 'healthy') return '💚';
    if (status === 'degraded') return '💛';
    if (status === 'critical') return '❤️‍🔥';
    return '⚪';
  };

  if (large) {
    return (
      <div className="health-large">
        <div className="health-circle" style={{ borderColor: getColor() }}>
          <span className="health-score">{score}</span>
          <span className="health-label">/ 100</span>
        </div>
        <p className="health-status" style={{ color: getColor() }}>
          {getIcon()} {status.toUpperCase()}
        </p>
      </div>
    );
  }

  return (
    <div className="health-badge" style={{ background: getColor() + '22', borderColor: getColor() }}>
      {getIcon()} Health: {score}%
    </div>
  );
}

export default HealthIndicator;
