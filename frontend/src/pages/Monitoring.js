import React, { useState, useEffect } from 'react';
import HealthIndicator from '../components/HealthIndicator';
import { fetchHealth, fetchMetrics, fetchLogs, fetchLogStats, fetchEventMetrics } from '../services/api';

function Monitoring() {
  const [health, setHealth] = useState({});
  const [metrics, setMetrics] = useState({});
  const [logs, setLogs] = useState([]);
  const [logStats, setLogStats] = useState({});
  const [eventMetrics, setEventMetrics] = useState({});
  const [logFilter, setLogFilter] = useState({ level: '', component: '' });

  useEffect(() => {
    const load = async () => {
      const [h, m, l, ls, em] = await Promise.all([
        fetchHealth(),
        fetchMetrics(),
        fetchLogs(30, logFilter.level || null, logFilter.component || null),
        fetchLogStats(),
        fetchEventMetrics(),
      ]);
      setHealth(h);
      setMetrics(m);
      setLogs(l.logs || []);
      setLogStats(ls);
      setEventMetrics(em);
    };
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [logFilter]);

  return (
    <div className="monitoring-page">
      <h1>📈 System Monitoring</h1>
      
      {/* Health Section */}
      <section className="panel">
        <h2>❤️ System Health</h2>
        <div className="health-grid">
          <HealthIndicator health={health} large />
          <div className="health-details">
            <p><strong>Status:</strong> {health.status || 'unknown'}</p>
            <p><strong>Score:</strong> {health.score || 0}/100</p>
            <p><strong>Uptime:</strong> {health.uptime_seconds || 0}s</p>
            {health.alerts && health.alerts.length > 0 && (
              <div className="alerts">
                <h4>⚠️ Active Alerts:</h4>
                {health.alerts.map((a, i) => <p key={i} className="alert-item">• {a}</p>)}
              </div>
            )}
          </div>
        </div>
        
        {/* Component Health */}
        {health.components && (
          <div className="components-grid">
            {Object.entries(health.components).map(([name, data]) => (
              <div key={name} className={`component-card ${data.status}`}>
                <h4>{name.replace(/_/g, ' ')}</h4>
                <span className={`status-dot ${data.status}`}>●</span>
                <p>Avg: {data.avg_ms ?? data.avg ?? 0}ms | P95: {data.p95_ms ?? data.p95 ?? 0}ms</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Metrics Section */}
      <section className="panel">
        <h2>⚡ Performance Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>FPS</h3>
            <span className="metric-value">{metrics.fps || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Frame Processing</h3>
            <span className="metric-value">
              {metrics.frame_processing_ms?.avg?.toFixed(1) || 0}ms
            </span>
            <small>p95: {metrics.frame_processing_ms?.p95?.toFixed(1) || 0}ms</small>
          </div>
          <div className="metric-card">
            <h3>Detection</h3>
            <span className="metric-value">
              {metrics.detection_ms?.avg?.toFixed(1) || 0}ms
            </span>
            <small>p95: {metrics.detection_ms?.p95?.toFixed(1) || 0}ms</small>
          </div>
          <div className="metric-card">
            <h3>Total Frames</h3>
            <span className="metric-value">{metrics.total_frames || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Total Events</h3>
            <span className="metric-value">{eventMetrics.total_emitted || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Error Rate</h3>
            <span className="metric-value">{((metrics.error_rate ?? 0) * 100).toFixed(2)}%</span>
          </div>
        </div>
      </section>

      {/* Event Bus Section */}
      <section className="panel">
        <h2>🔥 Event Bus</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Total Emitted</h3>
            <span className="metric-value">{eventMetrics.total_emitted || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Total Handled</h3>
            <span className="metric-value">{eventMetrics.total_handled || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Success Rate</h3>
            <span className="metric-value">{eventMetrics.success_rate || 0}%</span>
          </div>
          <div className="metric-card">
            <h3>Dead Letters</h3>
            <span className="metric-value">{eventMetrics.dead_letters || 0}</span>
          </div>
        </div>
      </section>

      {/* Logs Section */}
      <section className="panel">
        <h2>📝 System Logs</h2>
        <div className="log-filters">
          <select value={logFilter.level} onChange={e => setLogFilter({...logFilter, level: e.target.value})}>
            <option value="">All Levels</option>
            <option value="ERROR">🔴 ERROR</option>
            <option value="WARNING">🟡 WARNING</option>
            <option value="INFO">🔵 INFO</option>
            <option value="DEBUG">⚪ DEBUG</option>
          </select>
          <select value={logFilter.component} onChange={e => setLogFilter({...logFilter, component: e.target.value})}>
            <option value="">All Components</option>
            <option value="pipeline">Pipeline</option>
            <option value="detection">Detection</option>
            <option value="tracking">Tracking</option>
            <option value="violation">Violation</option>
            <option value="prediction">Prediction</option>
          </select>
          <span className="log-count">
            Errors: {logStats.errors || 0} | Warnings: {logStats.warnings || 0}
          </span>
        </div>
        <div className="log-container">
          {logs.length === 0 ? (
            <p className="empty-state">No logs to display</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className={`log-entry log-${log.level?.toLowerCase()}`}>
                <span className="log-time">{log.timestamp?.split('T')[1]?.slice(0,8) || ''}</span>
                <span className={`log-level level-${log.level?.toLowerCase()}`}>{log.level}</span>
                <span className="log-component">[{log.component}]</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

export default Monitoring;
