import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Violations from './pages/Violations';
import Monitoring from './pages/Monitoring';
import Results from './pages/Results';
import RLSignalControl from './pages/RLSignalControl';
import MultiCamera from './pages/MultiCamera';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="logo">🚔 AI Traffic Cop</div>
        <ul>
          <li className={currentPage === 'dashboard' ? 'active' : ''}
              onClick={() => setCurrentPage('dashboard')}>
            📊 Dashboard
          </li>
          <li className={currentPage === 'violations' ? 'active' : ''}
              onClick={() => setCurrentPage('violations')}>
            🚨 Violations
          </li>
          <li className={currentPage === 'rl' ? 'active' : ''}
              onClick={() => setCurrentPage('rl')}>
            🚦 RL Signal Control
          </li>
          <li className={currentPage === 'cameras' ? 'active' : ''}
              onClick={() => setCurrentPage('cameras')}>
            📷 Multi-Camera
          </li>
          <li className={currentPage === 'monitoring' ? 'active' : ''}
              onClick={() => setCurrentPage('monitoring')}>
            📈 Monitoring
          </li>
          <li className={currentPage === 'results' ? 'active' : ''}
              onClick={() => setCurrentPage('results')}>
            📊 Results
          </li>
        </ul>
        <div className="sidebar-footer">
          <small>Event-Driven Architecture</small>
        </div>
      </nav>
      <main className="content">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'violations' && <Violations />}
        {currentPage === 'rl' && <RLSignalControl />}
        {currentPage === 'cameras' && <MultiCamera />}
        {currentPage === 'monitoring' && <Monitoring />}
        {currentPage === 'results' && <Results />}
      </main>
    </div>
  );
}

export default App;
