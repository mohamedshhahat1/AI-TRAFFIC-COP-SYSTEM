/**
 * API Service - communicates with the FastAPI backend
 * Auto-detects API URL: works in Coder proxy, localhost, and Docker
 */

// API connects to backend - uses env var or relative path via proxy
const API_BASE = process.env.REACT_APP_API_URL || '/api';
const WS_BASE = process.env.REACT_APP_WS_URL || '';

// Construct WebSocket URL dynamically from current location
function getWebSocketUrl() {
  if (WS_BASE) return WS_BASE;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/live`;
}

// ==================== Core APIs ====================

export async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch stats:', err);
    return {};
  }
}

export async function fetchViolations(limit = 50, type = '', severity = '') {
  try {
    let url = `${API_BASE}/violations?limit=${limit}`;
    if (type) url += `&type=${type}`;
    if (severity) url += `&severity=${severity}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.violations || [];
  } catch (err) {
    console.error('Failed to fetch violations:', err);
    return [];
  }
}

export async function fetchVehicles(limit = 50) {
  try {
    const res = await fetch(`${API_BASE}/vehicles?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch health:', err);
    return { status: 'unreachable', score: 0, components: {}, alerts: [] };
  }
}

export async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/metrics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch logs:', err);
    return { logs: [], total: 0 };
  }
}

export async function fetchLogStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/logs/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch event metrics:', err);
    return {};
  }
}

export async function fetchEventHistory(topic = 'violation.*', limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/events/history?topic=${topic}&limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.events || [];
  } catch (err) {
    console.error('Failed to fetch event history:', err);
    return [];
  }
}

// ==================== Camera Control ====================

export async function startCamera(source = 'data/videos/traffic.mp4') {
  try {
    const res = await fetch(`${API_BASE}/camera/start?source=${encodeURIComponent(source)}`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to start camera:', err);
    return { status: 'error', message: err.message };
  }
}

export async function stopCamera() {
  try {
    const res = await fetch(`${API_BASE}/camera/stop`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to stop camera:', err);
    return { status: 'error', message: err.message };
  }
}

export async function fetchCameraStats() {
  try {
    const res = await fetch(`${API_BASE}/camera/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { running: false, fps: 0, objects: 0, tracks: 0, frame: 0 };
  }
}

export async function fetchCameraInfo() {
  try {
    const res = await fetch(`${API_BASE}/camera/info`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { source: '', name: 'No camera', resolution: '—', fps: 0, status: 'Disconnected' };
  }
}

export async function fetchRequestCount() {
  try {
    const res = await fetch(`${API_BASE}/stats/requests`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { total_requests: 0 };
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

    try {
      const wsUrl = getWebSocketUrl();
      ws = new WebSocket(wsUrl);

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
    } catch (e) {
      console.log('WebSocket not available, retrying in 5s...');
      reconnectTimer = setTimeout(connect, 5000);
    }
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

// Export API_BASE for components that need the base URL (e.g., MJPEG stream)
export { API_BASE };
