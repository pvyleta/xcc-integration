# XCC Integration Testing Guide

This guide covers all testing approaches for the XCC Heat Pump Controller integration.

## 🚀 Quick Start

**Want to test immediately?** Run this:

```bash
# Install test framework and run all tests
pip install -r requirements-test.txt
python run_ha_tests.py
```

This tests your integration in **seconds** without any setup!

## 🧪 Testing Options

### Option 1: Unit Testing (Fastest)

**Best for:** Quick validation, development, CI/CD

```bash
# Install official HA testing framework
pip install pytest-homeassistant-custom-component

# Run comprehensive integration tests
python run_ha_tests.py
```

**What it tests:**
- ✅ Configuration flow (setup UI)
- ✅ Integration loading/unloading
- ✅ Entity discovery and creation
- ✅ MQTT discovery functionality
- ✅ Error handling and edge cases

**Benefits:**
- 🚀 **Fast** - tests run in seconds
- 🧪 **Comprehensive** - tests all aspects
- 💻 **No setup** - pure Python testing
- ✅ **Professional** - same tools HA uses

### Option 2: VS Code Dev Container (Best for Development)

**Best for:** Full development experience, debugging, UI testing

**Setup:**
1. Install VS Code + Dev Containers extension
2. Open project in VS Code
3. Command Palette → "Dev Containers: Reopen in Container"
4. Wait for automatic setup

**Usage:**
```bash
# Start Home Assistant
hass --config /config --debug

# Open in browser
open http://localhost:8123
```

**What you get:**
- 🏠 **Real Home Assistant** with full UI
- 📡 **MQTT broker** pre-configured
- 🎭 **Mock XCC controller** for testing
- 🔧 **All dependencies** pre-installed
- 🐛 **Debugging support** built-in

### Option 3: Mock Controller Testing

**Best for:** Testing without real hardware

```bash
# Start mock XCC controller
python xcc_mock_server.py

# In Home Assistant, configure integration with:
# - IP: localhost:8080
# - Username: xcc
# - Password: xcc
```

**Mock controller provides:**
- 🎭 **Realistic responses** based on real XCC data
- 🔄 **Settable parameters** for testing controls
- 📊 **Multiple entity types** (sensors, switches, etc.)
- 🌐 **Multi-language** support testing

### Option 4: Docker Environment

**Best for:** Isolated testing, team development

```bash
# Start complete environment
./start_dev_environment.sh

# Access services:
# - Home Assistant: http://localhost:8123
# - Mock XCC: http://localhost:8080
# - MQTT Broker: localhost:1883
```

## 📋 Testing Workflow

### For Developers

1. **Quick validation:**
   ```bash
   python run_ha_tests.py
   ```

2. **Integration testing:**
   ```bash
   # Use VS Code Dev Container or Docker
   hass --config /config --debug
   ```

3. **Real hardware testing:**
   ```bash
   # Deploy to your Home Assistant instance
   ```

### For Users

1. **Before installation:**
   ```bash
   # Test with mock controller
   python xcc_mock_server.py
   ```

2. **After installation:**
   - Add integration through HA UI
   - Verify entities are created
   - Test controls work correctly

## 🔧 Troubleshooting

### Tests Fail

```bash
# Ensure correct directory
cd /path/to/xcc-integration

# Reinstall dependencies
pip install -r requirements-test.txt

# Run with verbose output
python run_ha_tests.py -v
```

### VS Code Container Issues

- Ensure Docker is running
- Install "Dev Containers" extension
- Try "Dev Containers: Rebuild Container"

### Mock Controller Connection Fails

```bash
# Check if port is available
netstat -an | grep 8080

# Try different port
python xcc_mock_server.py --port 8081
```

### Integration Not Loading

1. Check Home Assistant logs
2. Verify `custom_components/xcc/` exists
3. Restart Home Assistant
4. Check for dependency issues

## 📊 Test Coverage

The test suite covers:

- **Configuration Flow**: Setup UI, validation, error handling
- **Integration Lifecycle**: Loading, unloading, cleanup
- **Entity Discovery**: Automatic parameter detection
- **Entity Creation**: Sensors, switches, numbers, selects
- **MQTT Discovery**: Automatic MQTT device creation
- **Multi-language**: English/Czech language support
- **Error Handling**: Network issues, authentication, timeouts

## 🎯 Testing Checklist

Before deploying to production:

- [ ] **Unit tests pass**: `python run_ha_tests.py`
- [ ] **Integration loads**: No errors in HA logs
- [ ] **Entities created**: All expected sensors/controls appear
- [ ] **Configuration works**: Setup UI accepts your credentials
- [ ] **MQTT discovery**: MQTT entities appear (if MQTT enabled)
- [ ] **Controls work**: Switches, numbers, selects function correctly
- [ ] **Language correct**: Entity names in expected language
- [ ] **Error handling**: Graceful handling of connection issues

## 🚀 Next Steps

After testing:

1. **Deploy to Home Assistant**: Copy to `custom_components/`
2. **Configure integration**: Use HA UI to add XCC integration
3. **Monitor logs**: Check for any issues during operation
4. **Create automations**: Use XCC entities in your automations
5. **Share feedback**: Report issues or improvements

## 📚 Additional Resources

- [Integration README](README-integration.md) - Full integration documentation
- [CLI README](README.md) - Command-line tool documentation
- [Home Assistant Developer Docs](https://developers.home-assistant.io/) - HA development guide
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) - Testing framework docs

Happy testing! 🎉
