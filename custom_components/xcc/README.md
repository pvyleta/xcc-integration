# XCC Heat Pump Controller Integration for Home Assistant

This integration allows you to monitor and control XCC heat pump controllers through Home Assistant. It automatically discovers all available parameters from your XCC controller and creates appropriate entities for monitoring and control.

## Features

- **Automatic Discovery**: Automatically discovers all available parameters from your XCC controller
- **Multi-language Support**: Supports English and Czech languages with automatic language detection
- **MQTT Integration**: Automatically creates MQTT devices and entities for external access
- **Real-time Monitoring**: Monitors temperatures, pressures, power consumption, and system status
- **Control Capabilities**: Allows setting of configurable parameters like setpoints and operation modes
- **Device Classes**: Proper device classes for sensors (temperature, power, energy, etc.)

## Supported Entity Types

- **Sensors**: Read-only values like temperatures, pressures, power consumption
- **Binary Sensors**: Status indicators like running, alarms, heating/cooling states
- **Switches**: Boolean controls like enable/disable functions, modes
- **Numbers**: Numeric controls like temperature setpoints, power limits
- **Selects**: Enumerated controls like operation modes, schedules

## Installation

### Method 1: Manual Installation

1. Copy the `xcc` folder to your Home Assistant `custom_components` directory:
   ```
   custom_components/
   └── xcc/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       ├── coordinator.py
       ├── entity.py
       ├── sensor.py
       ├── binary_sensor.py
       ├── switch.py
       ├── number.py
       ├── select.py
       ├── mqtt_discovery.py
       ├── xcc_client.py
       ├── const.py
       ├── strings.json
       └── translations/
           └── cs.json
   ```

2. Restart Home Assistant

3. Go to **Settings** > **Devices & Services** > **Add Integration**

4. Search for "XCC Heat Pump Controller"

5. Follow the configuration steps

### Method 2: HACS (Future)

This integration will be available through HACS in the future.

## Configuration

### Required Information

- **IP Address**: The IP address of your XCC controller
- **Username**: Username for XCC controller (default: `xcc`)
- **Password**: Password for XCC controller (default: `xcc`)
- **Scan Interval**: How often to update data (10-3600 seconds, default: 30)

### Configuration Steps

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

### Entity Issues

1. **No entities created**:
   - Check the logs for errors
   - Verify the XCC controller is responding
   - Ensure the controller has discoverable parameters

2. **Entities not updating**:
   - Check the coordinator update interval
   - Verify network connectivity
   - Look for authentication errors in logs

### MQTT Issues

1. **MQTT entities not appearing**:
   - Ensure MQTT is configured in Home Assistant
   - Check MQTT broker connectivity
   - Verify MQTT discovery is enabled

## Development

### File Structure

- `__init__.py`: Main integration setup and platform loading
- `config_flow.py`: Configuration flow for setup UI
- `coordinator.py`: Data update coordinator for XCC communication
- `entity.py`: Base entity class with common functionality
- `sensor.py`: Sensor entities for read-only values
- `binary_sensor.py`: Binary sensor entities for status indicators
- `switch.py`: Switch entities for boolean controls
- `number.py`: Number entities for numeric controls
- `select.py`: Select entities for enumerated controls
- `mqtt_discovery.py`: MQTT device discovery functionality
- `xcc_client.py`: XCC controller communication client
- `const.py`: Constants and configuration
- `strings.json`: English translations
- `translations/cs.json`: Czech translations

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This integration is released under the MIT License.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Acknowledgments

- XCC controller manufacturers for the device
- Home Assistant community for the platform
- Contributors to this integration
