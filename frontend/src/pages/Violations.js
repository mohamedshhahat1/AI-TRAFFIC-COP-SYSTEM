import React, { useState, useEffect } from 'react';
import ViolationTable from '../components/ViolationTable';
import { fetchViolations } from '../services/api';

function Violations() {
  const [violations, setViolations] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const load = async () => {
      const data = await fetchViolations(50, filter);
      setViolations(data);
    };
    load();
  }, [filter]);

  return (
    <div className="violations-page">
      <h1>🚨 Violation History</h1>
      <div className="filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="speed_violation">Speed</option>
          <option value="red_light_violation">Red Light</option>
          <option value="lane_violation">Lane</option>
          <option value="parking_violation">Parking</option>
        </select>
      </div>
      <ViolationTable violations={violations} />
    </div>
  );
}

export default Violations;
