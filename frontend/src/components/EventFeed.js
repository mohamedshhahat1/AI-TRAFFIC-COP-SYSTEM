import React from 'react';

function EventFeed({ events = [] }) {
  const getIcon = (type) => {
    const icons = {
      violation: '🚨',
      accident_risk: '⚠️',
      congestion: '🚦',
      tracking: '🚗',
    };
    return icons[type] || '📡';
  };

  const getPriorityClass = (priority) => {
    if (priority === 'CRITICAL' || priority === 'EMERGENCY') return 'event-critical';
    if (priority === 'HIGH') return 'event-high';
    return 'event-normal';
  };

  return (
    <div className="event-feed-panel">
      <div className="panel-header">
        <h2>🔥 Live Event Stream</h2>
        <span className="event-count">{events.length} events</span>
      </div>
      <div className="event-list">
        {events.length === 0 ? (
          <p className="empty-state">Waiting for events...</p>
        ) : (
          events.map((event, i) => (
            <div key={i} className={`event-item ${getPriorityClass(event.priority)}`}>
              <span className="event-icon">{getIcon(event.type)}</span>
              <div className="event-content">
                <span className="event-topic">{event.topic || event.type}</span>
                <span className="event-detail">
                  {event.data?.description || event.data?.track_id 
                    ? `Vehicle #${event.data.track_id}` 
                    : JSON.stringify(event.data || {}).slice(0, 60)}
                </span>
              </div>
              <span className="event-time">
                {event.timestamp ? new Date(event.timestamp * 1000).toLocaleTimeString() : 'now'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default EventFeed;
