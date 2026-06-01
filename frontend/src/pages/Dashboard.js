import React, { useState, useEffect } from 'react';
import StatsCards from '../components/StatsCards';
import LiveCameraFeed from '../components/LiveCameraFeed';
import ViolationTable from '../components/ViolationTable';
import HealthIndicator from '../components/HealthIndicator';
import EventFeed from '../components/EventFeed';
import { fetchStats, fetchViolations, fetchHealth, connectWebSocket } from '../services/api';
import DetectionStats from '../components/DetectionStats';
import AccidentRiskPanel from '../components/AccidentRiskPanel';
import TrafficHeatmap from '../components/TrafficHeatmap';
import DetectedPlates from '../components/DetectedPlates';
import SystemArchLive from '../components/SystemArchLive';

function Dashboard() {
  const [stats, setStats] = useState({});
  const [violations, setViolations] = useState([]);
  const [health, setHealth] = useState({ status: 'loading', score: 0 });
  const [liveEvents, setLiveEvents] = useState([]);
  const [detectionCounts, setDetectionCounts] = useState({});
  const [cameraStats, setCameraStats] = useState({});
  const [accidentRisks, setAccidentRisks] = useState([]);
  const [currentRisk, setCurrentRisk] = useState({ level: 'low', score: 0, active: 0 });

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
    const interval = setInterval(async () => {
      loadData();
      try {
        const res = await fetch('http://localhost:8000/api/camera/stats');
        const data = await res.json();
        setCameraStats(data);
        if (data.detection_counts) setDetectionCounts(data.detection_counts);
      } catch(e) {}
    }, 2000);

    // Connect to live event stream
    const ws = connectWebSocket((event) => {
      setLiveEvents(prev => [event, ...prev].slice(0, 20));
      // Update detection counts from frame updates
      if (event.type === 'frame_update' && event.data?.detection_counts) {
        setDetectionCounts(event.data.detection_counts);
      }
      // Capture accident risks
      if (event.type === 'accident_risk') {
        setAccidentRisks(prev => [event.data, ...prev].slice(0, 10));
        setCurrentRisk({
          level: event.data.level || 'medium',
          score: event.data.score || event.data.risk_score || 0.5,
          active: accidentRisks.length + 1,
        });
      }
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
      
      <StatsCards stats={stats} cameraStats={cameraStats} />
      
      <SystemArchLive />
      
      <div className="grid-2col">
        <LiveCameraFeed />
        <EventFeed events={liveEvents} />
      </div>
      
      <DetectionStats counts={detectionCounts} />
      
      <AccidentRiskPanel risks={accidentRisks} currentRisk={currentRisk} />
      
      <DetectedPlates />
      
      <TrafficHeatmap />
      
      <ViolationTable violations={violations} title="Recent Violations" />
    </div>
  );
}

export default Dashboard;
