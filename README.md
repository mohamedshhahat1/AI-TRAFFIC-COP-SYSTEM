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
│   ├── monitoring/                  # 📊 Logging & Monitoring
│   │   ├── logger.py               # Structured logging system
│   │   └── metrics.py              # Performance metrics & health
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

---

## 🔌 Backend ↔ AI Engine Integration

The backend **fully initializes the AIGateway on startup** and subscribes to the Event Bus:

```python
# backend/app/main.py (startup)

from ai_engine.api_bridge import AIGateway

ai_gateway = AIGateway(config)
ai_gateway.start()

# Subscribe to Event Bus → broadcast to WebSocket clients
ai_gateway.on_violation(lambda v: broadcast({"type": "violation", "data": v}))
ai_gateway.on_accident_risk(lambda r: broadcast({"type": "accident_risk", "data": r}))
ai_gateway.on_congestion_change(lambda c: broadcast({"type": "congestion", "data": c}))

# Direct Event Bus subscription (full features: wildcards, priority, replay)
ai_gateway.event_bus.on("tracking.update", lambda event: broadcast(event.data))
```

### Graceful Fallback

The system handles missing AI dependencies gracefully:

| Environment | Behavior |
|-------------|----------|
| **With GPU + AI packages** | ✅ Full pipeline + Event Bus + WebSocket broadcasting |
| **Without GPU / AI packages** | ✅ API still runs (API-only mode) — no crash |

```
Startup with AI:
  🚀 Starting AI Traffic Cop API...
  ✅ AI Gateway initialized - Event Bus subscriptions active
  ✅ API server ready

Startup without AI:
  🚀 Starting AI Traffic Cop API...
  ⚠️ AI Engine not available: No module named 'ultralytics'
  Running in API-only mode (no AI processing)
  ✅ API server ready
```

This means:
- **Production** (GPU server): Full AI + real-time events
- **Development** (laptop): API works for frontend/mobile development
- **Docker**: Everything runs together automatically

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
| 📊 Monitoring | Metrics, health scoring, Prometheus |
| 📝 Logging | Structured logs, rotation, alerting |
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
| Monitoring | Custom MetricsCollector + Loguru |
| API Gateway | Custom InferenceService |
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL / SQLite |
| Frontend | React.js |
| Mobile | Flutter |
| Deploy | Docker Compose |

---

## 🔄 Complete Workflow (Train → Run)

### Step 1: Setup (one time)
```bash
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### Step 2: Get Training Data
```bash
# Download from Roboflow (YOLO format) and extract:
unzip dataset.zip -d data/annotations/
```

### Step 3: Train
```bash
python scripts/train_model.py
# ⏳ Wait... (5-60 min depending on GPU/dataset size)
# ✅ Model saved to: models/training/traffic_cop_v1/weights/best.pt
```

### Step 4: Update Config
Edit `configs/settings.yaml`:
```yaml
detection:
  model: "models/training/traffic_cop_v1/weights/best.pt"
```

### Step 5: Run the System
```bash
python scripts/run_pipeline.py --source data/videos/traffic.mp4 --display
```

### Flow Summary:
```
Setup → Get Data → Train → Update Config → Run
  ↓        ↓         ↓          ↓            ↓
 pip    Roboflow   train.py   settings.yaml  run_pipeline.py
```

### ⚡ Skip Training (Quick Demo)
```bash
# YOLOv8 pre-trained already knows cars/trucks/people/traffic lights
# Just run — no training needed:
python scripts/run_pipeline.py --source data/videos/sample.mp4 --display
```

---

## 🖥️ Running on Windows

```bash
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1: AI Pipeline
python scripts/run_pipeline.py --source data/videos/sample.mp4 --display

# Terminal 2: API Server
uvicorn backend.app.main:app --reload --port 8000

# Terminal 3: Frontend Dashboard
cd frontend && npm install && npm start
```

**GPU (Optional):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

## 🐳 Running with Docker (One-Click)

```bash
# Prerequisites: Docker Desktop installed & running
cd AI-TRAFFIC-COP-SYSTEM/docker
docker-compose up --build

# API:       http://localhost:8000
# Dashboard: http://localhost:3000
```

Stop: `docker-compose down` | Rebuild: `docker-compose up --build`

---

## 📦 Training Datasets

### 🏆 Best Free Datasets (Ready for YOLOv8)

#### 1. Roboflow Universe (RECOMMENDED — Easiest)
| Dataset | Link | Contents |
|---------|------|----------|
| Traffic Detection | [roboflow.com/traffic](https://universe.roboflow.com/search?q=traffic) | Cars, trucks, buses, motorcycles |
| Traffic Lights | [roboflow.com/traffic-light](https://universe.roboflow.com/search?q=traffic+light) | Red/green/yellow states |
| Vehicle Detection | [roboflow.com/vehicle](https://universe.roboflow.com/search?q=vehicle+detection) | Multi-class vehicles |

> ✅ Export directly in **YOLO format** — no conversion needed

#### 2. Kaggle Datasets
| Dataset | Link |
|---------|------|
| Road Vehicle Images | [kaggle.com/road-vehicles](https://www.kaggle.com/datasets/ashfakyeafi/road-vehicle-images-dataset) |
| Car Object Detection | [kaggle.com/car-detection](https://www.kaggle.com/datasets/sshikamaru/car-object-detection) |
| Speed Estimation | [kaggle.com/speed-estimation](https://www.kaggle.com/datasets/kmader/speed-estimation-dataset) |
| LISA Traffic Lights | [kaggle.com/lisa-traffic](https://www.kaggle.com/datasets/mbornoe/lisa-traffic-light-dataset) |

#### 3. Research Datasets
| Dataset | Description | Link |
|---------|-------------|------|
| **COCO** | 80 classes (cars, trucks, traffic lights) | [cocodataset.org](https://cocodataset.org) |
| **KITTI** | Self-driving car data | [cvlibs.net/kitti](https://www.cvlibs.net/datasets/kitti/) |
| **BDD100K** | 100K driving videos with labels | [bdd100k.com](https://www.bdd100k.com) |
| **UA-DETRAC** | Traffic surveillance + tracking | [detrac-db.rit.albany.edu](https://detrac-db.rit.albany.edu) |

#### 4. YouTube Videos (for testing)
Search: "traffic camera footage 4K", "intersection camera", "dashcam compilation"

### ⚡ Quickest Path (5 min to start training)

```bash
# 1. Go to: https://universe.roboflow.com/search?q=traffic+vehicle+detection
# 2. Pick dataset → Download → Select "YOLOv8" format
# 3. Extract:
unzip dataset.zip -d data/annotations/

# 4. Structure should be:
# data/annotations/
# ├── data.yaml (rename to dataset.yaml)
# ├── train/images/ + train/labels/
# └── valid/images/ + valid/labels/

# 5. Train!
python scripts/train_model.py
```

### 📝 Label Your Own Data
1. Record traffic video (phone or YouTube)
2. Extract frames: `ffmpeg -i video.mp4 -vf "fps=2" frames/frame_%04d.jpg`
3. Label at [app.roboflow.com](https://app.roboflow.com) → export YOLO format
4. Train: `python scripts/train_model.py`

### 💡 Tips
- **Start small**: 200-500 images is enough for a demo
- **YOLOv8 pre-trained** already knows cars/trucks — fine-tuning improves your camera angle
- **Roboflow** has free augmentation (flip, rotate, blur) that 3x your dataset
- **Speed estimation** needs no labeled data — just calibrate `pixel_to_meter`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System + AI Gateway health |
| GET | `/api/violations/` | List violations |
| GET | `/api/vehicles/` | Tracked vehicles |
| GET | `/api/analytics/` | Statistics |
| GET | `/api/events/metrics` | Event Bus metrics |
| GET | `/api/events/history` | Recent events |
| GET | `/api/analytics/health` | System health score |
| GET | `/api/analytics/metrics` | Performance metrics (p50/p95/p99) |
| GET | `/api/analytics/metrics/prometheus` | Prometheus export |
| GET | `/api/analytics/logs` | Recent structured logs |
| GET | `/api/analytics/logs/stats` | Log statistics |
| WS | `/ws/live` | Real-time event stream |

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Files** | 98 |
| **Total Lines of Code** | 9,331 |
| **Total Commits** | 50 |
| **Architecture Layers** | 13 |

### By Language

| Language | Files | Lines |
|----------|-------|-------|
| Python | 56 | 5,931 |
| Dart (Flutter) | 9 | 1,144 |
| JavaScript (React) | 10 | 725 |
| CSS | 1 | 268 |
| Markdown/Docs | 4 | 903 |
| YAML/Config | 5 | — |
| Docker | 2 | — |
| HTML | 1 | — |

### Architecture Layers (13)

```
AI Engine (9 modules):
├── detection/              → YOLOv8 Object Detection
├── tracking/               → DeepSORT Multi-Object Tracking
├── speed_estimation/       → Speed Calculation
├── violation_detection/    → Violation Engine (4 types)
├── prediction/             → Accident & Congestion AI
├── smart_city/             → Multi-Camera & City Analytics
├── event_bus/              → Event-Driven Architecture (Pub/Sub)
├── api_bridge/             → API Gateway / Communication Layer
└── monitoring/             → Logging & Metrics (Observability)

Full Stack (4 modules):
├── backend/                → FastAPI REST Server + WebSocket
├── frontend/               → React.js Real-time Dashboard
├── mobile_app/             → Flutter Cross-Platform App
└── docker/                 → Docker Deployment (one-click)
```

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**Mohamed Shahat** — [@mohamedshhahat1](https://github.com/mohamedshhahat1)

---

⭐ **Star this repo if you find it useful!**
