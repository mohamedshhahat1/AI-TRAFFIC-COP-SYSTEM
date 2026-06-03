# 🚔 AI Traffic Cop System

[![CI](https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM/actions/workflows/ci.yml/badge.svg)](https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM/actions)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![React](https://img.shields.io/badge/React-18-61DAFB.svg)
![Flutter](https://img.shields.io/badge/Flutter-Mobile-02569B.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-red.svg)

An **intelligent traffic surveillance and enforcement platform** combining deep learning computer vision, real-time tracking, and smart city analytics. Detects traffic violations, predicts accidents, recognizes license plates, and optimizes traffic signal timing using reinforcement learning.

---

## 🌟 Features

### 🎯 Core AI Engine
| Feature | Technology | Description |
|---------|-----------|-------------|
| **Object Detection** | YOLOv8 (Ultralytics) | Real-time vehicle, pedestrian, and traffic light detection |
| **Multi-Object Tracking** | DeepSORT | Persistent vehicle tracking with unique IDs across frames |
| **Speed Estimation** | Pixel-to-World Calibration | Per-camera configurable speed measurement with perspective transform |
| **Violation Detection** | Rule-based + CV | Speed violations, red light running, illegal lane changes, parking violations |
| **Accident Prediction** | Physics-based TTC | Time-to-collision analysis with trajectory prediction and risk scoring |
| **License Plate Recognition (ANPR)** | OCR Pipeline | Automatic plate detection, character recognition, and owner database lookup |
| **RL Signal Optimization** | PPO/DQN (Stable-Baselines3) | Reinforcement learning for adaptive traffic signal control |
| **Multi-Camera Fusion** | Re-ID + Spatial | Cross-camera vehicle tracking and city-wide analytics |

### 🖥️ Backend (FastAPI)
- **RESTful API** with full CRUD for violations, vehicles, plates, analytics
- **WebSocket** real-time event streaming (violations, tracking, accidents, RL decisions)
- **Event Bus** architecture (pub/sub) for decoupled components
- **SQLite/PostgreSQL** database with async SQLAlchemy ORM
- **API Key authentication** with rate limiting (60 req/min)
- **Prometheus-compatible** metrics export
- **Health monitoring** with component status tracking
- **File upload** with validation, sanitization, and size limits

### 📊 Frontend (React)
- **Real-time Dashboard** with live camera feed (MJPEG streaming)
- **Violation History** with type/severity filtering
- **Traffic Heatmap** showing congestion zones from live data
- **Detection Statistics** with per-class breakdown
- **Accident Risk Panel** with TTC alerts
- **Detected Plates** display with owner info (ANPR)
- **Multi-Camera Grid** for simultaneous monitoring
- **System Architecture** live performance counters
- **Results & Evaluation** page with all metrics

### 📱 Mobile App (Flutter)
- Real-time violation alerts via WebSocket
- Camera monitoring and control
- Event history browsing
- System health dashboard

### 🤖 RL Traffic Signal Control
- **Custom Gymnasium environment** simulating intersection traffic
- **PPO and DQN agents** trained with Stable-Baselines3
- **Live integration** — feeds from CV pipeline to RL decisions
- **Reward functions** balancing throughput, wait time, and fairness
- **Signal controller** that executes RL decisions on traffic lights
- **TensorBoard** training visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│   Dashboard │ Violations │ Monitoring │ Results │ Multi-Camera   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP / WebSocket
┌───────────────────────────────┴─────────────────────────────────┐
│                     Backend (FastAPI)                             │
│   Auth │ Rate Limit │ Routes │ WebSocket │ Event Bus │ DB        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                      AI Engine                                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ YOLOv8   │→│ DeepSORT │→│  Speed      │→│  Violations   │  │
│  │ Detector │  │ Tracker  │  │  Estimator │  │  Engine       │  │
│  └──────────┘  └──────────┘  └────────────┘  └──────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Accident │  │   ANPR   │  │ Multi-Cam  │  │  RL Signal   │  │
│  │ Predictor│  │ Pipeline │  │  Fusion    │  │  Controller  │  │
│  └──────────┘  └──────────┘  └────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pip

### 1. Clone & Install

```bash
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM
make install          # pip install -r requirements.txt
```

### 2. Download AI Models

```bash
make models           # Downloads YOLOv8 Nano (~6MB)
# Or for better accuracy:
python scripts/download_models.py --model yolov8s
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (API_KEY, SMTP, etc.)
```

### 4. Run Backend

```bash
make run              # uvicorn backend.app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/api/docs (when DEBUG=true)
```

### 5. Run Frontend

```bash
make run-frontend     # cd frontend && npm install && npm start
# Dashboard: http://localhost:3000
```

### 6. Docker (Alternative)

```bash
make docker-run       # docker-compose up --build
```

---

## 📁 Project Structure

```
AI-TRAFFIC-COP-SYSTEM/
├── ai_engine/                  # Core AI modules
│   ├── detection/              # YOLOv8 object detection
│   ├── tracking/               # DeepSORT multi-object tracking
│   ├── speed_estimation/       # Speed calculation + calibration
│   ├── violation_detection/    # Speed, red light, lane, parking
│   ├── prediction/             # Accident prediction (TTC)
│   ├── plate_recognition/      # ANPR pipeline (detect → OCR → match)
│   ├── smart_city/             # Multi-camera fusion + analytics
│   ├── event_bus/              # Pub/sub event system
│   ├── api_bridge/             # InferenceService + AIGateway
│   ├── monitoring/             # Logging + metrics
│   └── pipeline.py             # Main processing pipeline
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Environment-based settings
│   │   ├── middleware/         # Auth + rate limiting
│   │   ├── routes/             # API endpoints (violations, vehicles, plates, analytics)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── services/           # DB + alert services
│   │   └── video_processor.py  # Frame processing + annotation
│   └── requirements.txt
├── frontend/                   # React dashboard
│   └── src/
│       ├── components/         # UI components (camera, heatmap, plates, etc.)
│       ├── pages/              # Dashboard, Violations, Results, Monitoring
│       └── services/           # API service layer
├── mobile_app/                 # Flutter mobile app
│   └── lib/
│       ├── screens/            # App screens
│       ├── services/           # API + event services
│       └── widgets/            # Reusable widgets
├── rl_signal_control/          # Reinforcement Learning module
│   ├── environment/            # Gymnasium traffic environment
│   ├── agents/                 # PPO, DQN agents
│   ├── training/               # Train + evaluate scripts
│   └── integration/            # Live RL ↔ CV bridge
├── configs/                    # YAML configuration
├── docker/                     # Docker deployment
├── scripts/                    # Utility scripts (download, train, export)
├── tests/                      # Comprehensive test suite
├── data/                       # Data directory (videos, annotations)
├── models/                     # AI model weights
├── .github/workflows/          # CI/CD pipeline
├── .env.example                # Environment variables template
├── Makefile                    # Standardized commands
├── pyproject.toml              # pytest + coverage config
├── requirements.txt            # Python dependencies (pinned)
└── CONTRIBUTING.md             # Development guidelines
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode + API docs | `false` |
| `PORT` | Backend server port | `8000` |
| `DATABASE_URL` | DB connection string | SQLite |
| `API_KEY` | Authentication key (empty = dev mode) | `` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | localhost |
| `RATE_LIMIT_PER_MINUTE` | Max requests/IP/minute | `60` |
| `SMTP_HOST` | Alert email server | `smtp.gmail.com` |
| `ALERT_EMAIL` | Violation alert recipient | `` |
| `REACT_APP_API_URL` | Frontend API URL | `/api` |

### Per-Camera Calibration

```yaml
# configs/camera_config.yaml
cameras:
  - id: "cam_01"
    location: "Main Street"
    pixel_to_meter: 0.048    # Calibrated per camera
    speed_limit: 50.0         # Zone speed limit (km/h)
    fps: 25                   # Camera FPS
```

---

## 🧪 Testing

```bash
make test             # Run all tests
make test-cov         # With coverage report
make lint             # Code style (ruff)
```

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| GET | `/api/violations/` | No | List violations |
| POST | `/api/violations/` | No | Create violation |
| DELETE | `/api/violations/{id}` | ✅ | Delete violation |
| GET | `/api/vehicles/` | No | List vehicles |
| GET | `/api/analytics/` | No | System analytics |
| GET | `/api/analytics/heatmap` | No | Congestion zones |
| GET | `/api/analytics/metrics/prometheus` | No | Prometheus metrics |
| POST | `/api/camera/start` | ✅ | Start AI processing |
| POST | `/api/camera/stop` | ✅ | Stop processing |
| GET | `/api/camera/feed` | No | MJPEG video stream |
| POST | `/api/camera/upload` | ✅ | Upload video |
| GET | `/api/plates/` | No | Detected plates |
| WS | `/ws/live?token=KEY` | ✅* | Real-time events |

*WebSocket auth required only when `API_KEY` is set.

---

## 🔒 Security

- ✅ API Key Authentication (sensitive endpoints)
- ✅ Rate Limiting (60 req/min per IP)
- ✅ File Upload Sanitization (extension + size + path validation)
- ✅ CORS Restriction (explicit origins, no wildcard)
- ✅ WebSocket Token Auth
- ✅ Non-root Docker Container
- ✅ API Docs hidden in production

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Detection | YOLOv8 (Ultralytics) |
| Tracking | DeepSORT |
| Speed | Pixel-to-World + Perspective Transform |
| Prediction | Physics-based TTC |
| ANPR | Plate Detection + OCR |
| RL | PPO/DQN (Stable-Baselines3 + Gymnasium) |
| Backend | FastAPI + SQLAlchemy + WebSockets |
| Frontend | React.js |
| Mobile | Flutter |
| Database | SQLite / PostgreSQL |
| Events | Custom Event Bus (Pub/Sub) |
| Metrics | Prometheus-compatible |
| CI/CD | GitHub Actions |
| Deploy | Docker + Docker Compose |
| CV | OpenCV + PyTorch |

---

## 📄 License

This project is for educational and research purposes.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

**Built with ❤️ by Mohamed Shahat**
