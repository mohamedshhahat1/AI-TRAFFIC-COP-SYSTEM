import React from 'react';

function AccidentRiskPanel({ risks = [], currentRisk = {} }) {
  const level = currentRisk.level || 'low';
  const score = currentRisk.score || 0;
  const activeRisks = currentRisk.active || 0;

  const getLevelConfig = (lvl) => {
    const configs = {
      low: { color: '#34a853', bg: 'rgba(52,168,83,0.1)', icon: '✅', text: 'LOW RISK' },
      medium: { color: '#fbbc04', bg: 'rgba(251,188,4,0.1)', icon: '⚠️', text: 'MEDIUM RISK' },
      high: { color: '#ea4335', bg: 'rgba(234,67,53,0.1)', icon: '🚨', text: 'HIGH RISK' },
      imminent: { color: '#ff0000', bg: 'rgba(255,0,0,0.15)', icon: '💀', text: 'IMMINENT DANGER' },
    };
    return configs[lvl] || configs.low;
  };

  const config = getLevelConfig(level);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>⚠️ Accident Risk Prediction</h2>
        <span className="count-badge" style={{background: config.bg, color: config.color}}>
          {activeRisks} active
        </span>
      </div>
      
      <div className="risk-content">
        {/* Main Risk Indicator */}
        <div className="risk-indicator" style={{background: config.bg, borderColor: config.color}}>
          <div className="risk-icon">{config.icon}</div>
          <div className="risk-info">
            <span className="risk-level" style={{color: config.color}}>{config.text}</span>
            <span className="risk-score">Risk Score: {(score * 100).toFixed(0)}%</span>
          </div>
          <div className="risk-gauge">
            <div className="risk-gauge-bg">
              <div 
                className="risk-gauge-fill" 
                style={{width: `${score * 100}%`, background: config.color}}
              />
            </div>
          </div>
        </div>

        {/* Recent Risk Events */}
        {risks.length > 0 ? (
          <div className="risk-events">
            {risks.slice(0, 5).map((risk, i) => {
              const riskConfig = getLevelConfig(risk.level || risk.data?.level || 'medium');
              return (
                <div key={i} className="risk-event-item" style={{borderLeftColor: riskConfig.color}}>
                  <span className="risk-event-icon">{riskConfig.icon}</span>
                  <div className="risk-event-info">
                    <span style={{color: riskConfig.color, fontWeight: 'bold', fontSize: '0.8rem'}}>
                      {(risk.level || risk.data?.level || 'unknown').toUpperCase()}
                    </span>
                    <span className="risk-event-detail">
                      Vehicles: {(risk.vehicles || risk.data?.vehicles || []).join(', ')} 
                      {risk.ttc !== undefined && ` | TTC: ${Number(risk.ttc).toFixed(1)}s`}
                      {risk.data?.ttc !== undefined && ` | TTC: ${Number(risk.data.ttc).toFixed(1)}s`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="risk-empty">
            <p>No collision risks detected</p>
            <small>AI monitors Time-To-Collision (TTC) between vehicles</small>
          </div>
        )}
      </div>
    </div>
  );
}

export default AccidentRiskPanel;
