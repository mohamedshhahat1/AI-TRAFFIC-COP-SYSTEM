import React, { useState, useEffect } from 'react';

function DetectedPlates() {
  const [plates, setPlates] = useState([]);

  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/camera/stats');
        const data = await res.json();
        if (data.plates_detected && data.plates_detected.length > 0) {
          setPlates(data.plates_detected);
        }
      } catch (e) {}
    }, 1000);
    return () => clearInterval(poll);
  }, []);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>🔢 Detected License Plates (ANPR)</h2>
        <span className="count-badge">{plates.length} plates</span>
      </div>
      {plates.length === 0 ? (
        <div className="empty-state">Waiting for plate detections...</div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Plate Number</th>
                <th>Vehicle ID</th>
                <th>Owner</th>
                <th>Confidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {plates.map((p, i) => (
                <tr key={i}>
                  <td style={{fontWeight: 'bold', color: '#fbbc04', fontSize: '1.1rem'}}>{p.plate}</td>
                  <td>#{p.track_id}</td>
                  <td>{p.owner}</td>
                  <td>{(p.confidence * 100).toFixed(0)}%</td>
                  <td>
                    <span className={`badge ${p.owner === 'Unregistered' ? 'badge-orange' : 'badge-green'}`}>
                      {p.owner === 'Unregistered' ? 'Unknown' : 'Registered'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default DetectedPlates;
