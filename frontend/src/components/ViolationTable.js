import React from 'react';

function ViolationTable({ violations = [], title = 'Violations' }) {
  const severityClass = (s) => {
    const map = { critical: 'badge-red', high: 'badge-orange', medium: 'badge-yellow', low: 'badge-green' };
    return map[s] || '';
  };

  const typeIcon = (t) => {
    const map = {
      speed_violation: '🏎️ Speed',
      red_light_violation: '🚦 Red Light',
      lane_violation: '🛣️ Lane',
      parking_violation: '🚫 Parking',
    };
    return map[t] || t;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🚨 {title}</h2>
        <span className="count-badge">{violations.length}</span>
      </div>
      {violations.length === 0 ? (
        <div className="empty-state">No violations recorded yet</div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Vehicle</th>
                <th>Speed</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((v, i) => (
                <tr key={i}>
                  <td>{v.timestamp ? new Date(v.timestamp * 1000).toLocaleTimeString() : '-'}</td>
                  <td>{typeIcon(v.type)}</td>
                  <td><span className={`badge ${severityClass(v.severity)}`}>{v.severity}</span></td>
                  <td>#{v.track_id} ({v.vehicle_class || 'car'})</td>
                  <td>{v.speed ? `${v.speed.toFixed(1)} km/h` : '-'}</td>
                  <td><span className="source-badge">Event Bus</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ViolationTable;
