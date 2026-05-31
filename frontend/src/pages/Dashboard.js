import React, { useState, useEffect } from 'react';
import StatsCards from '../components/StatsCards';
import LiveCameraFeed from '../components/LiveCameraFeed';
import ViolationTable from '../components/ViolationTable';
import { fetchStats, fetchViolations } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({});
  const [violations, setViolations] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      const statsData = await fetchStats();
      const violData = await fetchViolations(10);
      setStats(statsData);
      setViolations(violData);
    };
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <h1>📊 Real-time Traffic Dashboard</h1>
      <StatsCards stats={stats} />
      <div className="grid-2col">
        <LiveCameraFeed />
        <ViolationTable violations={violations} />
      </div>
    </div>
  );
}

export default Dashboard;
