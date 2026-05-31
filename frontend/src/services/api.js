/**
 * API Service - communicates with the FastAPI backend
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

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

export function connectWebSocket(onMessage) {
  const ws = new WebSocket(`ws://localhost:8000/ws/live`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  ws.onclose = () => setTimeout(() => connectWebSocket(onMessage), 5000);
  return ws;
}
