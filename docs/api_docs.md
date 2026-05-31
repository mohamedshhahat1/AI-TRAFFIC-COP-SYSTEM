# 📡 API Documentation

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### Health Check
```
GET /api/health
```
Returns system health status.

### Violations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/violations/` | List all violations |
| GET | `/api/violations/{id}` | Get violation by ID |
| POST | `/api/violations/` | Create violation |
| GET | `/api/violations/summary/today` | Today's summary |

**Query Parameters:**
- `type` - Filter by violation type
- `severity` - Filter by severity level
- `limit` - Max results (default: 50)

### Vehicles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles/` | List tracked vehicles |
| GET | `/api/vehicles/{track_id}` | Get vehicle details |
| GET | `/api/vehicles/{track_id}/history` | Vehicle history |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/` | Overall statistics |
| GET | `/api/analytics/congestion` | Congestion data |
| GET | `/api/analytics/heatmap` | Violation heatmap |
| GET | `/api/analytics/trends` | Traffic trends |

### WebSocket

```
WS /ws/live
```
Real-time violation and tracking data stream.

## Response Format

```json
{
  "total": 10,
  "violations": [
    {
      "id": "abc123",
      "type": "speed_violation",
      "severity": "high",
      "track_id": 5,
      "speed": 85.3,
      "timestamp": "2026-05-31T12:00:00"
    }
  ]
}
```
