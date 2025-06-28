# XCC Heat Pump Controller CLI

Command-line tool for XCC heat pump controllers with photovoltaic integration. Read, monitor, and configure your heat pump system through a structured, page-based interface.

## Features

- 🔧 **470+ settable fields** across 6 configuration pages
- 📊 **Live data fetching** with real-time current values
- 🌐 **Bilingual support** (English/Czech descriptions)
- 📋 **Page-based organization** (heating, PV, hot water, etc.)
- 🔍 **Advanced search** across all fields and pages
- 🔄 **Database refresh** to sync with firmware updates
- 📈 **Rich display** with constraints, options, and current values
- 🖥️ **Click framework** for robust CLI interface

## Project Structure

```
xcc-integration/
├── xcc_cli.py                     # Main CLI application
├── xcc_client.py                  # Reusable XCC client library
├── custom_components/xcc/         # Home Assistant integration
├── homeassistant/components/xcc/  # HA core integration (dev)
├── tests/test_xcc/               # Integration test suite
├── scripts/                      # Development utilities
├── .devcontainer/               # VS Code dev container
├── mock_data/                   # Test data for mock controller
└── xcc_data/                    # Live XML data cache
```

## Home Assistant Integration

This project includes a **complete Home Assistant integration** that transforms the CLI tool into a full smart home integration:

### 🏠 **Integration Features**
- **Automatic Discovery**: Finds all XCC parameters automatically
- **Multi-language Support**: English/Czech with auto-detection
- **MQTT Integration**: Auto-discovery for external systems
- **Entity Types**: Sensors, switches, numbers, selects, binary sensors
- **Professional UI**: Native Home Assistant configuration flow

### 📦 **Installation Options**
- **HACS**: One-click installation (recommended)
- **Manual**: Download and copy to `custom_components/`
- **Development**: Full testing and development environment

See [Integration README](README-integration.md) for detailed installation and usage instructions.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
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

**Note:** The field database is automatically generated on first run if missing.

## Quick Start

### List Available Pages
```bash
python xcc_cli.py --ip 192.168.0.50 pages
```

### View Configuration Fields
```bash
# List all settable fields in spot pricing page
python xcc_cli.py --ip 192.168.0.50 spot --list

# List all fields (including read-only) in PV page
python xcc_cli.py --ip 192.168.0.50 fve --list-all

# Show detailed info about a specific field
python xcc_cli.py --ip 192.168.0.50 fve --show FVE-USEMODE

# Get current value of a field
python xcc_cli.py --ip 192.168.0.50 tuv1 --get TUVPOZADOVANA
```

### Search and Filter
```bash
# Search for battery-related fields in PV page
python xcc_cli.py --ip 192.168.0.50 fve --search battery

# Search across all pages
python xcc_cli.py --ip 192.168.0.50 search temperature
```

## Configuration Pages

| Command | Page | Description | Fields |
|---------|------|-------------|--------|
| `okruh` | Heating Circuits | Temperature control, schedules, weather influence | 114 |
| `fve` | Photovoltaics | Battery management, export limits, spot pricing | 220 |
| `tuv1` | Hot Water | Sanitization, circulation, external heating | 82 |
| `biv` | Bivalent Heating | Backup heating system configuration | 47 |
| `spot` | Spot Pricing | Dynamic pricing optimization | 7 |

## Command Line Interface

### Shell Script vs Python Script

```bash
python xcc_cli.py --ip 192.168.0.50 --lang cz spot --list
```

### Global Options

**Important**: Global options must come **before** the subcommand.

- `--ip IP` - Controller IP address (default: 192.168.0.50)
- `--username USER` - Username (default: xcc)
- `--password PASS` - Password (default: xcc)
- `--lang {en,cz}` - Language for descriptions (default: en)
- `-v, --verbose` - Enable verbose debugging output
- `--show-entities` - Show entity output during data fetching

### Page Commands
Each page supports these subcommands:
- `--list` - List all settable fields with current values
- `--list-all` - List all fields (settable + read-only)
- `--show FIELD` - Show detailed field information
- `--get FIELD` - Get current value of a field
- `--search QUERY` - Search fields in this page

### Special Commands
- `pages` - List all available configuration pages
- `search QUERY` - Search across all pages
- `refresh-db` - Update field database from controller
- `refresh-db --force` - Force refresh even if recent

## Examples

### Basic Usage
```bash
# View all spot pricing settings
python xcc_cli.py --ip 192.168.0.50 spot --list

# Check current battery mode
python xcc_cli.py --ip 192.168.0.50 fve --get FVE-USEMODE

# Search for temperature-related settings
python xcc_cli.py --ip 192.168.0.50 okruh --search temperature
```

### Advanced Usage
```bash
# Use Czech descriptions (global options come first)
python xcc_cli.py --ip 192.168.0.50 --lang cz spot --list

# Custom credentials with verbose output
python xcc_cli.py --ip 192.168.0.50 --username admin --password secret123 -v pages

# Show entity output during data fetching
python xcc_cli.py --ip 192.168.0.50 --show-entities fve --list
```

### Database Management
```bash
# Check if database needs refresh
python xcc_cli.py --ip 192.168.0.50 refresh-db

# Force database refresh after firmware update
python xcc_cli.py --ip 192.168.0.50 refresh-db --force
```



## Field Types and Display

### Table Columns
- **Field** - Field name/identifier
- **Type** - Data type (numeric, boolean, enum, time, action)
- **Current Value** - Live value from controller
- **Description** - Human-readable description
- **Constraints** - Min/max values, units, available options
- **Access** - 🔧 (settable) or 👁️ (read-only)

### Value Formatting
- **Boolean**: ✓ (enabled) / ✗ (disabled)
- **Enum**: Current value with description (e.g., "3 (Economic)")
- **Numeric**: Value with unit (e.g., "21.0 °C")
- **Time**: Formatted time values

## Database Management

The CLI uses a hybrid approach:
- **Static data** (field definitions, constraints) from JSON database
- **Dynamic data** (current values) fetched live from controller

### When to Refresh Database
- After controller firmware updates
- When new fields are added
- If field definitions change
- For troubleshooting sync issues

### Refresh Process
```bash
# The refresh command runs analyze_known_pages.py automatically
xcc refresh-db
```

## Troubleshooting

### Connection Issues
```bash
# Test with verbose output
python xcc_cli.py --ip 192.168.0.50 -v pages

# Check with custom IP
python xcc_cli.py --ip 192.168.1.100 pages
```

### Database Issues
```bash
# Force refresh database
python xcc_cli.py --ip 192.168.0.50 refresh-db --force

# Manual database generation
python scripts/analyze_known_pages.py 192.168.0.50
```

### Authentication Issues
```bash
# Use custom credentials
python xcc_cli.py --ip 192.168.0.50 --username myuser --password mypass pages
```



## Testing

This project includes comprehensive testing for both the CLI tool and Home Assistant integration.

### 🧪 **CLI Testing**

Test the command-line interface:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run CLI tests
python -m pytest test/ -v

# Test with mock data
python test_xcc_client.py
```

### 🏠 **Home Assistant Integration Testing**

Multiple testing approaches for the HA integration:

#### **Quick Unit Testing (Recommended)**
```bash
# Fast, comprehensive testing using official HA framework
python run_ha_tests.py
```
- ✅ Tests configuration flow, entity creation, MQTT discovery
- ✅ Runs in seconds, no setup required
- ✅ Same framework Home Assistant core uses

#### **VS Code Development Container**
```bash
# 1. Install VS Code + Dev Containers extension
# 2. Open project in VS Code
# 3. Command Palette → "Dev Containers: Reopen in Container"
# 4. Start HA: hass --config /config --debug
# 5. Open: http://localhost:8123
```
- 🏠 Real Home Assistant with full UI
- 📡 MQTT broker pre-configured
- 🎭 Mock XCC controller included

#### **Mock Controller Testing**
```bash
# Start mock XCC controller (no real hardware needed)
python xcc_mock_server.py

# Configure HA integration with:
# IP: localhost:8080, User: xcc, Pass: xcc
```

#### **Docker Development Environment**
```bash
# Complete isolated environment
./start_dev_environment.sh

# Access: HA (8123), Mock XCC (8080), MQTT (1883)
```

### 📋 **Testing Checklist**

Before deploying:
- [ ] CLI tests pass: `pytest test/ -v`
- [ ] Integration tests pass: `python run_ha_tests.py`
- [ ] Mock controller works: `python xcc_mock_server.py`
- [ ] Real hardware connection: `python xcc_cli.py --ip YOUR_IP pages`

See [Integration Testing Guide](README-integration.md#testing-the-integration) for detailed instructions.

## Architecture

### Data Flow
1. **Static Database**: Field definitions loaded from `field_database.json`
2. **Live Connection**: Current values fetched from controller XML endpoints
3. **Hybrid Display**: Combined static metadata with live values

### File Structure
- `xcc_cli.py` - Main CLI application
- `xcc` - Shell wrapper script
- `xcc_client.py` - Reusable XCC client library
- `scripts/analyze_known_pages.py` - Database generator
- `field_database.json` - Field database (auto-generated)
- `requirements.txt` - Python dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your controller
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Run with `-v` flag for detailed logs
3. Verify controller connectivity
4. Check database freshness with `refresh-db`
