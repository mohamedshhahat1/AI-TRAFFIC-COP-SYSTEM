import React, { useState, useEffect } from 'react';
import ViolationTable from '../components/ViolationTable';
import PlateViolationTable from '../components/PlateViolationTable';
import { fetchViolations, fetchEventHistory } from '../services/api';

function Violations() {
  const [violations, setViolations] = useState([]);
  const [eventHistory, setEventHistory] = useState([]);
  const [filter, setFilter] = useState('');
  const [severity, setSeverity] = useState('');

  useEffect(() => {
    const load = async () => {
      const data = await fetchViolations(50, filter, severity);
      const events = await fetchEventHistory('violation.*', 20);
      setViolations(data);
      setEventHistory(events);
    };
    load();
  }, [filter, severity]);

  return (
    <div className="violations-page">
      <h1>🚨 Violation History</h1>
      
      <div className="filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="speed_violation">🏎️ Speed</option>
          <option value="red_light_violation">🚦 Red Light</option>
          <option value="lane_violation">🛣️ Lane</option>
          <option value="parking_violation">🚫 Parking</option>
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All Severity</option>
          <option value="critical">🔴 Critical</option>
          <option value="high">🟠 High</option>
          <option value="medium">🟡 Medium</option>
          <option value="low">🟢 Low</option>
        </select>
      </div>
      
      <ViolationTable violations={violations} title="All Violations" />
      
      <PlateViolationTable />
      
      {/* Event History */}
      <div className="panel">
        <div className="panel-header">
          <h2>🔥 Violation Events (from Event Bus)</h2>
        </div>
        <div className="event-history">
          {eventHistory.length === 0 ? (
            <p className="empty-state">No violation events in history</p>
          ) : (
            eventHistory.map((evt, i) => (
              <div key={i} className="event-history-item">
                <span className="event-topic">{evt.topic}</span>
                <span className="event-payload">{JSON.stringify(evt.payload || {}).slice(0, 80)}</span>
                <span className="event-time">
                  {evt.timestamp ? new Date(evt.timestamp * 1000).toLocaleTimeString() : ''}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default Violations;
