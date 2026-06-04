import React, { useState, useEffect } from 'react';
import {
  fetchRLStatus, startRL, stopRL, fetchRLMetrics,
  fetchRLMetricsHistory, fetchRLControllerState,
  fetchRLControllerStats, fetchRLModels, loadRLModel,
  resetRLStats, setRLManualPhase,
} from '../services/api';

const PHASE_LABELS = [
  { name: 'North-South Through', directions: ['N', 'S'], icon: '↕️' },
  { name: 'North-South Left', directions: ['N←', 'S→'], icon: '↩️' },
  { name: 'East-West Through', directions: ['E', 'W'], icon: '↔️' },
  { name: 'East-West Left', directions: ['E←', 'W→'], icon: '↪️' },
];

function RLSignalControl() {
  const [status, setStatus] = useState({ running: false });
  const [metrics, setMetrics] = useState({});
  const [controllerState, setControllerState] = useState({});
  const [controllerStats, setControllerStats] = useState({});
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [models, setModels] = useState([]);
  const [config, setConfig] = useState({
    agent_type: 'dqn',
    decision_interval: 5.0,
    control_mode: 'simulated',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadAll = async () => {
    try {
      const [s, m, cs, cst, mh, mdl] = await Promise.all([
        fetchRLStatus(),
        fetchRLMetrics(),
        fetchRLControllerState(),
        fetchRLControllerStats(),
        fetchRLMetricsHistory(50),
        fetchRLModels(),
      ]);
      setStatus(s);
      setMetrics(m);
      setControllerState(cs);
      setControllerStats(cst);
      setMetricsHistory(mh.metrics || []);
      setModels(mdl.models || []);
      setError(null);
    } catch (e) {
      setError('Failed to connect to RL backend');
    }
  };

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    const res = await startRL(config);
    if (res.status === 'error') setError(res.message);
    else setError(null);
    await loadAll();
    setLoading(false);
  };

  const handleStop = async () => {
    setLoading(true);
    await stopRL();
    await loadAll();
    setLoading(false);
  };

  const handleReset = async () => {
    await resetRLStats();
    await loadAll();
  };

  const handlePhaseClick = async (phase) => {
    const res = await setRLManualPhase(phase);
    if (res.accepted) await loadAll();
  };

  const handleLoadModel = async (model) => {
    setLoading(true);
    const agentType = model.name.includes('ppo') ? 'ppo' : 'dqn';
    const path = model.has_best
      ? `${model.path}/best_model.pt`
      : `${model.path}/final_model.pt`;
    await loadRLModel(agentType, path);
    await loadAll();
    setLoading(false);
  };

  const isRunning = status.running;
  const signalState = controllerState.signal_state || 'red';
  const currentPhase = controllerState.current_phase ?? 0;

  return (
    <div className="rl-page">
      <h1>🚦 RL Signal Control</h1>
      <p className="page-subtitle">Reinforcement Learning-based adaptive traffic signal optimization</p>

      {error && <div className="rl-error">{error}</div>}

      {/* Status & Controls */}
      <section className="panel">
        <div className="panel-header">
          <h2>⚡ Control Panel</h2>
          <span className={`system-pulse ${isRunning ? 'active' : 'inactive'}`}>
            {isRunning ? '● RL ACTIVE' : '○ RL INACTIVE'}
          </span>
        </div>

        <div className="rl-controls-grid">
          {/* Agent Config */}
          <div className="rl-config-section">
            <h3>Agent Configuration</h3>
            <div className="rl-config-form">
              <label>
                Agent Type
                <select
                  value={config.agent_type}
                  onChange={(e) => setConfig({ ...config, agent_type: e.target.value })}
                  disabled={isRunning}
                >
                  <option value="dqn">DQN (Deep Q-Network)</option>
                  <option value="ppo">PPO (Proximal Policy Optimization)</option>
                </select>
              </label>
              <label>
                Decision Interval (s)
                <input
                  type="number"
                  min="1" max="30" step="0.5"
                  value={config.decision_interval}
                  onChange={(e) => setConfig({ ...config, decision_interval: parseFloat(e.target.value) })}
                  disabled={isRunning}
                />
              </label>
              <label>
                Control Mode
                <select
                  value={config.control_mode}
                  onChange={(e) => setConfig({ ...config, control_mode: e.target.value })}
                  disabled={isRunning}
                >
                  <option value="simulated">Simulated</option>
                  <option value="hardware">Hardware (GPIO)</option>
                  <option value="api">API (External Controller)</option>
                </select>
              </label>
            </div>
            <div className="rl-action-buttons">
              {!isRunning ? (
                <button className="btn-start" onClick={handleStart} disabled={loading}>
                  {loading ? 'Starting...' : '▶ Start RL Control'}
                </button>
              ) : (
                <button className="btn-stop" onClick={handleStop} disabled={loading}>
                  {loading ? 'Stopping...' : '⏹ Stop RL Control'}
                </button>
              )}
              <button className="btn-reset" onClick={handleReset}>↻ Reset Stats</button>
            </div>
          </div>

          {/* Live Signal State */}
          <div className="rl-signal-section">
            <h3>Live Signal State</h3>
            <div className="signal-display">
              <div className="traffic-light">
                <div className={`light red ${signalState === 'red' ? 'on' : ''}`} />
                <div className={`light yellow ${signalState === 'yellow' ? 'on' : ''}`} />
                <div className={`light green ${signalState === 'green' ? 'on' : ''}`} />
              </div>
              <div className="signal-info">
                <span className="signal-phase-name">
                  {PHASE_LABELS[currentPhase]?.icon} {controllerState.phase_name || 'N/A'}
                </span>
                <span className="signal-duration">
                  Duration: {controllerState.phase_duration?.toFixed(1) || 0}s
                </span>
                <span className={`signal-mode ${controllerState.mode || ''}`}>
                  Mode: {controllerState.mode?.toUpperCase() || 'N/A'}
                </span>
                <span className="signal-switches">
                  Total Switches: {controllerState.total_switches || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Phase Selector */}
      <section className="panel">
        <div className="panel-header">
          <h2>🔄 Phase Control</h2>
          <small>Click to manually set phase (for testing)</small>
        </div>
        <div className="phase-grid">
          {PHASE_LABELS.map((phase, i) => (
            <div
              key={i}
              className={`phase-card ${currentPhase === i ? 'active' : ''} ${!controllerState.can_switch && currentPhase !== i ? 'disabled' : ''}`}
              onClick={() => handlePhaseClick(i)}
            >
              <span className="phase-icon">{phase.icon}</span>
              <span className="phase-name">{phase.name}</span>
              <span className="phase-directions">{phase.directions.join(' / ')}</span>
              {currentPhase === i && <span className="phase-active-badge">ACTIVE</span>}
            </div>
          ))}
        </div>
      </section>

      {/* Intersection Visualization */}
      <section className="panel">
        <div className="panel-header">
          <h2>🗺️ Intersection View</h2>
        </div>
        <div className="intersection-viz">
          <div className="intersection-grid">
            <div className="intersection-cell" />
            <div className={`intersection-road north ${currentPhase === 0 || currentPhase === 1 ? 'green' : 'red'}`}>
              <span>N</span>
              <div className={`road-signal ${(currentPhase === 0 || currentPhase === 1) ? signalState : 'red'}`} />
            </div>
            <div className="intersection-cell" />
            <div className={`intersection-road west ${currentPhase === 2 || currentPhase === 3 ? 'green' : 'red'}`}>
              <span>W</span>
              <div className={`road-signal ${(currentPhase === 2 || currentPhase === 3) ? signalState : 'red'}`} />
            </div>
            <div className="intersection-center">+</div>
            <div className={`intersection-road east ${currentPhase === 2 || currentPhase === 3 ? 'green' : 'red'}`}>
              <div className={`road-signal ${(currentPhase === 2 || currentPhase === 3) ? signalState : 'red'}`} />
              <span>E</span>
            </div>
            <div className="intersection-cell" />
            <div className={`intersection-road south ${currentPhase === 0 || currentPhase === 1 ? 'green' : 'red'}`}>
              <div className={`road-signal ${(currentPhase === 0 || currentPhase === 1) ? signalState : 'red'}`} />
              <span>S</span>
            </div>
            <div className="intersection-cell" />
          </div>
        </div>
      </section>

      {/* RL Metrics */}
      <section className="panel">
        <div className="panel-header">
          <h2>📊 RL Performance Metrics</h2>
        </div>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Decisions Made</h3>
            <span className="metric-value">{metrics.decisions_made || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Total Switches</h3>
            <span className="metric-value">{controllerStats.total_switches || 0}</span>
          </div>
          <div className="metric-card">
            <h3>Avg Phase Duration</h3>
            <span className="metric-value">{(controllerStats.avg_phase_duration || 0).toFixed(1)}s</span>
          </div>
          <div className="metric-card">
            <h3>Switches/min</h3>
            <span className="metric-value">{(controllerStats.switches_per_minute || 0).toFixed(1)}</span>
          </div>
          <div className="metric-card">
            <h3>Yellow Time</h3>
            <span className="metric-value">{controllerStats.total_yellow_time || 0}s</span>
          </div>
          <div className="metric-card">
            <h3>Uptime</h3>
            <span className="metric-value">
              {controllerStats.uptime_seconds
                ? `${Math.floor(controllerStats.uptime_seconds / 60)}m`
                : '0m'}
            </span>
          </div>
        </div>

        {/* Phase Distribution */}
        {controllerStats.phase_distribution && Object.keys(controllerStats.phase_distribution).length > 0 && (
          <div className="phase-distribution">
            <h3>Phase Time Distribution</h3>
            <div className="phase-bars">
              {Object.entries(controllerStats.phase_distribution).map(([phase, pct]) => (
                <div key={phase} className="phase-bar-row">
                  <span className="phase-bar-label">
                    {PHASE_LABELS[parseInt(phase)]?.icon} Phase {phase}
                  </span>
                  <div className="phase-bar-track">
                    <div
                      className="phase-bar-fill"
                      style={{ width: `${pct}%`, backgroundColor: `hsl(${parseInt(phase) * 90}, 60%, 50%)` }}
                    />
                  </div>
                  <span className="phase-bar-value">{pct}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Metrics History */}
      {metricsHistory.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <h2>📈 Metrics History</h2>
          </div>
          <div className="metrics-history-table">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Reward</th>
                  <th>Queue Length</th>
                  <th>Wait Time</th>
                  <th>Throughput</th>
                </tr>
              </thead>
              <tbody>
                {metricsHistory.slice(-20).map((m, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td className={m.reward >= 0 ? 'positive' : 'negative'}>{(m.reward || 0).toFixed(2)}</td>
                    <td>{m.queue_length || 0}</td>
                    <td>{(m.wait_time || 0).toFixed(1)}s</td>
                    <td>{m.throughput || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Bridge Metrics (CV-to-RL) */}
      {metrics.bridge && (
        <section className="panel">
          <div className="panel-header">
            <h2>🔗 CV-to-RL Bridge</h2>
            <small>Computer Vision data feeding into RL decisions</small>
          </div>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Vehicles Tracked</h3>
              <span className="metric-value">{metrics.bridge.total_vehicles || 0}</span>
            </div>
            <div className="metric-card">
              <h3>Avg Speed</h3>
              <span className="metric-value">{(metrics.bridge.avg_speed || 0).toFixed(1)} km/h</span>
            </div>
            <div className="metric-card">
              <h3>Congestion</h3>
              <span className="metric-value">{(metrics.bridge.congestion_level || 0).toFixed(1)}%</span>
            </div>
            <div className="metric-card">
              <h3>Updates Received</h3>
              <span className="metric-value">{metrics.bridge.updates_received || 0}</span>
            </div>
          </div>
        </section>
      )}

      {/* Model Management */}
      <section className="panel">
        <div className="panel-header">
          <h2>🧠 Trained Models</h2>
        </div>
        {models.length === 0 ? (
          <div className="empty-state">
            <p>No trained models found.</p>
            <p><code>python -m rl_signal_control.training.train</code> to train a model.</p>
          </div>
        ) : (
          <div className="models-list">
            {models.map((model, i) => (
              <div key={i} className="model-card">
                <div className="model-info">
                  <span className="model-name">{model.name}</span>
                  <div className="model-badges">
                    {model.has_best && <span className="badge badge-best">Best</span>}
                    {model.has_final && <span className="badge badge-final">Final</span>}
                  </div>
                </div>
                <button
                  className="btn-load-model"
                  onClick={() => handleLoadModel(model)}
                  disabled={loading}
                >
                  Load Model
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default RLSignalControl;
