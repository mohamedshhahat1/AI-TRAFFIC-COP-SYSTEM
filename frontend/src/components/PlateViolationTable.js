import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';

function PlateViolationTable() {
  const [plates, setPlates] = useState([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const url = search
          ? `${API_BASE}/plates/search?q=${search}`
          : `${API_BASE}/plates`;
        const res = await fetch(url);
        const data = await res.json();
        if (search) {
          setPlates(data.results || []);
        } else {
          // Convert registry object to array
          const vehicles = data.vehicles || {};
          const arr = Object.entries(vehicles).map(([plate, info]) => ({
            plate, ...info
          }));
          setPlates(arr);
        }
      } catch (e) {}
    };
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [search]);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🚘 License Plate Registry</h2>
        <input
          type="text"
          placeholder="Search plate / owner..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: '6px 12px',
            background: 'var(--dark)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            color: 'var(--text)',
            fontSize: '0.85rem',
          }}
        />
      </div>
      <div className="table-container">
        {plates.length === 0 ? (
          <p className="empty-state">No plates found</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Plate</th>
                <th>Owner</th>
                <th>Vehicle</th>
                <th>Color</th>
                <th>Violations</th>
              </tr>
            </thead>
            <tbody>
              {plates.map((p, i) => (
                <tr key={i}>
                  <td style={{fontWeight: 'bold', color: '#4285f4', direction: 'auto'}}>{p.plate || p.plate_number}</td>
                  <td style={{direction: 'auto'}}>{p.owner}</td>
                  <td style={{direction: 'auto'}}>{p.vehicle}</td>
                  <td style={{direction: 'auto'}}>{p.color}</td>
                  <td>
                    <span className={`badge ${p.violations_history > 3 ? 'badge-red' : p.violations_history > 0 ? 'badge-orange' : 'badge-green'}`}>
                      {p.violations_history || 0}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default PlateViolationTable;
