# AGENTS.md - LLMGateway Project Guidelines

## Build/Lint/Test Commands

### Backend (FastAPI + Python)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements.txt  # For testing

# Run all tests
pytest tests/test_all.py -v

# Run single test file
pytest tests/test_all.py::TestEncryption -v

# Run single test method
pytest tests/test_all.py::TestEncryption::test_encrypt_decrypt_roundtrip -v

# Run tests with coverage
pytest tests/test_all.py -v --cov=backend

# Run FastAPI dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend - Vue (Port 80)
```bash
cd frontend

# Install dependencies
npm install

# Dev server
npm run dev

# Build production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

### Frontend - React (Port 88)
```bash
cd frontend-react

# Install dependencies
npm install

# Dev server
npm run dev

# Build production
npm run build

# Preview production build
npm run preview
```

### Docker (All Services)
```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend
docker compose up -d frontend
docker compose up -d frontend-react

# View logs
docker compose logs -f

# Stop all
docker compose down

# Rebuild
docker compose build --no-cache
```

## Code Style Guidelines

### Python (Backend)
- **Style**: Follow PEP 8
- **Imports**: Group imports - stdlib, third-party, local; sort alphabetically
- **Types**: Use type hints for function parameters and return values
- **Naming**: 
  - `snake_case` for functions, variables, methods
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Error Handling**: Use FastAPI HTTPException with appropriate status codes
- **Docstrings**: Use triple double quotes for docstrings
- **Line Length**: Max 100 characters
- **String Quotes**: Use double quotes for strings

### Vue 3 (frontend/)
- **Style**: Element Plus component conventions
- **Components**: `PascalCase` for component names
- **Composition API**: Use `<script setup>` syntax
- **Imports**: Group by Vue, third-party, local components, API services

### React (frontend-react/)
- **Style**: Ant Design 5.x patterns
- **Components**: `PascalCase` for component files
- **Hooks**: Custom hooks in `useHookName` format
- **Imports**: Group by React, third-party, local components, services

### Database/SQLAlchemy
- Use scoped sessions for thread safety
- Always close sessions in `finally` blocks
- Use proper transaction handling with `db.commit()` after modifications

### Testing
- Use pytest with async support (`@pytest.mark.asyncio`)
- Mock external dependencies (HTTP calls, etc.)
- Name test classes as `Test*` prefix
- Use descriptive test method names with underscores
- Include fixtures for shared test data

### Security
- Encrypt API keys using Fernet (see `config/encryption.py`)
- Never log sensitive information
- Use proper CORS settings in production
- Validate all user inputs with Pydantic models

### Git
- Write meaningful commit messages
- Don't commit `__pycache__`, `.pyc`, `node_modules`, or `venv/`
- Keep sensitive files (`.env`, API keys) out of version control
