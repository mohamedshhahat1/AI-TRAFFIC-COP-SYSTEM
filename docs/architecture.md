# 🏗️ System Architecture

## High-Level Architecture

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
        │  - Vehicles                                │
        │  - Traffic Lights                          │
        │  - Pedestrians                             │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │         Tracking Layer                     │
        │   DeepSORT Multi-Object Tracking           │
        │   → Assign Vehicle IDs                     │
        │   → Track Movement Paths                   │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │     Motion & Speed Estimation Layer        │
        │   - Distance between frames                │
        │   - Speed calculation (km/h)               │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │     Violation Detection Engine             │
        │  - Speed Violation                         │
        │  - Red Light Violation                     │
        │  - Lane Violation                          │
        │  - Illegal Parking                         │
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
        ┌────────────────────────────────────────────┐
        │   AI Prediction Layer                      │
        │ - Accident Prediction                      │
        │ - Traffic Congestion AI                    │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │ Smart City Integration                     │
        │ - Multi-camera fusion                      │
        │ - City-wide analytics                      │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │            Backend API Layer               │
        │   FastAPI Server                           │
        │   - Store violations                       │
        │   - Handle requests                        │
        └─────────────┬──────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌──────────────────┐   ┌────────────────────┐  ┌────────────────────┐
│   Database       │   │   Dashboard UI     │  │  Alert System      │
│ PostgreSQL /     │   │ React / Flutter    │  │ SMS / Email / Push │
│ SQLite           │   │ - Live Monitoring  │  │ - Real-time alerts │
└──────────────────┘   └────────────────────┘  └────────────────────┘
```

## Layer Descriptions

### 1. Input Layer
- Camera feed management (RTSP, files, webcam)
- Frame preprocessing and normalization

### 2. AI Vision Layer
- YOLOv8 object detection
- Classes: car, truck, bus, motorcycle, person, traffic_light

### 3. Tracking Layer
- DeepSORT multi-object tracking
- Persistent vehicle IDs across frames
- Movement path recording

### 4. Speed Estimation Layer
- Pixel-to-real-world speed conversion
- Calibration support
- Moving average smoothing

### 5. Violation Detection Engine
- Speed violations
- Red light violations
- Lane violations
- Illegal parking detection

### 6. AI Prediction Layer (NEW)
- Accident risk prediction using TTC
- Congestion level analysis & forecasting
- Dangerous driving pattern detection

### 7. Smart City Integration (NEW)
- Multi-camera network management
- Cross-camera vehicle re-identification
- City-wide traffic analytics
- Environmental impact estimation

### 8. Backend API
- FastAPI REST server
- WebSocket live streaming
- Database storage (SQLAlchemy)

### 9. Frontend Dashboard
- React.js web dashboard
- Real-time statistics
- Violation history & filtering

### 10. Mobile App
- Flutter cross-platform app
- Push notifications
- Quick violation overview

### 11. Alert System
- Email (SMTP)
- SMS (Twilio)
- Push notifications (Firebase)
- Webhook support
