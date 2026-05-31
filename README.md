# 🚔 AI Traffic Cop System

> **Smart Traffic Enforcement & Analytics System** — Event-Driven AI Architecture

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-green.svg)
![DeepSORT](https://img.shields.io/badge/DeepSORT-Tracking-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)
![React](https://img.shields.io/badge/React-Frontend-61DAFB.svg)
![Flutter](https://img.shields.io/badge/Flutter-Mobile-02569B.svg)
![Docker](https://img.shields.io/badge/Docker-Deploy-2496ED.svg)
![Event-Driven](https://img.shields.io/badge/Architecture-Event--Driven-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🧠 Project Overview

The **AI Traffic Cop System** is an intelligent real-time surveillance system that uses **computer vision**, **AI**, and **event-driven architecture** to:
- Monitor road traffic in real-time
- Detect traffic violations automatically
- Predict accidents before they happen
- Analyze city-wide congestion patterns
- Alert authorities through multiple channels

Built with **production-grade patterns** used by companies like Uber, Tesla, and Google.

---

## 🏗️ System Architecture

```
                    ┌────────────────────────────┐
                    │      CCTV / Video Feed     │
                    │  (Live Camera / RTSP / MP4)│
                    └─────────────┬──────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │        AI Vision Layer (YOLOv8)            │
        │  Vehicles 🚗 | Lights 🚦 | People 🚶      │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │   Tracking (DeepSORT) → Speed Estimation   │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │       Violation Detection Engine           │
        │  Speed | Red Light | Lane | Parking        │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │       AI Prediction Layer                  │
        │  Accident Risk | Congestion Forecast       │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
        ┌────────────────────────────────────────────┐
        │       Smart City Integration               │
        │  Multi-Camera | City Analytics             │
        └─────────────┬──────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────┐
    │         🔥 EVENT BUS (Pub/Sub Architecture)         │
    │                                                     │
    │   violation.* | accident.* | congestion.* |         │
    │   tracking.* | system.* | camera.*                  │
    └────────┬──────────────┬──────────────┬──────────────┘
             │              │              │
             ▼              ▼              ▼
    ┌────────────────┐ ┌──────────┐ ┌────────────────┐
    │  API Gateway   │ │  Alerts  │ │   Dashboard    │
    │ (Backend API)  │ │ SMS/Email│ │  (WebSocket)   │
    └────────────────┘ └──────────┘ └────────────────┘
```

---

## 📁 Project Structure

```
AI-Traffic-Cop-System/
│
├── ai_engine/                       # 🧠 Core AI Intelligence
│   ├── detection/
│   │   ├── yolo_detector.py         # YOLOv8 object detection
│   │   └── model_loader.py          # Model management
│   ├── tracking/
│   │   ├── deep_sort_tracker.py     # DeepSORT tracking
│   │   └── object_tracker.py        # Track data structures
│   ├── speed_estimation/
│   │   └── speed_calculator.py      # Speed measurement
│   ├── violation_detection/
│   │   ├── speed_violation.py       # Speed limit detection
│   │   ├── red_light.py             # Red light running
│   │   ├── lane_violation.py        # Illegal lane changes
│   │   ├── parking_violation.py     # Illegal parking
│   │   └── violation_engine.py      # Central orchestrator
│   ├── prediction/                  # 🔮 AI Prediction Layer
│   │   ├── accident_predictor.py    # Collision risk (TTC)
│   │   └── congestion_analyzer.py   # Traffic density AI
│   ├── smart_city/                  # 🏙️ Smart City
│   │   ├── multi_camera_fusion.py   # Cross-camera tracking
│   │   └── city_analytics.py        # City-wide insights
│   ├── event_bus/                   # 🔥 Event-Driven System
│   │   ├── event_manager.py         # Central Event Bus
│   │   └── event_types.py           # Typed event factory
│   ├── api_bridge/                  # 🌐 API Gateway Layer
│   │   ├── inference_service.py     # Sync/async inference
│   │   ├── message_broker.py        # Cross-service comms
│   │   └── api_gateway.py           # Single entry point
│   ├── pipeline.py                  # Main AI pipeline
│   └── utils.py                     # Utility functions
│
├── backend/                         # ⚙️ API Server
│   ├── app/
│   │   ├── main.py                  # FastAPI + Event Bus integration
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── violations.py
│   │   │   ├── vehicles.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── db_service.py
│   │   │   └── alert_service.py
│   │   └── models/
│   │       ├── violation_model.py
│   │       └── vehicle_model.py
│   └── database/
│       └── db_connection.py
│
├── frontend/                        # 📊 Web Dashboard (React)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.js
│   └── package.json
│
├── mobile_app/                      # 📱 Mobile App (Flutter)
│   ├── lib/
│   │   ├── screens/
│   │   ├── services/
│   │   └── main.dart
│   └── pubspec.yaml
│
├── configs/                         # ⚙️ Configuration
│   ├── settings.yaml
│   ├── camera_config.yaml
│   └── thresholds.yaml
│
├── scripts/                         # 🚀 Automation
│   ├── run_pipeline.py              # Uses AIGateway
│   ├── train_model.py
│   └── export_model.py
│
├── docs/                            # 📄 Documentation
│   ├── architecture.md              # Full architecture diagram
│   └── api_docs.md                  # API reference
│
├── tests/                           # 🧪 Tests
│   ├── test_detection.py
│   ├── test_tracking.py
│   └── test_api.py
│
├── docker/                          # 🐳 Deployment
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── data/                            # 📦 Data
├── models/                          # 🧠 AI Models
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🔥 Event-Driven Architecture

The system uses a **production-grade pub/sub Event Bus** — no direct calls between components:

```python
# AI detects violation → emits event
TrafficEvent.speed_violation(bus, track_id=5, speed=95, limit=60)

# Multiple consumers react INDEPENDENTLY:
bus.on("violation.*", save_to_database)        # Backend
bus.on("violation.*", broadcast_websocket)     # Dashboard  
bus.on("violation.speed", send_sms_alert)      # Alerts
bus.on("accident.risk", emergency_dispatch)    # Emergency
```

### Event Topics

| Topic | Trigger | Priority |
|-------|---------|----------|
| `violation.speed` | Vehicle exceeds limit | HIGH |
| `violation.red_light` | Red light crossed | CRITICAL |
| `violation.lane` | Illegal lane change | HIGH |
| `accident.risk` | Collision predicted | CRITICAL |
| `accident.imminent` | TTC < 1.5 seconds | EMERGENCY |
| `congestion.change` | Traffic level shifts | NORMAL |
| `tracking.update` | Vehicle count update | LOW |
| `system.error` | Component failure | CRITICAL |

### Event Bus Features
- ⚡ Priority levels (LOW → EMERGENCY)
- 🎯 Wildcard matching (`violation.*`)
- 🔁 Event replay for late subscribers
- 💀 Dead letter queue (retry failed events)
- 🛡️ Rate limiting per topic
- 🔌 Middleware/interceptor support
- 📈 Built-in metrics & monitoring

---

## 🌐 API Gateway Pattern

```
Backend → AIGateway → InferenceService → AI Pipeline → Results
                   → Event Bus → All subscribers
```

The backend ONLY interacts with `AIGateway` — clean separation:

```python
from ai_engine import AIGateway

gateway = AIGateway(config)
gateway.start()

# Single call does everything
results = gateway.process_frame(frame)

# Subscribe to live events
gateway.on_violation(handle_violation)
gateway.on_accident_risk(send_emergency)
```

---

## 🚀 Features

### AI Features
| Feature | Technology |
|---------|-----------|
| 🎥 Real-time Detection | YOLOv8 |
| 🎯 Vehicle Tracking | DeepSORT |
| ⚡ Speed Estimation | Calibrated pixel-to-world |
| 🚨 Violation Detection | Multi-type engine |
| 🔮 Accident Prediction | Time-To-Collision AI |
| 🚦 Congestion AI | Density + flow analysis |
| 🏙️ Multi-Camera | Cross-camera ReID |

### Architecture Features
| Feature | Description |
|---------|-------------|
| 🔥 Event-Driven | Pub/sub like Uber/Tesla |
| 🌐 API Gateway | Single entry point, scalable |
| 📡 WebSocket | Real-time dashboard updates |
| 🐳 Docker | One-click deployment |
| 🧪 Tests | Unit test coverage |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Detection | YOLOv8 (Ultralytics) |
| Tracking | DeepSORT |
| Vision | OpenCV |
| ML | PyTorch |
| Event System | Custom Event Bus |
| API Gateway | Custom InferenceService |
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL / SQLite |
| Frontend | React.js |
| Mobile | Flutter |
| Deploy | Docker Compose |

---

## ⚙️ Installation

```bash
# Clone
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM

# Install
pip install -r requirements.txt

# Run full pipeline (event-driven)
python scripts/run_pipeline.py --source data/videos/sample.mp4 --display

# Run API server
uvicorn backend.app.main:app --reload --port 8000

# Docker (one-click)
cd docker && docker-compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System + AI Gateway health |
| GET | `/api/violations/` | List violations |
| GET | `/api/vehicles/` | Tracked vehicles |
| GET | `/api/analytics/` | Statistics |
| GET | `/api/events/metrics` | Event Bus metrics |
| GET | `/api/events/history` | Recent events |
| WS | `/ws/live` | Real-time event stream |

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**Mohamed Shahat** — [@mohamedshhahat1](https://github.com/mohamedshhahat1)

---

⭐ **Star this repo if you find it useful!**
