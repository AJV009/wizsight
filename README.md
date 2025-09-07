# WizSight

A simple web dashboard for discovering and controlling WiZ smart lights on your network.

## Features

- **Network Discovery**: Scan your network to find WiZ lights automatically
- **Manual Control**: Toggle lights, adjust brightness, and set color temperature
- **Quick Presets**: One-click warm/neutral/cool color temperature presets
- **Lighting Scenarios**: Pre-configured mood lighting (Cozy, Focus, Daylight, etc.)
- **Real-time Dashboard**: No-refresh interface with live status updates

## Quick Start

```bash
# Clone and enter the project
cd wizsight

# Launch the application
./launch.sh
```

Open http://localhost:8001 (or 8002 if 8001 is busy) in your browser.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Python 3.11+
- WiZ lights connected to the same network

## Development

```bash
# Install dependencies
cd backend
uv sync

# Run tests
uv run pytest

# Start development server
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
```

## API

- `GET /scan` - Discover lights on network
- `POST /lights/{ip}/toggle` - Toggle light on/off
- `POST /lights/{ip}/brightness` - Set brightness (0-255)
- `POST /lights/{ip}/colortemp` - Set color temperature (1000-10000K)
- `GET /lights/{ip}/state` - Get light state
- `GET /docs` - Interactive API documentation

## License

MIT