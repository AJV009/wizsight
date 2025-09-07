# Data Model: WizLight Control System

## Core Entities

### LightDevice
**Purpose**: Represents a discovered WiZ smart light with its current state and capabilities

**Fields**:
- `ip`: string (required) - IP address of the light on local network
- `mac`: string (optional) - MAC address for device identification
- `name`: string (optional) - User-friendly device name if available
- `state`: boolean (required) - Current power state (on/off)
- `brightness`: integer (0-255) - Current brightness level
- `rgb`: tuple[int, int, int] (optional) - Current RGB color values (0-255 each)
- `colortemp`: integer (optional) - Current color temperature in Kelvin (1000-10000)
- `scene`: integer (optional) - Current scene ID if active (1-37)
- `last_seen`: datetime - Timestamp of last successful communication
- `available`: boolean - Whether device is currently reachable

**Validation Rules**:
- IP must be valid IPv4 format
- Brightness range: 0-255, but effective minimum is 10% when on
- RGB values must be 0-255 for each channel
- Color temperature range: 1000K-10000K
- Scene ID range: 1-37

**State Transitions**:
- `available: true → false` when device becomes unreachable
- `state: false → true` when light is turned on
- `brightness` changes only affect display when `state: true`
- RGB and colortemp are mutually exclusive (setting one clears the other)

### NetworkScan
**Purpose**: Represents a network discovery operation and its results

**Fields**:
- `scan_id`: string (UUID) - Unique identifier for scan operation
- `broadcast_address`: string - Network broadcast address used
- `started_at`: datetime - When scan was initiated
- `completed_at`: datetime (optional) - When scan finished
- `timeout_seconds`: float - Discovery timeout setting
- `status`: enum ["in_progress", "completed", "failed"] - Current scan state
- `discovered_count`: integer - Number of lights found
- `error_message`: string (optional) - Error details if scan failed

**Validation Rules**:
- Broadcast address must be valid IPv4 broadcast format
- Timeout must be positive float (1.0-30.0 seconds)
- Status transitions: in_progress → completed|failed

### LightControlRequest  
**Purpose**: Represents a user's request to change light settings

**Fields**:
- `target_ip`: string (required) - IP address of light to control
- `action`: enum ["toggle", "set_brightness", "set_colortemp", "set_rgb", "set_scene"]
- `brightness`: integer (optional) - Target brightness (0-255)
- `rgb`: tuple[int, int, int] (optional) - Target RGB values
- `colortemp`: integer (optional) - Target color temperature (1000-10000K)
- `scene`: integer (optional) - Scene ID to activate (1-37)
- `requested_at`: datetime - When request was made
- `force_on`: boolean (default: true) - Whether to turn light on with changes

**Validation Rules**:
- Target IP must be valid IPv4 format
- Action must match provided parameters
- Parameter ranges match LightDevice validation
- RGB and colortemp are mutually exclusive
- Scene setting clears RGB and colortemp values

### LightControlResponse
**Purpose**: Results of a light control operation

**Fields**:
- `request_id`: string - Reference to originating request
- `target_ip`: string - IP address that was controlled
- `success`: boolean - Whether operation succeeded
- `previous_state`: LightDevice (optional) - State before change
- `new_state`: LightDevice (optional) - State after change if successful
- `error_code`: string (optional) - Error classification if failed
- `error_message`: string (optional) - Human-readable error description
- `response_time_ms`: float - Operation duration in milliseconds
- `completed_at`: datetime - When operation finished

**Error Codes**:
- `DEVICE_UNREACHABLE` - Network timeout or connection failure
- `INVALID_PARAMETERS` - Parameter validation failed
- `DEVICE_BUSY` - Light rejected command (rare)
- `NETWORK_ERROR` - UDP communication failure
- `UNKNOWN_ERROR` - Unexpected failure

## Relationships

### Discovery to Devices
- One NetworkScan can discover multiple LightDevices
- LightDevices exist independently after discovery
- Scans don't modify existing device states

### Control Operations
- Each LightControlRequest targets exactly one LightDevice
- Multiple requests can target same device concurrently
- Responses contain before/after state snapshots

### State Consistency
- LightDevice state reflects last known values
- Control operations update device state on success
- Failed operations don't modify device state
- Stale device states marked as unavailable

## Data Flow Patterns

### Discovery Flow
1. User initiates scan → NetworkScan created with "in_progress" status
2. UDP broadcast sent to network
3. Responses processed → LightDevice entities created/updated
4. NetworkScan marked "completed" with device count
5. Frontend receives list of available devices

### Control Flow  
1. User action → LightControlRequest created
2. Current device state fetched (for toggle logic)
3. Control command sent via pywizlight
4. Success: Device state updated, positive response
5. Failure: Error response with classification

### State Synchronization
- No automatic polling or push updates
- Frontend requests fresh state when needed
- State queries always fetch current values from device
- Cached states marked with last_seen timestamp

## Serialization Formats

### API Request/Response JSON
```json
{
  "lightDevice": {
    "ip": "192.168.1.100",
    "mac": "AA:BB:CC:DD:EE:FF",
    "name": "Living Room Light",
    "state": true,
    "brightness": 180,
    "colortemp": 4000,
    "available": true,
    "last_seen": "2025-09-07T10:30:45Z"
  }
}
```

### Control Request JSON
```json
{
  "action": "set_brightness",
  "brightness": 200,
  "force_on": true
}
```

### Discovery Response JSON
```json
{
  "scan_id": "uuid-here",
  "status": "completed", 
  "discovered_count": 3,
  "devices": [
    {"ip": "192.168.1.100", "available": true, ...},
    {"ip": "192.168.1.101", "available": true, ...}
  ],
  "completed_at": "2025-09-07T10:30:45Z"
}
```