# Quickstart Guide: WizLight Control System

## Prerequisites
- Python 3.11+
- UV package manager installed
- WiZ smart lights on local network
- Network that allows UDP broadcast (port 38899)

## Quick Setup

### 1. Project Initialization
```bash
# Clone/create project
cd wizsight

# Initialize UV project (if not already done)
uv init --app

# Install dependencies
uv add fastapi uvicorn pywizlight
uv add --dev pytest httpx pytest-asyncio
```

### 2. Start the System
```bash
# Start the backend server
uv run uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### 3. Access the Web Interface
1. Open browser to `http://localhost:8000`
2. Click "Scan for Lights" to discover devices
3. Control discovered lights using the interface

## API Usage Examples

### Discover Lights
```bash
# Scan entire network
curl http://localhost:8000/scan

# Scan specific network range  
curl "http://localhost:8000/scan?broadcast_address=192.168.1.255&timeout=10"
```

Expected response:
```json
{
  "scan_id": "12345678-1234-1234-1234-123456789abc",
  "status": "completed",
  "discovered_count": 2,
  "devices": [
    {
      "ip": "192.168.1.100",
      "mac": "AA:BB:CC:DD:EE:FF",
      "state": true,
      "brightness": 180,
      "colortemp": 4000,
      "available": true
    }
  ]
}
```

### Control Lights
```bash
# Toggle power state
curl -X POST http://localhost:8000/lights/192.168.1.100/toggle

# Set brightness
curl -X POST http://localhost:8000/lights/192.168.1.100/brightness \
  -H "Content-Type: application/json" \
  -d '{"brightness": 200, "force_on": true}'

# Set color temperature  
curl -X POST http://localhost:8000/lights/192.168.1.100/colortemp \
  -H "Content-Type: application/json" \
  -d '{"colortemp": 5000, "force_on": true}'

# Get current state
curl http://localhost:8000/lights/192.168.1.100/state
```

## Frontend Usage

### Scan and Display
1. Click **"Scan for Lights"** button
2. Wait for discovery to complete (5-10 seconds)
3. Available lights appear in the interface
4. Each light shows current state and controls

### Light Controls
- **Power Button**: Toggle on/off state
- **Brightness Slider**: Adjust 0-255 brightness
- **Color Temperature Slider**: Adjust warm (2700K) to cool (6500K)
- **Refresh**: Update current light state

### Error Handling
- Network timeouts show as "Device Unreachable"
- Invalid parameters show validation errors
- Discovery failures show "No lights found" message
- Connection errors display with retry options

## Testing Scenarios

### Basic Functionality Test
1. **Discovery Test**:
   - Start with no lights in interface
   - Click "Scan for Lights"
   - Verify lights appear within 10 seconds
   - Check each light shows correct IP and state

2. **Power Control Test**:
   - Toggle each discovered light on/off
   - Verify physical light matches interface state
   - Test rapid on/off operations

3. **Brightness Control Test**:
   - Set brightness to minimum (effectively 10%)
   - Set brightness to maximum (255)
   - Test intermediate values (50, 127, 200)
   - Verify smooth transitions

4. **Color Temperature Test**:
   - Set to warm white (2700K)
   - Set to cool white (6500K)
   - Test intermediate values (4000K, 5000K)
   - Verify color change is visible

### Error Scenario Testing
1. **Network Issues**:
   - Disconnect light from network
   - Attempt control operations
   - Verify appropriate error messages

2. **Invalid Parameters**:
   - Try brightness > 255 (should fail)
   - Try color temperature < 1000K (should fail)
   - Try invalid IP addresses

3. **Discovery Edge Cases**:
   - Scan with no lights on network
   - Scan with network isolated
   - Scan with different broadcast addresses

## Development Workflow

### Code Structure Validation
```bash
# Verify project structure matches plan
tree backend/ frontend/

# Expected:
# backend/
# ├── src/
# │   ├── api/          # FastAPI routes  
# │   ├── models/       # Pydantic models
# │   └── services/     # pywizlight wrapper
# └── tests/
# 
# frontend/
# ├── static/
# │   ├── index.html
# │   ├── app.js
# │   └── styles.css
# └── tests/
```

### Testing Commands
```bash
# Run backend tests
cd backend
uv run pytest

# Test API endpoints
uv run pytest tests/test_api.py -v

# Test pywizlight integration  
uv run pytest tests/test_integration.py -v

# Run with real lights (requires network setup)
uv run pytest tests/test_real_lights.py -v --real-lights
```

### Performance Validation
```bash
# Test response times
time curl http://localhost:8000/scan
time curl -X POST http://localhost:8000/lights/192.168.1.100/toggle

# Expected response times:
# - Discovery: < 5 seconds
# - Light control: < 500ms  
# - State queries: < 200ms
```

## Deployment Notes

### Local Network Setup
- Ensure lights and server on same network
- Verify UDP port 38899 not blocked by firewall
- Test broadcast addressing works correctly

### Production Considerations
- Set appropriate CORS settings for frontend domain
- Configure proper logging for debugging
- Consider rate limiting for API endpoints
- Add monitoring for light connectivity

### Troubleshooting

**"No lights found" during scan**:
- Verify lights are on same network
- Check UDP port 38899 accessibility
- Try specific broadcast address instead of 255.255.255.255

**"Device unreachable" errors**:
- Check light power and network connection
- Verify IP address hasn't changed
- Test with ping command first

**Slow response times**:
- Check network latency to lights
- Verify server isn't overloaded
- Consider network congestion issues

**Frontend not loading**:
- Verify backend server running on port 8000
- Check browser console for errors
- Confirm CORS settings if accessing from different domain