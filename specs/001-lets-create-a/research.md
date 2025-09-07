# Research: WizLight Control System

## Technology Decisions

### Backend Framework
**Decision**: FastAPI with uvicorn
**Rationale**: 
- Native async/await support required for pywizlight compatibility
- Automatic OpenAPI schema generation for API documentation
- High performance for real-time light control operations
- Built-in data validation and serialization

**Alternatives considered**: 
- Flask: Lacks native async support, would require additional complexity
- Django: Too heavyweight for simple API, poor async support for this use case

### Light Control Library
**Decision**: pywizlight library
**Rationale**:
- Official Python connector for WiZ smart lights
- Mature async UDP implementation with built-in retry logic
- Comprehensive feature support (discovery, power, brightness, color temp)
- Active maintenance and documentation

**Alternatives considered**: 
- Direct UDP implementation: Would require reimplementing discovery protocol and error handling
- Third-party alternatives: Limited options, pywizlight is most established

### Frontend Approach
**Decision**: Vanilla HTML/JS/CSS (no frameworks)
**Rationale**:
- Minimal complexity as requested by user requirements
- No build process or dependencies needed
- Direct API integration sufficient for simple UI
- Fast loading and execution on local network

**Alternatives considered**: 
- React/Vue: Added complexity and build process not justified for simple interface
- Server-side rendering: Would add unnecessary backend templating complexity

## Implementation Patterns

### API Design
**Decision**: RESTful HTTP endpoints with JSON responses
**Rationale**:
- Standard web API patterns familiar to developers
- FastAPI automatic validation and documentation
- Easy integration with vanilla JavaScript fetch()
- Clear separation between discovery and control operations

**Key Endpoints**:
- `GET /scan` - Discover lights on network
- `POST /lights/{ip}/toggle` - Toggle power state
- `POST /lights/{ip}/brightness` - Set brightness (0-255)
- `POST /lights/{ip}/colortemp` - Set color temperature (1000-10000K)
- `GET /lights/{ip}/state` - Get current light state

### Error Handling Strategy
**Decision**: HTTP status codes with structured JSON error responses
**Rationale**:
- Standard web API error handling patterns
- Frontend can display user-friendly error messages
- Proper timeout and network error classification

**Error Categories**:
- 400: Invalid parameters (brightness out of range)
- 404: Light not found/unreachable
- 408: Network timeout
- 500: Unexpected server errors

### State Management
**Decision**: Stateless API with real-time state fetching
**Rationale**:
- UDP-based pywizlight is inherently stateless
- Avoids state synchronization issues between multiple clients
- Real-time accuracy for light states
- Simpler implementation and debugging

**Pattern**:
- Each API request creates fresh wizlight instance
- No persistent connections or caching
- Frontend polls for state updates when needed

### Async Implementation
**Decision**: Full async/await pattern throughout stack
**Rationale**:
- Required for pywizlight compatibility
- Non-blocking operations for multiple light control
- Better performance for concurrent requests
- FastAPI async advantages

**Implementation**:
- All API endpoints marked as async
- Proper exception handling for async operations
- Timeout management with asyncio.wait_for()
- Background task support for discovery operations

### Network Discovery
**Decision**: Broadcast-based discovery with configurable network scope
**Rationale**:
- Uses pywizlight built-in UDP broadcast discovery
- Allows network-specific scanning for better performance
- Handles network topology variations
- Built-in error handling for discovery failures

**Configuration**:
- Default broadcast address: 255.255.255.255 (whole network)
- Configurable per network setup
- 5-second discovery timeout
- Graceful handling of empty discovery results

### Project Structure
**Decision**: backend/frontend separation with shared static serving
**Rationale**:
- Clear separation of concerns
- FastAPI can serve static files for frontend
- Simple deployment as single process
- Development-friendly structure

**Structure**:
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

### Development Environment
**Decision**: UV-based Python project management
**Rationale**:
- Fast dependency resolution and installation
- Modern Python project management
- Virtual environment management
- Consistent across development machines

**Configuration**:
- Python 3.11+ requirement (pywizlight compatibility)
- UV for dependency management
- pyproject.toml configuration
- Development and production dependency separation

## Performance Considerations

### Response Time Targets
- Light control operations: <500ms
- Network discovery: <5 seconds
- State queries: <200ms

### Concurrency Handling
- FastAPI async request handling
- Multiple light control operations in parallel
- Non-blocking discovery operations
- Proper timeout management

### Network Optimization
- UDP packet efficiency (pywizlight built-in)
- Retry logic with exponential backoff
- Broadcast address optimization per network
- Error recovery for transient network issues

## Security Considerations

### Local Network Scope
- System operates only on local network
- No external internet connectivity required
- No authentication required (trusted local environment)
- No persistent data storage

### Input Validation
- Parameter range validation (brightness, color temp)
- IP address format validation
- JSON schema validation via FastAPI
- Error message sanitization

## Testing Strategy

### Backend Testing
- Unit tests for service layer
- Integration tests for API endpoints
- Mock pywizlight for offline testing
- Real light testing for validation

### Frontend Testing
- Manual testing with real lights
- Error scenario simulation
- Cross-browser compatibility testing
- Network failure handling validation

### End-to-End Testing
- Full discovery and control workflow
- Multiple light scenarios
- Error recovery testing
- Performance validation under load