/**
 * API Service - communicates with the FastAPI backend
 * Includes: violations, vehicles, analytics, monitoring, events, health
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/live';

// ==================== Core APIs ====================

export async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch stats:', err);
    return {};
  }
}

export async function fetchViolations(limit = 50, type = '') {
  try {
    let url = `${API_BASE}/violations/?limit=${limit}`;
    if (type) url += `&type=${type}`;
    const res = await fetch(url);
    const data = await res.json();
    return data.violations || [];
  } catch (err) {
    console.error('Failed to fetch violations:', err);
    return [];
  }
}

export async function fetchVehicles(limit = 50) {
  try {
    const res = await fetch(`${API_BASE}/vehicles/?limit=${limit}`);
    const data = await res.json();
    return data.vehicles || [];
  } catch (err) {
    console.error('Failed to fetch vehicles:', err);
    return [];
  }
}

// ==================== Monitoring APIs ====================

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/analytics/health`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch health:', err);
    return { status: 'unreachable', score: 0, components: {}, alerts: [] };
  }
}

export async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/metrics`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch metrics:', err);
    return {};
  }
}

export async function fetchLogs(limit = 50, level = null, component = null) {
  try {
    let url = `${API_BASE}/analytics/logs?limit=${limit}`;
    if (level) url += `&level=${level}`;
    if (component) url += `&component=${component}`;
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch logs:', err);
    return { logs: [], total: 0 };
  }
}

export async function fetchLogStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/logs/stats`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch log stats:', err);
    return {};
  }
}

// ==================== Event Bus APIs ====================

export async function fetchEventMetrics() {
  try {
    const res = await fetch(`${API_BASE}/events/metrics`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch event metrics:', err);
    return {};
  }
}

export async function fetchEventHistory(topic = 'violation.*', limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/events/history?topic=${topic}&limit=${limit}`);
    const data = await res.json();
    return data.events || [];
  } catch (err) {
    console.error('Failed to fetch event history:', err);
    return [];
  }
}

// ==================== WebSocket (Live Events) ====================

export function connectWebSocket(onMessage, onError = null) {
  let ws;
  let reconnectTimer = null;
  let isClosedManually = false;
  
  function connect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
      console.log('🔌 WebSocket connected - receiving live events');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };
    
    ws.onclose = () => {
      if (!isClosedManually) {
        console.log('WebSocket disconnected. Reconnecting in 5s...');
        reconnectTimer = setTimeout(connect, 5000);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };
  }
  
  connect();
  return { 
    close: () => { 
      isClosedManually = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close(); 
    } 
  };
}
