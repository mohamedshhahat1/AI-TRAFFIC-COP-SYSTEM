import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Violations from './pages/Violations';
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
        </ul>
      </nav>
      <main className="content">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'violations' && <Violations />}
      </main>
    </div>
  );
}

export default App;
