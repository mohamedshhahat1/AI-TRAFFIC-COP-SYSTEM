/**
 * AI Traffic Cop System - Dashboard JavaScript
 * Real-time monitoring and data visualization
 */

const API_BASE = window.location.origin + '/api';
const WS_URL = `ws://${window.location.host}/ws/live-feed`;

// State
let ws = null;
let violationsChart = null;
let speedChart = null;
let refreshInterval = null;

// ============ Initialization ============

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    initCharts();
    initWebSocket();
    startAutoRefresh();
    updateClock();
});

function initDashboard() {
    // Button handlers
    document.getElementById('btn-start').addEventListener('click', startCamera);
    document.getElementById('btn-stop').addEventListener('click', stopCamera);
    
    // Filter handlers
    document.getElementById('filter-type').addEventListener('change', loadViolations);
    document.getElementById('filter-severity').addEventListener('change', loadViolations);
    
    // Initial data load
    loadStatistics();
    loadViolations();
}

// ============ API Calls ============

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

async function loadStatistics() {
    const stats = await fetchAPI('/statistics/');
    if (stats) {
        document.getElementById('total-vehicles').textContent = stats.total_vehicles_tracked || 0;
        document.getElementById('total-violations').textContent = stats.total_violations || 0;
        document.getElementById('today-violations').textContent = stats.today_violations || 0;
        document.getElementById('avg-speed').textContent = `${stats.average_speed || 0} km/h`;
    }
}

async function loadViolations() {
    const typeFilter = document.getElementById('filter-type').value;
    const severityFilter = document.getElementById('filter-severity').value;
    
    let endpoint = '/violations/?limit=20';
    if (typeFilter) endpoint += `&violation_type=${typeFilter}`;
    if (severityFilter) endpoint += `&severity=${severityFilter}`;
    
    const data = await fetchAPI(endpoint);
    if (data && data.violations) {
        renderViolationsTable(data.violations);
    }
}

async function startCamera() {
    const response = await fetch(`${API_BASE}/camera/start`, { method: 'POST' });
    if (response.ok) {
        document.getElementById('system-status').textContent = '● LIVE';
        document.getElementById('system-status').className = 'status-badge active';
    }
}

async function stopCamera() {
    const response = await fetch(`${API_BASE}/camera/stop`, { method: 'POST' });
    if (response.ok) {
        document.getElementById('system-status').textContent = '● STOPPED';
        document.getElementById('system-status').className = 'status-badge';
    }
}

// ============ WebSocket ============

function initWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleLiveUpdate(data);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected. Reconnecting...');
            setTimeout(initWebSocket, 5000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.log('WebSocket not available');
    }
}

function handleLiveUpdate(data) {
    if (data.type === 'violation') {
        // Add new violation to table
        addViolationRow(data.violation);
        // Update stats
        loadStatistics();
        // Show notification
        showNotification(data.violation);
    }
}

// ============ Rendering ============

function renderViolationsTable(violations) {
    const tbody = document.getElementById('violations-tbody');
    
    if (!violations.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No violations recorded yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = violations.map(v => `
        <tr>
            <td>${formatTime(v.timestamp)}</td>
            <td>${formatViolationType(v.violation_type)}</td>
            <td><span class="severity-badge severity-${v.severity}">${v.severity.toUpperCase()}</span></td>
            <td>${v.vehicle_class} #${v.track_id}</td>
            <td>${v.speed ? v.speed.toFixed(1) + ' km/h' : '-'}</td>
            <td>${v.description || '-'}</td>
            <td>${v.is_confirmed ? '✅' : '⏳'}</td>
        </tr>
    `).join('');
}

function addViolationRow(violation) {
    const tbody = document.getElementById('violations-tbody');
    const row = document.createElement('tr');
    row.style.animation = 'fadeIn 0.5s';
    row.innerHTML = `
        <td>${formatTime(violation.timestamp)}</td>
        <td>${formatViolationType(violation.violation_type)}</td>
        <td><span class="severity-badge severity-${violation.severity}">${violation.severity.toUpperCase()}</span></td>
        <td>${violation.vehicle_class} #${violation.track_id}</td>
        <td>${violation.speed ? violation.speed.toFixed(1) + ' km/h' : '-'}</td>
        <td>${violation.description || '-'}</td>
        <td>✅</td>
    `;
    tbody.insertBefore(row, tbody.firstChild);
}

// ============ Charts ============

function initCharts() {
    // Violations by Type Chart
    const violationsCtx = document.getElementById('violations-chart').getContext('2d');
    violationsChart = new Chart(violationsCtx, {
        type: 'doughnut',
        data: {
            labels: ['Speed', 'Red Light', 'Lane', 'Parking'],
            datasets: [{
                data: [45, 25, 20, 10],
                backgroundColor: ['#ea4335', '#fbbc04', '#4285f4', '#34a853'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#e0e0e0', padding: 15 }
                }
            }
        }
    });

    // Speed Distribution Chart
    const speedCtx = document.getElementById('speed-chart').getContext('2d');
    speedChart = new Chart(speedCtx, {
        type: 'bar',
        data: {
            labels: ['0-20', '20-40', '40-60', '60-80', '80-100', '100+'],
            datasets: [{
                label: 'Vehicles',
                data: [5, 15, 35, 25, 12, 3],
                backgroundColor: ['#34a853', '#34a853', '#4285f4', '#fbbc04', '#ea4335', '#ea4335'],
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Speed (km/h)', color: '#888' },
                    ticks: { color: '#888' },
                    grid: { display: false }
                },
                y: {
                    title: { display: true, text: 'Count', color: '#888' },
                    ticks: { color: '#888' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ============ Utilities ============

function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function formatViolationType(type) {
    const icons = {
        'speed_violation': '🏎️ Speed',
        'red_light_violation': '🚦 Red Light',
        'lane_violation': '🛣️ Lane',
        'illegal_parking': '🚫 Parking',
        'wrong_way': '⛔ Wrong Way',
    };
    return icons[type] || type;
}

function showNotification(violation) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('🚨 Traffic Violation Detected', {
            body: violation.description,
            icon: '🚔'
        });
    }
}

function updateClock() {
    const el = document.getElementById('current-time');
    const now = new Date();
    el.textContent = now.toLocaleString();
    setTimeout(updateClock, 1000);
}

function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadStatistics();
    }, 5000);
}

// Request notification permission
if ('Notification' in window) {
    Notification.requestPermission();
}
