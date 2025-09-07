# WizSight Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-07

## Active Technologies
- Python 3.11+ (001-lets-create-a)
- FastAPI + uvicorn (001-lets-create-a)
- pywizlight library (001-lets-create-a)
- Vanilla HTML/JS/CSS (001-lets-create-a)
- UV package manager (001-lets-create-a)

## Project Structure
```
backend/
├── src/
│   ├── api/          # FastAPI routes
│   ├── models/       # Pydantic models  
│   └── services/     # pywizlight wrapper
└── tests/

frontend/
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── tests/
```

## Commands
```bash
# Start development server
uv run uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests  
uv run pytest

# Install dependencies
uv add <package>
uv add --dev <dev-package>
```

## Code Style
- Follow async/await patterns for all pywizlight operations
- Use Pydantic models for API validation
- HTTP status codes: 400 (bad params), 404 (not found), 408 (timeout), 500 (server error)
- JSON API responses with structured error messages
- Parameter validation: brightness (0-255), colortemp (1000-10000K)

## Architecture Notes
- Stateless API design - no caching or persistent state
- Each request creates fresh wizlight instances (UDP is stateless)
- Real-time state fetching for accuracy
- UDP broadcast discovery on port 38899
- FastAPI serves static frontend files

## Error Handling
- WizLightError exceptions map to HTTP 400
- ValueError exceptions map to HTTP 422  
- asyncio.TimeoutError maps to HTTP 408
- Network errors classified with error codes: DEVICE_UNREACHABLE, INVALID_PARAMETERS, DEVICE_BUSY, NETWORK_ERROR

## Recent Changes
- 001-lets-create-a: Added WizLight control system with FastAPI backend and HTML/JS frontend

<!-- MANUAL ADDITIONS START -->
<!-- Add your manual additions here - they will be preserved across updates -->
<!-- MANUAL ADDITIONS END -->