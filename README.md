# XCC Heat Pump Controller Integration

Home Assistant integration for XCC heat pump controllers with photovoltaic integration. Monitor and control your heat pump system directly from Home Assistant with automatic entity discovery and bilingual support.

## 🏠 Home Assistant Integration Features

- 🔧 **470+ settable fields** automatically discovered across 6 configuration pages
- 📊 **Live data monitoring** with real-time sensor values
- 🌐 **Bilingual support** (English/Czech with auto-detection)
- 🎛️ **Native HA entities**: Sensors, switches, numbers, selects, binary sensors
- 📋 **Organized by device** (heating, PV, hot water, auxiliary source, etc.)
- 🔄 **Automatic updates** with configurable scan intervals
- 📈 **Professional UI** with native Home Assistant configuration flow
- 🏷️ **Consistent naming** with `xcc_` prefix for easy identification

## 📦 Installation

### 🚀 HACS Installation (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Click the 3 dots (⋮) → "Custom repositories"
   - Add repository: `https://github.com/pvyleta/xcc-integration`
   - Category: `Integration`

2. **Install Integration**:
   - Go to HACS > Integrations
   - Search for "XCC Heat Pump Controller"
   - Click "Download" and restart Home Assistant

3. **Configure Integration**:
   - Settings > Devices & Services > "Add Integration"
   - Search for "XCC Heat Pump Controller"
   - Enter your XCC controller details:
     - IP Address: Your XCC controller IP
     - Username: Your XCC username
     - Password: Your XCC password
     - Scan Interval: 30 seconds (recommended)

### 📁 Manual Installation

1. Download the latest release
2. Copy `custom_components/xcc/` to your Home Assistant `custom_components/` directory
3. Restart Home Assistant
4. Follow configuration steps above

## ✅ What You'll Get

- 🌡️ **Temperature sensors**: Outdoor, indoor, water temperatures
- 🔄 **Status sensors**: Compressor, pump, operation modes
- 🎛️ **Controls**: Switches, temperature setpoints, operation modes
- 📊 **Performance metrics**: Power consumption, efficiency data
- 🌐 **Multi-language**: English/Czech with automatic detection
- 🏷️ **Organized entities**: All entities prefixed with `xcc_` for easy identification

## 🔧 Development & Testing

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pvyleta/xcc-integration
   cd xcc-integration
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

The integration includes comprehensive tests to ensure reliability:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_basic_validation.py -v
python -m pytest tests/test_xcc_client.py -v
```

**Test Coverage:**
- ✅ Python syntax validation
- ✅ Manifest.json validation
- ✅ Sample data parsing
- ✅ XML structure validation
- ✅ Integration constants verification

## 🔧 Troubleshooting

### Integration Not Appearing in HACS
- Ensure you added the repository correctly to HACS custom repositories
- Refresh HACS and search again
- Check HACS logs for any errors

### Connection Issues
- Verify XCC controller IP is reachable from Home Assistant
- Check username/password are correct
- Ensure XCC controller web interface is accessible
- Test connection from Home Assistant host: `ping <XCC_IP>`

### Entity Issues
- All XCC entities are prefixed with `xcc_` for easy identification
- If entities don't appear, check Home Assistant logs for errors
- Restart Home Assistant after configuration changes
- Check entity registry in Developer Tools

### Performance Issues
- Default scan interval is 30 seconds (recommended)
- Reduce scan interval if you need faster updates
- Increase scan interval if experiencing performance issues

## 📚 Configuration Pages

The integration automatically discovers entities from these XCC pages:

| Page | Description | Typical Entities |
|------|-------------|------------------|
| **Heating Circuits** | Temperature control, schedules | Temperature sensors, setpoint controls |
| **Photovoltaics** | Battery management, export limits | Power sensors, battery controls |
| **Hot Water** | Sanitization, circulation | Water temperature, heating controls |
| **Auxiliary Source** | Backup heating system | Status sensors, operation controls |
| **Spot Pricing** | Dynamic pricing optimization | Price sensors, optimization switches |
| **System Status** | Overall system information | Status sensors, diagnostic data |

## 🆘 Support

### Getting Help
If you encounter issues:

1. **Check Home Assistant logs**: Settings > System > Logs
2. **Look for XCC errors**: Search for "xcc" or "custom_components" in logs
3. **Verify connectivity**: Ensure XCC controller is reachable from HA
4. **Check entity registry**: Developer Tools > States (search for `xcc_`)

### Common Issues

**Entities not updating:**
- Check scan interval configuration
- Verify XCC controller is responding
- Look for timeout errors in logs

**Authentication errors:**
- Verify username/password are correct
- Check if XCC web interface is accessible
- Ensure no special characters in credentials

**Missing entities:**
- Some entities may be hidden if they have no current value
- Check if XCC controller has all expected modules/features
- Restart Home Assistant after configuration changes

### Reporting Issues

When reporting issues, please include:
- Home Assistant version
- XCC integration version
- XCC controller model/firmware
- Relevant log entries
- Steps to reproduce the issue

[Open an issue on GitHub](https://github.com/pvyleta/xcc-integration/issues)

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and changes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ for the Home Assistant community**
