# Contributing to AI Traffic Cop System

Thank you for your interest in contributing! This document provides guidelines for development.

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/mohamedshhahat1/AI-TRAFFIC-COP-SYSTEM.git
   cd AI-TRAFFIC-COP-SYSTEM
   ```

2. **Install dependencies**
   ```bash
   make install  # or: pip install -r requirements.txt
   ```

3. **Download AI models**
   ```bash
   make models  # Downloads YOLOv8 Nano
   ```

4. **Run the backend**
   ```bash
   make run  # or: uvicorn backend.app.main:app --reload
   ```

5. **Run the frontend** (separate terminal)
   ```bash
   make run-frontend  # or: cd frontend && npm start
   ```

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `make test`
4. Run linter: `make lint`
5. Commit with a clear message
6. Open a Pull Request

## Code Style

- **Python**: Follow PEP 8. We use `ruff` for linting.
- **JavaScript**: ES6+ with React functional components.
- **Dart**: Follow Dart style guide.

## Commit Messages

Use conventional commits:
- `feat(scope): description` — New features
- `fix(scope): description` — Bug fixes
- `docs: description` — Documentation only
- `test: description` — Adding tests
- `refactor: description` — Code restructuring

## Testing

```bash
make test        # Run all tests
make test-cov    # Run with coverage report
```

- Write tests for new features
- Maintain minimum 30% coverage
- Test files go in `tests/`

## Project Structure

```
├── ai_engine/          # AI/ML modules (detection, tracking, prediction)
├── backend/            # FastAPI backend server
├── frontend/           # React dashboard
├── mobile_app/         # Flutter mobile app
├── configs/            # YAML configuration files
├── data/               # Data directory (videos, images, DB)
├── docker/             # Docker configuration
├── models/             # AI model weights (downloaded)
├── scripts/            # Utility scripts
└── tests/              # Test suite
```

## Questions?

Open a GitHub Issue for bugs, feature requests, or questions.
