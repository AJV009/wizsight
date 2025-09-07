/**
 * WizSight Frontend Application
 * Simple JavaScript client for controlling WiZ lights
 */

class WizSightApp {
    constructor() {
        this.baseURL = window.location.origin;
        this.discoveredLights = [];
        this.selectedLight = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateSliderDisplays();
        this.log('Ready', 'Enter a light IP address or scan for lights to get started.', 'info');
    }

    bindEvents() {
        // Discovery controls
        document.getElementById('scan-btn').addEventListener('click', () => this.scanForLights());

        // Manual control inputs  
        document.getElementById('light-ip').addEventListener('input', (e) => {
            this.selectedLight = null; // Clear selection when manually typing
            this.updateSelectedLight();
        });

        // Control buttons
        document.getElementById('toggle-btn').addEventListener('click', () => this.toggleLight());
        document.getElementById('state-btn').addEventListener('click', () => this.getLightState());
        document.getElementById('brightness-btn').addEventListener('click', () => this.setBrightness());
        document.getElementById('colortemp-btn').addEventListener('click', () => this.setColorTemp());

        // Slider and number input synchronization
        document.getElementById('brightness-slider').addEventListener('input', () => this.updateSliderDisplays());
        document.getElementById('colortemp-slider').addEventListener('input', () => this.updateSliderDisplays());
        document.getElementById('brightness-value').addEventListener('input', () => this.updateNumberInputs());
        document.getElementById('colortemp-value').addEventListener('input', () => this.updateNumberInputs());

        // Color temperature presets
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const temp = parseInt(e.target.dataset.temp);
                const presetName = e.target.textContent;
                
                // Update UI first
                document.getElementById('colortemp-slider').value = temp;
                document.getElementById('colortemp-value').value = temp;
                
                // Apply immediately if we have a light IP
                const ip = this.getCurrentLightIP();
                if (ip) {
                    await this.applyColorTempPreset(presetName, temp, ip);
                }
            });
        });

        // Scenario buttons
        document.querySelectorAll('.scenario-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const brightness = parseInt(e.currentTarget.dataset.brightness);
                const colortemp = parseInt(e.currentTarget.dataset.colortemp);
                const scenarioName = e.currentTarget.querySelector('.scenario-name').textContent;
                
                this.applyScenario(scenarioName, brightness, colortemp);
            });
        });
    }

    updateSliderDisplays() {
        const brightnessSlider = document.getElementById('brightness-slider');
        const colortempSlider = document.getElementById('colortemp-slider');
        const brightnessValue = document.getElementById('brightness-value');
        const colortempValue = document.getElementById('colortemp-value');
        
        brightnessValue.value = brightnessSlider.value;
        colortempValue.value = colortempSlider.value;
    }

    updateNumberInputs() {
        const brightnessSlider = document.getElementById('brightness-slider');
        const colortempSlider = document.getElementById('colortemp-slider');
        const brightnessValue = document.getElementById('brightness-value');
        const colortempValue = document.getElementById('colortemp-value');
        
        // Validate and sync number inputs back to sliders
        const brightness = parseInt(brightnessValue.value);
        const colortemp = parseInt(colortempValue.value);
        
        if (!isNaN(brightness) && brightness >= 0 && brightness <= 255) {
            brightnessSlider.value = brightness;
        }
        
        if (!isNaN(colortemp) && colortemp >= 1000 && colortemp <= 10000) {
            colortempSlider.value = colortemp;
        }
    }

    async applyColorTempPreset(presetName, colortemp, ip) {
        this.log('Preset', `Applying "${presetName}" (${colortemp}K)...`, 'info');

        try {
            const forceOn = document.getElementById('colortemp-force-on').checked;
            const response = await fetch(`${this.baseURL}/lights/${ip}/colortemp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ colortemp, force_on: forceOn })
            });

            if (!response.ok) {
                throw new Error('Color temperature preset failed');
            }

            const data = await response.json();
            const responseTime = Math.round(data.response_time_ms);

            this.log('Preset', `"${presetName}" applied successfully (${colortemp}K, ${responseTime}ms)`, 'success');

            // Update selected light state if available
            if (this.selectedLight && this.selectedLight.ip === ip) {
                this.selectedLight.colortemp = colortemp;
                if (data.new_state !== undefined) {
                    this.selectedLight.state = data.new_state;
                }
                this.updateLightDisplay(this.selectedLight);
            }

        } catch (error) {
            this.log('Preset Error', `Failed to apply "${presetName}": ${error.message}`, 'error');
        }
    }

    async applyScenario(scenarioName, brightness, colortemp) {
        const ip = this.getCurrentLightIP();
        if (!ip) {
            this.log('Scenario Error', 'Please enter a light IP address first', 'error');
            return;
        }

        this.log('Scenario', `Applying "${scenarioName}" scenario (${brightness} brightness, ${colortemp}K)`, 'info');

        // Update UI sliders first
        document.getElementById('brightness-slider').value = brightness;
        document.getElementById('colortemp-slider').value = colortemp;
        document.getElementById('brightness-value').value = brightness;
        document.getElementById('colortemp-value').value = colortemp;

        try {
            // Apply brightness first
            const brightnessResponse = await fetch(`${this.baseURL}/lights/${ip}/brightness`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ brightness, force_on: true })
            });

            if (!brightnessResponse.ok) {
                throw new Error('Brightness control failed');
            }

            // Then apply color temperature
            const colortempResponse = await fetch(`${this.baseURL}/lights/${ip}/colortemp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ colortemp, force_on: false }) // Don't force on again
            });

            if (!colortempResponse.ok) {
                throw new Error('Color temperature control failed');
            }

            const colortempData = await colortempResponse.json();
            const responseTime = Math.round(colortempData.response_time_ms);

            this.log('Scenario', `"${scenarioName}" applied successfully (${responseTime}ms)`, 'success');

            // Update selected light state if available
            if (this.selectedLight && this.selectedLight.ip === ip) {
                this.selectedLight.brightness = brightness;
                this.selectedLight.colortemp = colortemp;
                this.selectedLight.state = true; // Scenarios turn the light on
                this.updateLightDisplay(this.selectedLight);
            }

        } catch (error) {
            this.log('Scenario Error', `Failed to apply "${scenarioName}": ${error.message}`, 'error');
        }
    }

    async scanForLights() {
        const scanBtn = document.getElementById('scan-btn');
        const broadcastAddress = document.getElementById('broadcast-address').value.trim();
        const timeout = parseFloat(document.getElementById('timeout').value);

        this.setButtonLoading(scanBtn, true);
        this.log('Discovery', `Scanning network ${broadcastAddress} with ${timeout}s timeout...`, 'info');

        try {
            const params = new URLSearchParams();
            if (broadcastAddress) {
                params.append('broadcast_address', broadcastAddress);
            }
            if (timeout !== 5.0) {
                params.append('timeout', timeout.toString());
            }

            const response = await fetch(`${this.baseURL}/scan?${params}`);
            const data = await response.json();

            if (response.ok) {
                this.discoveredLights = data.devices || [];
                this.displayScanResults(data);
                this.log('Discovery', `Scan completed: found ${data.discovered_count} lights in ${data.started_at ? this.calculateDuration(data.started_at, data.completed_at) : 'N/A'}`, 'success');
            } else {
                this.log('Discovery Error', `Scan failed: ${data.message || data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.log('Discovery Error', `Network error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(scanBtn, false);
        }
    }

    displayScanResults(scanData) {
        const resultsContainer = document.getElementById('scan-results');
        
        if (scanData.discovered_count === 0) {
            resultsContainer.innerHTML = `
                <div class="status-item warning">
                    <svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
                    </svg>
                    <div class="status-content">
                        <strong>No lights found</strong><br>
                        Make sure your WiZ lights are powered on and connected to the same network.
                    </div>
                </div>
            `;
            return;
        }

        const devicesHTML = scanData.devices.map(device => `
            <div class="light-device" data-ip="${device.ip}" onclick="app.selectLight('${device.ip}')">
                <div class="device-header">
                    <span class="device-ip">${device.ip}</span>
                    <div class="device-status">
                        <span class="status-indicator ${device.available ? 'online' : 'offline'}"></span>
                        <span>${device.available ? 'Online' : 'Offline'}</span>
                        <span>${device.state ? 'On' : 'Off'}</span>
                    </div>
                </div>
                <div class="device-details">
                    <div><strong>State:</strong> ${device.state ? 'On' : 'Off'}</div>
                    <div><strong>Available:</strong> ${device.available ? 'Yes' : 'No'}</div>
                    ${device.brightness !== undefined ? `<div><strong>Brightness:</strong> ${device.brightness}</div>` : ''}
                    ${device.colortemp !== undefined ? `<div><strong>Color Temp:</strong> ${device.colortemp}K</div>` : ''}
                    ${device.name ? `<div><strong>Name:</strong> ${device.name}</div>` : ''}
                    ${device.mac ? `<div><strong>MAC:</strong> ${device.mac}</div>` : ''}
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = devicesHTML;
    }

    selectLight(ip) {
        // Update UI selection
        document.querySelectorAll('.light-device').forEach(el => el.classList.remove('selected'));
        document.querySelector(`[data-ip="${ip}"]`)?.classList.add('selected');
        
        // Update form
        document.getElementById('light-ip').value = ip;
        this.selectedLight = this.discoveredLights.find(light => light.ip === ip);
        
        this.log('Selection', `Selected light: ${ip}`, 'info');
        this.updateSelectedLight();
    }

    updateSelectedLight() {
        // Could add more UI updates here based on selected light state
    }

    async toggleLight() {
        const ip = this.getCurrentLightIP();
        if (!ip) return;

        const toggleBtn = document.getElementById('toggle-btn');
        this.setButtonLoading(toggleBtn, true);
        this.log('Control', `Toggling light ${ip}...`, 'info');

        try {
            const response = await fetch(`${this.baseURL}/lights/${ip}/toggle`, {
                method: 'POST'
            });
            const data = await response.json();

            if (response.ok) {
                const stateText = data.new_state ? 'ON' : 'OFF';
                const responseTime = Math.round(data.response_time_ms);
                this.log('Control', `Toggle successful: Light is now ${stateText} (${responseTime}ms)`, 'success');
                
                // Update selected light state if available
                if (this.selectedLight && this.selectedLight.ip === ip) {
                    this.selectedLight.state = data.new_state;
                    this.updateLightDisplay(this.selectedLight);
                }
            } else {
                this.log('Control Error', `Toggle failed: ${data.error_message || data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.log('Control Error', `Network error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(toggleBtn, false);
        }
    }

    async setBrightness() {
        const ip = this.getCurrentLightIP();
        if (!ip) return;

        const brightness = parseInt(document.getElementById('brightness-value').value);
        const forceOn = document.getElementById('force-on').checked;
        const brightnessBtn = document.getElementById('brightness-btn');

        this.setButtonLoading(brightnessBtn, true);
        this.log('Control', `Setting brightness to ${brightness} for light ${ip}...`, 'info');

        try {
            const response = await fetch(`${this.baseURL}/lights/${ip}/brightness`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ brightness, force_on: forceOn })
            });
            const data = await response.json();

            if (response.ok) {
                const responseTime = Math.round(data.response_time_ms);
                this.log('Control', `Brightness set to ${brightness} (${responseTime}ms)`, 'success');
                
                // Update selected light state if available
                if (this.selectedLight && this.selectedLight.ip === ip) {
                    this.selectedLight.brightness = brightness;
                    if (data.new_state !== undefined) {
                        this.selectedLight.state = data.new_state;
                    }
                    this.updateLightDisplay(this.selectedLight);
                }
            } else {
                this.log('Control Error', `Brightness control failed: ${data.error_message || data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.log('Control Error', `Network error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(brightnessBtn, false);
        }
    }

    async setColorTemp() {
        const ip = this.getCurrentLightIP();
        if (!ip) return;

        const colortemp = parseInt(document.getElementById('colortemp-value').value);
        const forceOn = document.getElementById('colortemp-force-on').checked;
        const colortempBtn = document.getElementById('colortemp-btn');

        this.setButtonLoading(colortempBtn, true);
        this.log('Control', `Setting color temperature to ${colortemp}K for light ${ip}...`, 'info');

        try {
            const response = await fetch(`${this.baseURL}/lights/${ip}/colortemp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ colortemp, force_on: forceOn })
            });
            const data = await response.json();

            if (response.ok) {
                const responseTime = Math.round(data.response_time_ms);
                this.log('Control', `Color temperature set to ${colortemp}K (${responseTime}ms)`, 'success');
                
                // Update selected light state if available
                if (this.selectedLight && this.selectedLight.ip === ip) {
                    this.selectedLight.colortemp = colortemp;
                    if (data.new_state !== undefined) {
                        this.selectedLight.state = data.new_state;
                    }
                    this.updateLightDisplay(this.selectedLight);
                }
            } else {
                this.log('Control Error', `Color temperature control failed: ${data.error_message || data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.log('Control Error', `Network error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(colortempBtn, false);
        }
    }

    async getLightState() {
        const ip = this.getCurrentLightIP();
        if (!ip) return;

        const stateBtn = document.getElementById('state-btn');
        this.setButtonLoading(stateBtn, true);
        this.log('Query', `Getting state for light ${ip}...`, 'info');

        try {
            const response = await fetch(`${this.baseURL}/lights/${ip}/state`);
            const data = await response.json();

            if (response.ok) {
                this.log('Query', `State retrieved for ${ip}:`, 'success');
                this.logLightState(data);
                
                // Update selected light if this is the same IP
                if (this.selectedLight && this.selectedLight.ip === ip) {
                    Object.assign(this.selectedLight, data);
                    this.updateLightDisplay(this.selectedLight);
                }
            } else {
                this.log('Query Error', `State query failed: ${data.error || data.message || data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.log('Query Error', `Network error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(stateBtn, false);
        }
    }

    updateLightDisplay(light) {
        const lightElement = document.querySelector(`[data-ip="${light.ip}"]`);
        if (lightElement) {
            // Update the display to reflect new state
            const statusIndicator = lightElement.querySelector('.status-indicator');
            const deviceStatus = lightElement.querySelector('.device-status span:nth-child(2)');
            const stateText = lightElement.querySelector('.device-status span:nth-child(3)');
            
            if (statusIndicator) {
                statusIndicator.className = `status-indicator ${light.available ? 'online' : 'offline'}`;
            }
            if (deviceStatus) {
                deviceStatus.textContent = light.available ? 'Online' : 'Offline';
            }
            if (stateText) {
                stateText.textContent = light.state ? 'On' : 'Off';
            }

            // Update details
            const details = lightElement.querySelector('.device-details');
            if (details) {
                details.innerHTML = `
                    <div><strong>State:</strong> ${light.state ? 'On' : 'Off'}</div>
                    <div><strong>Available:</strong> ${light.available ? 'Yes' : 'No'}</div>
                    ${light.brightness !== undefined ? `<div><strong>Brightness:</strong> ${light.brightness}</div>` : ''}
                    ${light.colortemp !== undefined ? `<div><strong>Color Temp:</strong> ${light.colortemp}K</div>` : ''}
                    ${light.name ? `<div><strong>Name:</strong> ${light.name}</div>` : ''}
                    ${light.mac ? `<div><strong>MAC:</strong> ${light.mac}</div>` : ''}
                `;
            }
        }
    }

    getCurrentLightIP() {
        const ip = document.getElementById('light-ip').value.trim();
        if (!ip) {
            this.log('Input Error', 'Please enter a light IP address', 'error');
            return null;
        }
        
        // Basic IP validation
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipPattern.test(ip)) {
            this.log('Input Error', 'Please enter a valid IP address', 'error');
            return null;
        }
        
        return ip;
    }

    setButtonLoading(button, loading) {
        const textSpan = button.querySelector('.btn-text');
        const spinner = button.querySelector('.loading-spinner');
        
        if (loading) {
            button.disabled = true;
            if (textSpan) textSpan.style.display = 'none';
            if (spinner) {
                spinner.style.display = 'inline-block';
            }
        } else {
            button.disabled = false;
            if (textSpan) textSpan.style.display = 'inline';
            if (spinner) {
                spinner.style.display = 'none';
            }
        }
    }

    log(category, message, type = 'info') {
        const statusDisplay = document.getElementById('status-display');
        const timestamp = new Date().toLocaleTimeString();
        
        // Choose appropriate icon based on type
        let iconSVG = '';
        switch (type) {
            case 'success':
                iconSVG = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="m9 12 2 2 4-4"/>
                    <circle cx="12" cy="12" r="10"/>
                </svg>`;
                break;
            case 'error':
                iconSVG = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="m15 9-6 6"/>
                    <path d="m9 9 6 6"/>
                </svg>`;
                break;
            case 'warning':
                iconSVG = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
                </svg>`;
                break;
            default:
                iconSVG = `<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 16v-4"/>
                    <path d="M12 8h.01"/>
                </svg>`;
        }
        
        const statusItem = document.createElement('div');
        statusItem.className = `status-item ${type}`;
        statusItem.innerHTML = `
            ${iconSVG}
            <div class="status-content">
                <strong>[${timestamp}] ${category}:</strong> ${message}
            </div>
        `;
        
        // Add to top of status display
        statusDisplay.insertBefore(statusItem, statusDisplay.firstChild);
        
        // Limit to last 20 messages
        const items = statusDisplay.querySelectorAll('.status-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
        
        console.log(`[WizSight] [${category}] ${message}`);
    }

    logLightState(state) {
        const details = [
            `Power: ${state.state ? 'ON' : 'OFF'}`,
            `Available: ${state.available ? 'Yes' : 'No'}`,
            state.brightness !== undefined ? `Brightness: ${state.brightness}/255` : null,
            state.colortemp !== undefined ? `Color Temp: ${state.colortemp}K` : null,
            state.rgb ? `RGB: [${state.rgb.join(', ')}]` : null,
            state.scene ? `Scene: ${state.scene}` : null,
            state.name ? `Name: ${state.name}` : null,
            state.mac ? `MAC: ${state.mac}` : null
        ].filter(Boolean);

        this.log('State Details', details.join(', '), 'success');
    }

    calculateDuration(startTime, endTime) {
        try {
            const start = new Date(startTime);
            const end = new Date(endTime);
            const durationMs = end - start;
            return `${(durationMs / 1000).toFixed(2)}s`;
        } catch (e) {
            return 'N/A';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WizSightApp();
});

// Global error handler
window.addEventListener('error', (event) => {
    if (window.app) {
        window.app.log('JavaScript Error', event.message, 'error');
    }
});

window.addEventListener('unhandledrejection', (event) => {
    if (window.app) {
        window.app.log('Promise Rejection', event.reason, 'error');
    }
});