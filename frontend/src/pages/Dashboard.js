import React, { useState, useEffect } from 'react';
import StatsCards from '../components/StatsCards';
import LiveCameraFeed from '../components/LiveCameraFeed';
import ViolationTable from '../components/ViolationTable';
import HealthIndicator from '../components/HealthIndicator';
import EventFeed from '../components/EventFeed';
import { fetchStats, fetchViolations, fetchHealth, connectWebSocket } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({});
  const [violations, setViolations] = useState([]);
  const [health, setHealth] = useState({ status: 'loading', score: 0 });
  const [liveEvents, setLiveEvents] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      const [statsData, violData, healthData] = await Promise.all([
        fetchStats(),
        fetchViolations(10),
        fetchHealth(),
      ]);
      setStats(statsData);
      setViolations(violData);
      setHealth(healthData);
    };
    
    loadData();
    const interval = setInterval(loadData, 5000);

    // Connect to live event stream
    const ws = connectWebSocket((event) => {
      setLiveEvents(prev => [event, ...prev].slice(0, 20));
      // Auto-refresh on new violation
      if (event.type === 'violation') {
        loadData();
      }
    });

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>📊 Real-time Traffic Dashboard</h1>
        <HealthIndicator health={health} />
      </div>
      
      <StatsCards stats={stats} />
      
      <div className="grid-2col">
        <LiveCameraFeed />
        <EventFeed events={liveEvents} />
      </div>
      
      <ViolationTable violations={violations} title="Recent Violations" />
    </div>
  );
}

export default Dashboard;
