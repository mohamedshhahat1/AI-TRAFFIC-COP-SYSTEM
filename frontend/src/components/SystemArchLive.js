import React, { useState, useEffect } from 'react';
import { fetchCameraStats, fetchEventMetrics, fetchHealth, fetchRequestCount } from '../services/api';

function SystemArchLive() {
  const [data, setData] = useState({
    frames: 0,
    events: 0,
    apiRequests: 0,
    avgConfidence: 0,
    uptime: 0,
    totalDetections: 0,
    totalViolations: 0,
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [stats, events, health, requests] = await Promise.all([
          fetchCameraStats(),
          fetchEventMetrics(),
          fetchHealth(),
          fetchRequestCount(),
        ]);

        const inference = health.ai_gateway?.inference || {};

        setData({
          frames: stats.frame || 0,
          events: events.total_emitted || 0,
          apiRequests: requests.total_requests || 0,
          avgConfidence: stats.avg_confidence || 0,
          uptime: inference.uptime_seconds || 0,
          totalDetections: inference.total_inferences || 0,
          totalViolations: events.total_handled || 0,
        });
      } catch (e) {
        console.error('Failed to load system arch data:', e);
      }
    };

    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, []);

  const formatNumber = (n) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return Number(n).toLocaleString();
  };

  const formatUptime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  const items = [
    { icon: '🎞️', label: 'Frames Processed', value: formatNumber(data.frames), color: '#4285f4', pulse: true },
    { icon: '⚡', label: 'Events Generated', value: formatNumber(data.events), color: '#fbbc04', pulse: true },
    { icon: '📡', label: 'API Requests', value: formatNumber(data.apiRequests), color: '#34a853', pulse: true },
    { icon: '🎯', label: 'Avg Detection Confidence', value: `${data.avgConfidence}%`, color: '#ea4335', pulse: false },
    { icon: '⏱️', label: 'System Uptime', value: formatUptime(data.uptime), color: '#9b59b6', pulse: false },
    { icon: '🧠', label: 'AI Inferences', value: formatNumber(data.totalDetections), color: '#00bcd4', pulse: true },
  ];

  return (
    <div className="panel system-arch-panel">
      <div className="panel-header">
        <h2>🏗️ System Architecture Live</h2>
        <span className="system-pulse">● RUNNING</span>
      </div>
      <div className="system-arch-grid">
        {items.map((item, i) => (
          <div key={i} className="system-arch-item">
            <span className="system-arch-icon">{item.icon}</span>
            <div className="system-arch-info">
              <span className="system-arch-value" style={{color: item.color}}>
                {item.value}
                {item.pulse && <span className="counter-pulse" />}
              </span>
              <span className="system-arch-label">{item.label}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="system-arch-flow">
        <span>Camera</span>
        <span className="flow-arrow">→</span>
        <span>YOLOv8</span>
        <span className="flow-arrow">→</span>
        <span>DeepSORT</span>
        <span className="flow-arrow">→</span>
        <span>Violations</span>
        <span className="flow-arrow">→</span>
        <span>Event Bus</span>
        <span className="flow-arrow">→</span>
        <span>Dashboard</span>
      </div>
    </div>
  );
}

export default SystemArchLive;
