import React from 'react';

function EvidenceViewer({ evidence = {} }) {
  if (!evidence || !evidence.plate_number) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>📸 Evidence Viewer</h2>
        </div>
        <div className="empty-state">
          <p>No violation evidence to display</p>
          <small>Evidence appears when a violation with plate recognition occurs</small>
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>📸 Violation Evidence</h2>
        <span className="badge badge-red">{evidence.violation_type || 'Violation'}</span>
      </div>
      <div className="evidence-grid">
        <div className="evidence-item">
          <h4>🚗 Vehicle</h4>
          {evidence.vehicle_crop ? (
            <img src={evidence.vehicle_crop} alt="Vehicle" className="evidence-img" />
          ) : (
            <div className="evidence-placeholder">No image</div>
          )}
        </div>
        <div className="evidence-item">
          <h4>🔢 License Plate</h4>
          {evidence.plate_crop ? (
            <img src={evidence.plate_crop} alt="Plate" className="evidence-img" />
          ) : (
            <div className="evidence-placeholder">No image</div>
          )}
          <p className="evidence-plate">{evidence.plate_number}</p>
        </div>
        <div className="evidence-item">
          <h4>📋 Details</h4>
          <div className="evidence-details">
            <p><strong>Plate:</strong> {evidence.plate_number}</p>
            <p><strong>Owner:</strong> {evidence.owner || 'Unknown'}</p>
            <p><strong>Vehicle:</strong> {evidence.vehicle || 'Unknown'}</p>
            <p><strong>Violation:</strong> {evidence.violation_type}</p>
            <p><strong>Speed:</strong> {evidence.speed || 0} km/h</p>
            <p><strong>Time:</strong> {evidence.timestamp || 'N/A'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EvidenceViewer;
