# 🏗️ System Architecture

## High-Level Architecture (Event-Driven)

```
                    ┌────────────────────────────┐
                    │      CCTV / Video Feed     │
                    │  (Live Camera / RTSP / MP4)│
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │  Frame Preprocessing Layer │
                    │ (Resize / Normalize / FPS) │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │        AI Vision Layer (Detection)         │
        │        YOLOv8 Object Detection             │
        │  - Vehicles 🚗 🚛 🏍️                      │
        │  - Traffic Lights 🚦                       │
        │  - Pedestrians 🚶                          │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │         Tracking Layer                     │
        │   DeepSORT Multi-Object Tracking           │
        │   → Assign Unique Vehicle IDs              │
        │   → Track Movement Paths                   │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │     Motion & Speed Estimation Layer        │
        │   - Pixel displacement measurement         │
        │   - Real-world speed (km/h)                │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │     Violation Detection Engine             │
        │  🔴 Speed Violation                        │
        │  🚦 Red Light Violation                    │
        │  🛣️ Lane Violation                         │
        │  🚫 Illegal Parking                        │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │     Decision & Severity Engine             │
        │  - Classify violation severity             │
        │  - Filter false positives                  │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │   AI Prediction Layer      │
                    │ - Accident Prediction      │
                    │ - Traffic Congestion AI    │
                    │ - Dangerous Driving Alert  │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │ Smart City Integration     │
                    │ - Multi-camera fusion      │
                    │ - City-wide analytics      │
                    │ - Environmental impact     │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────┐
    │              🔥 EVENT BUS (Central Nervous System)   │
    │                                                     │
    │   violation.speed ──┐                               │
    │   violation.red_light ──┤                           │
    │   accident.risk ────┤   → All events flow here     │
    │   congestion.change ┤                               │
    │   tracking.update ──┘                               │
    └────────────┬───────────────┬──────────────┬─────────┘
                 │               │              │
                 ▼               ▼              ▼
    ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
    │  API Gateway   │  │Alert Service │  │  Dashboard   │
    │(InferenceService)│  │(Email/SMS/Push)│  │ (WebSocket)  │
    └───────┬────────┘  └──────────────┘  └──────────────┘
            │
            ▼
    ┌────────────────────────────────────────────┐
    │            Backend API Layer               │
    │   FastAPI Server                           │
    │   - REST endpoints                         │
    │   - WebSocket streaming                    │
    │   - Database storage                       │
    └─────────────┬──────────────────────────────┘
            │
            ▼
    ┌──────────────────┐
    │   Database       │
    │ PostgreSQL/SQLite │
    └──────────────────┘
```

## Event-Driven Architecture

The system uses a **publish/subscribe event bus** (like Uber, Tesla, Google):

```
┌─────────────┐    emit()     ┌──────────────┐    notify    ┌──────────────┐
│  AI Engine  │──────────────▶│  EVENT BUS   │─────────────▶│   Backend    │
│  (Producer) │               │              │              │  (Consumer)  │
└─────────────┘               │  Topics:     │    notify    ├──────────────┤
                              │  violation.* │─────────────▶│Alert Service │
                              │  accident.*  │              ├──────────────┤
                              │  congestion.*│    notify    │  Dashboard   │
                              │  tracking.*  │─────────────▶│ (WebSocket)  │
                              │  system.*    │              ├──────────────┤
                              │  camera.*    │    notify    │  Database    │
                              └──────────────┘─────────────▶│  (Storage)   │
                                                            └──────────────┘
```

### Event Topics

| Topic | Description | Priority |
|-------|-------------|----------|
| `violation.speed` | Speed limit exceeded | HIGH |
| `violation.red_light` | Red light running | CRITICAL |
| `violation.lane` | Illegal lane change | HIGH |
| `violation.parking` | Illegal parking | LOW |
| `accident.risk` | Collision risk predicted | CRITICAL |
| `accident.imminent` | Collision in < 1.5s | EMERGENCY |
| `congestion.change` | Traffic level changed | NORMAL |
| `congestion.gridlock` | Gridlock detected | CRITICAL |
| `tracking.new_vehicle` | Vehicle entered frame | LOW |
| `tracking.vehicle_lost` | Vehicle left frame | LOW |
| `tracking.update` | Periodic tracking stats | LOW |
| `system.started` | System booted | NORMAL |
| `system.error` | Component failure | CRITICAL |
| `camera.connected` | Camera online | NORMAL |
| `camera.disconnected` | Camera offline | HIGH |

## API Gateway Pattern

```
Backend ←→ AIGateway ←→ InferenceService ←→ AIPipeline
                     ←→ MessageBroker ←→ Event subscribers
```

The backend ONLY talks to `AIGateway` — it never touches the AI internals.

### Benefits:
- AI engine can deploy on separate GPU server
- Backend stays lightweight (CPU only)
- Horizontal scaling (multiple inference workers)
- Clean separation of concerns
- Easy to add new consumers (just subscribe to events)

## Layer Descriptions

### 1. Detection Layer (`ai_engine/detection/`)
- YOLOv8 object detection
- Classes: car, truck, bus, motorcycle, person, traffic_light

### 2. Tracking Layer (`ai_engine/tracking/`)
- DeepSORT multi-object tracking
- Persistent vehicle IDs across frames

### 3. Speed Estimation (`ai_engine/speed_estimation/`)
- Pixel-to-real-world speed conversion
- Calibration & smoothing

### 4. Violation Detection (`ai_engine/violation_detection/`)
- Speed, red light, lane, parking violations
- Evidence snapshot capture

### 5. AI Prediction (`ai_engine/prediction/`)
- Accident risk via Time-To-Collision (TTC)
- Congestion level forecasting
- Dangerous driving pattern detection

### 6. Smart City (`ai_engine/smart_city/`)
- Multi-camera vehicle re-identification
- City-wide traffic analytics
- Environmental impact estimation

### 7. Event Bus (`ai_engine/event_bus/`) ⚡ NEW
- Production-grade pub/sub system
- Priority levels (LOW → EMERGENCY)
- Wildcard matching, replay, dead letter queue
- Rate limiting, middleware support

### 8. API Bridge (`ai_engine/api_bridge/`) 🌐 NEW
- `AIGateway` - Single entry point for backend
- `InferenceService` - Sync/async/batch inference
- `MessageBroker` - Cross-service communication

### 9. Backend (`backend/`)
- FastAPI REST server + WebSocket
- Database (SQLAlchemy + PostgreSQL/SQLite)
- Subscribes to Event Bus for real-time data

### 10. Frontend (`frontend/`)
- React.js web dashboard
- Real-time via WebSocket

### 11. Mobile (`mobile_app/`)
- Flutter cross-platform app
- Push notifications

### 12. Docker (`docker/`)
- One-click deployment
- docker-compose orchestration
