import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Violations from './pages/Violations';
import Monitoring from './pages/Monitoring';
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
          <li className={currentPage === 'monitoring' ? 'active' : ''} 
              onClick={() => setCurrentPage('monitoring')}>
            📈 Monitoring
          </li>
        </ul>
        <div className="sidebar-footer">
          <small>Event-Driven Architecture</small>
        </div>
      </nav>
      <main className="content">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'violations' && <Violations />}
        {currentPage === 'monitoring' && <Monitoring />}
      </main>
    </div>
  );
}

export default App;
