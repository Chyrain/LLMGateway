# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLMGateway (灵模网关) is a free LLM model aggregation gateway that provides:
- Multi-model support (OpenAI, Claude, Qwen, 智谱清言, 通义千问, MiniMax, DeepSeek, 月之暗面, etc.)
- Automatic model switching when quota is exhausted
- Real-time quota monitoring
- Request logging and operation logging
- Admin dashboard with dual frontends (Vue 3 and React)

## Architecture

### Components
- **Backend** (FastAPI + SQLAlchemy + SQLite): API server, gateway logic, database
- **Vue Frontend** (Element Plus): Default admin UI on port 80
- **React Frontend** (Ant Design): Alternative admin UI on port 88

### Key Backend Files
- `backend/main.py`: FastAPI application entry, router registration, middleware setup
- `backend/services/gateway_core.py`: Core gateway logic - request routing, model selection, auto-switching
- `backend/services/quota_monitor.py`: Quota tracking and monitoring
- `backend/services/model_switcher.py`: Model fallback/switching logic
- `backend/routers/`: API endpoints (auth, config, logs, notifications, stats)
- `backend/models/`: SQLAlchemy models (model_config, quota_stat, operation_log, system_config)
- `backend/config/encryption.py`: Fernet encryption for API keys

### Data Flow
1. Client requests arrive at gateway endpoint
2. `gateway_core.py` selects model (manual or auto-switch mode)
3. Request forwarded to LLM provider with encrypted API key
4. Response logged to `operation_log` table
5. Quota updated in `quota_stat` table

## Commands

### Development
```bash
# Backend
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Vue Frontend (port 80)
cd frontend && npm run dev

# React Frontend (port 88)
cd frontend-react && npm run dev
```

### Docker
```bash
docker compose up -d              # Start all services
docker compose logs -f            # View logs
docker compose down               # Stop all
```

### Testing
```bash
cd backend
pytest tests/test_all.py -v                    # Run all tests
pytest tests/test_all.py::TestEncryption -v   # Run specific test class
pytest tests/test_all.py -v --cov=backend     # With coverage
```

## API Access

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Gateway: http://localhost:8080
- Vue Frontend: http://localhost:80 (default admin: admin/admin123)
- React Frontend: http://localhost:88

## Environment Variables

Key variables in `.env`:
- `DB_TYPE`: Database type (sqlite)
- `DB_PATH`: Database file path
- `ENCRYPT_KEY`: Fernet encryption key for API keys
- `API_PORT`: Backend port (8000)
- `GATEWAY_PORT`: Gateway port (8080)
- `SWITCH_THRESHOLD`: Auto-switch threshold percentage
- `SYNC_INTERVAL`: Quota sync interval in seconds
