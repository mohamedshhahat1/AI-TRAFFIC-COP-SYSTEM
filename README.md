# 🚔 AI Traffic Cop System

> Smart Traffic Enforcement & Analytics System powered by AI and Computer Vision

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Object%20Detection-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🧠 Project Overview

The **AI Traffic Cop System** is an intelligent real-time surveillance system that uses **computer vision** and **AI** to monitor road traffic, detect violations, analyze driving behavior, and generate automated reports.

The system replaces traditional manual traffic monitoring with a fully automated AI-powered pipeline that works in real time using camera feeds.

## 🏗️ System Architecture

```
Camera Feed → AI Vision Layer → Tracking Layer → Decision Engine → Backend → Dashboard + Alerts
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI TRAFFIC COP SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Camera   │───▶│  YOLOv8  │───▶│ DeepSORT │───▶│  Speed   │      │
│  │  Feed     │    │Detection │    │ Tracking │    │Estimation│      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│                                                          │            │
│                                                          ▼            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Alert   │◀───│ Dashboard│◀───│  Backend │◀───│Violation │      │
│  │  System  │    │          │    │  (API)   │    │Detection │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
AI-TRAFFIC-COP-SYSTEM/
├── src/
│   ├── input_layer/          # Camera feed & video input
│   ├── vision_layer/         # YOLOv8 object detection
│   ├── tracking_layer/       # DeepSORT vehicle tracking
│   ├── speed_estimation/     # Speed calculation
│   ├── violation_detection/  # Violation detection engine
│   ├── decision_engine/      # AI decision-making
│   ├── backend/              # FastAPI server
│   ├── dashboard/            # Web dashboard
│   └── alerts/               # Notification system
├── config/                   # Configuration files
├── models/                   # Pre-trained models
├── data/
│   ├── videos/              # Test video files
│   ├── images/              # Captured images
│   └── violations/          # Violation records
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── main.py                  # Main entry point
└── README.md
```

## 🚀 Features

### Core Features
- 🎥 **Real-time Video Processing** - Live CCTV/RTSP stream analysis
- 🚗 **Vehicle Detection** - Cars, trucks, motorbikes, buses
- 🚶 **Pedestrian Detection** - Safety monitoring
- 🚦 **Traffic Light Recognition** - State detection (red/green/yellow)
- 📊 **Speed Estimation** - Real-time speed calculation
- 🔍 **Vehicle Tracking** - Persistent ID across frames

### Violation Detection
- 🔴 **Speed Violations** - Exceeding speed limits
- 🚦 **Red Light Running** - Crossing during red signal
- 🛣️ **Lane Violations** - Illegal lane changes
- 🚫 **Illegal Parking** - Unauthorized stationary vehicles
- 📵 **Driver Behavior** - Mobile phone usage detection

### System Features
- 📡 **REST API** - Full backend with FastAPI
- 📊 **Dashboard** - Real-time monitoring interface
- 🚨 **Alerts** - Push, email, and SMS notifications
- 🗄️ **Database** - PostgreSQL violation storage
- 📈 **Analytics** - Traffic statistics and reports

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Object Detection | YOLOv8 (Ultralytics) |
| Object Tracking | DeepSORT |
| Computer Vision | OpenCV |
| Backend API | FastAPI |
| Database | PostgreSQL |
| Dashboard | HTML/CSS/JS + Chart.js |
| Alerts | SMTP, Twilio, Firebase |
| ML Framework | PyTorch |

## ⚙️ Installation

### Prerequisites
- Python 3.9+
- PostgreSQL
- CUDA (optional, for GPU acceleration)

### Setup

```bash
# Clone the repository
git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
cd AI-TRAFFIC-COP-SYSTEM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Setup database
python -m src.backend.database.init_db

# Download YOLO model
python -m src.vision_layer.download_model

# Run the system
python main.py
```

## 🚀 Usage

### Start the full system:
```bash
python main.py
```

### Start only the API server:
```bash
uvicorn src.backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Process a video file:
```bash
python main.py --source data/videos/sample.mp4
```

### Connect to RTSP camera:
```bash
python main.py --source rtsp://camera-ip:554/stream
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/violations` | List all violations |
| GET | `/api/violations/{id}` | Get violation details |
| GET | `/api/vehicles` | List tracked vehicles |
| GET | `/api/statistics` | Traffic statistics |
| POST | `/api/camera/start` | Start camera feed |
| POST | `/api/camera/stop` | Stop camera feed |
| GET | `/api/alerts` | List alerts |
| WS | `/ws/live-feed` | Live video stream |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Mohamed Shahat**
- GitHub: [@mohamedshhahat1](https://github.com/mohamedshhahat1)

---

⭐ Star this repo if you find it useful!
