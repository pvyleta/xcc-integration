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

## Development and Testing

### Local Development Environment

This repository includes a complete Docker-based development environment:

```bash
# Start the development environment
./start_dev_environment.sh

# Access services
# - Home Assistant: http://localhost:8123
# - XCC Mock Controller: http://localhost:8080
# - MQTT Broker: localhost:1883
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests
python -m pytest tests/ -v

# Validate integration structure
python validate_integration.py
```

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
