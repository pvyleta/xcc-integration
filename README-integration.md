# XCC Heat Pump Controller Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

![Project Maintenance][maintenance-shield]

**This integration allows you to monitor and control XCC heat pump controllers through Home Assistant.**

## Features

- 🔍 **Automatic Discovery**: Automatically discovers all available parameters from your XCC controller
- 🌍 **Multi-language Support**: Supports English and Czech languages with automatic language detection
- 📡 **MQTT Integration**: Automatically creates MQTT devices and entities for external access
- 📊 **Real-time Monitoring**: Monitors temperatures, pressures, power consumption, and system status
- 🎛️ **Control Capabilities**: Allows setting of configurable parameters like setpoints and operation modes
- 🏷️ **Device Classes**: Proper device classes for sensors (temperature, power, energy, etc.)

## Supported Entity Types

- **Sensors**: Read-only values like temperatures, pressures, power consumption
- **Binary Sensors**: Status indicators like running, alarms, heating/cooling states  
- **Switches**: Boolean controls like enable/disable functions, modes
- **Numbers**: Numeric controls like temperature setpoints, power limits
- **Selects**: Enumerated controls like operation modes, schedules

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/pvyleta/xcc-integration`
6. Select "Integration" as the category
7. Click "Add"
8. Find "XCC Heat Pump Controller" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the ZIP file
3. Copy the `xcc` folder to your `custom_components` directory
4. Restart Home Assistant

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "XCC Heat Pump Controller"
4. Enter your XCC controller details:
   - IP address (e.g., `192.168.1.100`)
   - Username (usually `xcc`)
   - Password (usually `xcc`)
   - Scan interval in seconds (default: 30)
5. Click **Submit**

The integration will automatically discover all available parameters and create entities.

## Testing the Integration

The XCC integration includes comprehensive testing options for both developers and users who want to verify functionality before deployment.

### 🧪 Option 1: Quick Unit Testing (Recommended)

Use the official Home Assistant testing framework for fast, comprehensive testing:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all integration tests
python run_ha_tests.py
```

**What this tests:**
- ✅ Configuration flow (setup UI)
- ✅ Integration loading and unloading
- ✅ Entity discovery and creation
- ✅ MQTT discovery functionality
- ✅ Error handling and edge cases

**Benefits:**
- 🚀 **Fast** - tests run in seconds
- 🧪 **Comprehensive** - tests all integration aspects
- 💻 **No setup required** - pure Python testing
- ✅ **Professional** - same framework Home Assistant core uses

### 🎯 Option 2: VS Code Development Container

For full development experience with real Home Assistant:

1. **Install VS Code** + **Dev Containers extension**
2. **Open project** in VS Code
3. **Command Palette** → "Dev Containers: Reopen in Container"
4. **Wait for automatic setup**
5. **Start Home Assistant**: `hass --config /config --debug`
6. **Open**: http://localhost:8123

**What you get:**
- 🏠 **Real Home Assistant** with full UI
- 📡 **MQTT broker** pre-configured
- 🎭 **Mock XCC controller** for testing
- 🔧 **All dependencies** pre-installed
- 🐛 **Debugging support** built-in

### 🎭 Option 3: Mock Controller Testing

Test with a simulated XCC controller (no real hardware needed):

```bash
# Start mock XCC controller
python xcc_mock_server.py

# In another terminal, start Home Assistant
hass --config config --debug

# Configure integration with:
# - IP: localhost:8080
# - Username: xcc
# - Password: xcc
```

### 🏠 Option 4: Docker Development Environment

Complete isolated environment with all services:

```bash
# Start everything (HA + MQTT + Mock XCC)
./start_dev_environment.sh

# Access services:
# - Home Assistant: http://localhost:8123
# - Mock XCC: http://localhost:8080
# - MQTT: localhost:1883
```

### 📋 Testing Checklist

Before deploying to your real Home Assistant:

- [ ] **Unit tests pass**: `python run_ha_tests.py`
- [ ] **Integration loads**: No errors in HA logs
- [ ] **Entities created**: Sensors, switches, etc. appear
- [ ] **Configuration works**: Setup UI accepts your XCC details
- [ ] **MQTT discovery**: MQTT entities appear (if MQTT configured)
- [ ] **Multi-language**: Entity names in correct language
- [ ] **Error handling**: Graceful handling of connection issues

### 🔧 Troubleshooting Tests

**Tests fail with import errors:**
```bash
# Ensure you're in the project root directory
cd /path/to/xcc-integration

# Install test dependencies
pip install -r requirements-test.txt
```

**VS Code container won't start:**
- Ensure Docker is running
- Install "Dev Containers" extension
- Try "Dev Containers: Rebuild Container"

**Mock controller connection fails:**
- Check if port 8080 is available
- Try different port in `xcc_mock_server.py`
- Verify firewall settings

### 🚀 Recommended Testing Workflow

1. **Quick validation**: `python run_ha_tests.py`
2. **Integration testing**: Use VS Code Dev Container
3. **Real hardware**: Deploy to your Home Assistant
4. **Production**: Install via HACS

This ensures your integration works correctly at every level!

## MQTT Integration

If MQTT is configured in your Home Assistant, the integration will automatically:

- Create MQTT device discovery messages
- Publish entity states to MQTT topics
- Enable external access to XCC data via MQTT

### MQTT Topics

- Device availability: `xcc/{ip_address}/availability`
- Entity states: `xcc/{ip_address}/{entity_id}/state`
- Entity commands: `xcc/{ip_address}/{entity_id}/set`

## Language Support

The integration automatically detects your Home Assistant language setting:

- **English**: Uses English entity names and descriptions
- **Czech**: Uses Czech entity names and descriptions
- **Other languages**: Defaults to English

## Troubleshooting

### Connection Issues

1. **Cannot connect to XCC controller**:
   - Verify the IP address is correct
   - Ensure the XCC controller is on the same network
   - Check that the XCC web interface is accessible

2. **Authentication failed**:
   - Verify username and password
   - Default credentials are usually `xcc`/`xcc`
   - Check if credentials were changed in XCC settings

3. **Timeout errors**:
   - The controller may be overloaded
   - Try increasing the scan interval
   - Check network connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

- 🐛 [Report bugs][issues]
- 💡 [Request features][issues]

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/pvyleta/xcc-integration.svg?style=for-the-badge
[commits]: https://github.com/pvyleta/xcc-integration/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[issues]: https://github.com/pvyleta/xcc-integration/issues
[license-shield]: https://img.shields.io/github/license/pvyleta/xcc-integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Petr%20Vyleta%20%40pvyleta-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pvyleta/xcc-integration.svg?style=for-the-badge
[releases]: https://github.com/pvyleta/xcc-integration/releases
