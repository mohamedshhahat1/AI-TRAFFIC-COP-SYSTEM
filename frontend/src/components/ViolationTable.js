import React from 'react';

function ViolationTable({ violations = [] }) {
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

  if (!violations.length) {
    return <div className="empty-state">No violations recorded yet</div>;
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Vehicle</th>
            <th>Speed</th>
          </tr>
        </thead>
        <tbody>
          {violations.map((v, i) => (
            <tr key={i}>
              <td>{new Date(v.timestamp * 1000).toLocaleTimeString()}</td>
              <td>{typeIcon(v.type)}</td>
              <td><span className={`badge ${severityClass(v.severity)}`}>{v.severity}</span></td>
              <td>#{v.track_id} ({v.vehicle_class})</td>
              <td>{v.speed ? `${v.speed.toFixed(1)} km/h` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ViolationTable;
