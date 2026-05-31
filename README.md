# 🚔 AI Traffic Cop System

> **Smart Traffic Enforcement & Analytics System** powered by AI, Computer Vision, and Deep Learning

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-green.svg)
![DeepSORT](https://img.shields.io/badge/DeepSORT-Tracking-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)
![React](https://img.shields.io/badge/React-Frontend-61DAFB.svg)
![Flutter](https://img.shields.io/badge/Flutter-Mobile-02569B.svg)
![Docker](https://img.shields.io/badge/Docker-Deploy-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🧠 Project Overview

The **AI Traffic Cop System** is an intelligent real-time surveillance system that uses **computer vision** and **AI** to:
- Monitor road traffic in real-time
- Detect traffic violations automatically
- Predict accidents before they happen
- Analyze city-wide congestion patterns
- Generate automated enforcement reports

Replaces traditional manual traffic monitoring with a **fully automated AI-powered pipeline**.

---

## 🏗️ System Architecture

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
        │   - Speed limit comparison                 │
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
        │  - Prioritize critical violations          │
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
        ┌────────────────────────────────────────────┐
        │            Backend API Layer               │
        │   FastAPI Server + WebSocket               │
        │   - Store violations in DB                 │
        │   - REST API for all services              │
        └─────────────┬──────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌──────────────────┐   ┌────────────────────┐  ┌────────────────────┐
│   Database       │   │   Dashboard UI     │  │  Alert System      │
│ PostgreSQL /     │   │ React + Flutter    │  │ SMS / Email / Push │
│ SQLite           │   │ - Live Monitoring  │  │ - Real-time alerts │
│                  │   │ - Statistics       │  │ - Webhooks         │
└──────────────────┘   └────────────────────┘  └────────────────────┘
```

---

## 📁 Project Structure

```
AI-Traffic-Cop-System/
│
├── ai_engine/                    # 🧠 Core AI Intelligence
│   ├── detection/
│   │   ├── yolo_detector.py     # YOLOv8 object detection
│   │   └── model_loader.py      # Model management
│   ├── tracking/
│   │   ├── deep_sort_tracker.py # DeepSORT tracking
│   │   └── object_tracker.py    # Track data structures
│   ├── speed_estimation/
│   │   └── speed_calculator.py  # Speed measurement
│   ├── violation_detection/
│   │   ├── speed_violation.py   # Speed limit detection
│   │   ├── red_light.py         # Red light running
│   │   ├── lane_violation.py    # Illegal lane changes
│   │   ├── parking_violation.py # Illegal parking
│   │   └── violation_engine.py  # Central orchestrator
│   ├── prediction/              # 🔮 AI Prediction Layer
│   │   ├── accident_predictor.py
│   │   └── congestion_analyzer.py
│   ├── smart_city/              # 🏙️ Smart City Integration
│   │   ├── multi_camera_fusion.py
│   │   └── city_analytics.py
│   ├── pipeline.py              # Main AI pipeline
│   └── utils.py                 # Utility functions
│
├── backend/                     # ⚙️ API Server
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
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
│   ├── database/
│   │   └── db_connection.py
│   └── requirements.txt
│
├── frontend/                    # 📊 Web Dashboard (React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── LiveCameraFeed.js
│   │   │   ├── ViolationTable.js
│   │   │   └── StatsCards.js
│   │   ├── pages/
│   │   │   ├── Dashboard.js
│   │   │   └── Violations.js
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.js
│   └── package.json
│
├── mobile_app/                  # 📱 Mobile App (Flutter)
│   ├── lib/
│   │   ├── screens/
│   │   │   ├── home.dart
│   │   │   └── violations.dart
│   │   ├── services/
│   │   │   └── api_service.dart
│   │   ├── widgets/
│   │   └── main.dart
│   └── pubspec.yaml
│
├── data/                        # 📦 Data
│   ├── videos/
│   ├── images/
│   └── annotations/
│
├── models/                      # 🧠 AI Models
│   └── README.md
│
├── configs/                     # ⚙️ Configuration
│   ├── settings.yaml
│   ├── camera_config.yaml
│   └── thresholds.yaml
│
├── scripts/                     # 🚀 Automation
│   ├── run_pipeline.py
│   ├── train_model.py
│   └── export_model.py
│
├── docs/                        # 📄 Documentation
│   ├── architecture.md
│   ├── api_docs.md
│   └── diagrams/
│
├── tests/                       # 🧪 Tests
│   ├── test_detection.py
│   ├── test_tracking.py
│   └── test_api.py
│
├── docker/                      # 🐳 Deployment
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🚀 Features

### Core AI Features
| Feature | Description |
|---------|-------------|
| 🎥 Real-time Detection | YOLOv8 vehicle/pedestrian/traffic light detection |
| 🎯 Multi-Object Tracking | DeepSORT persistent vehicle IDs |
| ⚡ Speed Estimation | Real-time speed calculation with calibration |
| 🚨 Violation Detection | Speed, red light, lane, parking violations |
| 🔮 Accident Prediction | TTC-based collision risk analysis |
| 🚦 Congestion Analysis | Real-time traffic density & flow monitoring |

### Smart City Features
| Feature | Description |
|---------|-------------|
| 📷 Multi-Camera Fusion | Cross-camera vehicle tracking |
| 🌍 City-Wide Analytics | Traffic patterns & peak hours |
| 🌱 Environmental Impact | CO2 estimation & air quality |
| 📊 Trend Prediction | Congestion forecasting |

### System Features
| Feature | Description |
|---------|-------------|
| 📡 REST API | Full FastAPI backend |
| 📊 Web Dashboard | React.js real-time UI |
| 📱 Mobile App | Flutter cross-platform |
| 🔔 Alert System | Email, SMS, Push, Webhook |
| 🐳 Docker | One-click deployment |
| 🗄️ Database | PostgreSQL / SQLite |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Object Detection | YOLOv8 (Ultralytics) |
| Object Tracking | DeepSORT |
| Computer Vision | OpenCV |
| ML Framework | PyTorch |
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL / SQLite |
| Frontend | React.js + Chart.js |
| Mobile | Flutter |
| Deployment | Docker + Docker Compose |
| Alerts | SMTP, Twilio, Firebase |

---

## ⚙️ Installation

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- Flutter SDK (for mobile)
- Docker (optional)

### Quick Start

```bash
# Clone
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM

# Install Python dependencies
pip install -r requirements.txt

# Run AI pipeline
python scripts/run_pipeline.py --source data/videos/sample.mp4 --display

# Run API server
uvicorn backend.app.main:app --reload --port 8000

# Run frontend
cd frontend && npm install && npm start

# Or use Docker (one-click)
cd docker && docker-compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/violations/` | List violations |
| GET | `/api/vehicles/` | List vehicles |
| GET | `/api/analytics/` | Statistics |
| GET | `/api/analytics/congestion` | Congestion data |
| WS | `/ws/live` | Live data stream |

📖 Full docs: [API Documentation](docs/api_docs.md)

---

## 🐳 Docker Deployment

```bash
cd docker
docker-compose up --build
```

Services:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:3000
- **Database**: localhost:5432

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 👤 Author

**Mohamed Shahat**
- GitHub: [@mohamedshhahat1](https://github.com/mohamedshhahat1)

---

⭐ **Star this repo if you find it useful!**
