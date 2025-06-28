# XCC Heat Pump Controller CLI

Professional command-line interface for XCC heat pump controllers with photovoltaic integration. Read, monitor, and configure your heat pump system through a structured, page-based interface.

## Features

- 🔧 **470+ settable fields** across 6 configuration pages
- 📊 **Live data fetching** with real-time current values
- 🌐 **Bilingual support** (English/Czech descriptions)
- 📋 **Page-based organization** (heating, PV, hot water, etc.)
- 🔍 **Advanced search** across all fields and pages
- 🔄 **Database refresh** to sync with firmware updates
- 📈 **Rich display** with constraints, options, and current values
- 🖥️ **Professional CLI** built with Click framework
- 🛠️ **Shell integration** with convenient wrapper script

## Project Structure

```
xcc-integration/
├── xcc_cli.py              # Main CLI application
├── xcc_client.py           # Reusable XCC client library
├── xcc                     # Shell wrapper script
├── field_database.json     # Field database (auto-generated)
├── scripts/
│   ├── analyze_known_pages.py     # Database generator
│   ├── api_explorer.py            # Development utility
│   └── fetch_sample_pages.py      # Sample data fetcher
├── test/
│   ├── sample_pages/              # Test XML samples
│   └── test_*.py                  # Test suite
└── xcc_data/                      # Live XML data cache
```

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

4. **Set up shell integration:**
   ```bash
   chmod +x xcc
   # Optional: add to PATH
   sudo ln -s $(pwd)/xcc /usr/local/bin/xcc
   ```

**Note:** The field database is automatically generated on first run if missing.

## Quick Start

### List Available Pages
```bash
# Using Python script directly
python xcc_cli.py pages

# Using shell wrapper (if installed)
xcc pages
```

### View Configuration Fields
```bash
# List all settable fields in spot pricing page
xcc spot --list

# List all fields (including read-only) in PV page
xcc fve --list-all

# Show detailed info about a specific field
xcc fve --show FVE-USEMODE

# Get current value of a field
xcc tuv1 --get TUVPOZADOVANA
```

### Search and Filter
```bash
# Search for battery-related fields in PV page
xcc fve --search battery

# Search across all pages
xcc search temperature
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

**Shell Script (Recommended):**
```bash
xcc --lang cz spot --list
```

**Python Script (Direct):**
```bash
python xcc_cli.py --lang cz spot --list
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
xcc spot --list

# Check current battery mode
xcc fve --get FVE-USEMODE

# Search for temperature-related settings
xcc okruh --search temperature
```

### Advanced Usage
```bash
# Use Czech descriptions (global options come first)
xcc --lang cz spot --list

# Custom credentials with verbose output
xcc --username admin --password secret123 -v pages

# Show entity output during data fetching
xcc --show-entities fve --list
```

### Database Management
```bash
# Check if database needs refresh
xcc refresh-db

# Force database refresh after firmware update
xcc refresh-db --force
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
xcc -v pages

# Check with custom IP
xcc --ip 192.168.1.100 pages
```

### Database Issues
```bash
# Force refresh database
xcc refresh-db --force

# Manual database generation
python analyze_known_pages.py
```

### Authentication Issues
```bash
# Use custom credentials
xcc --username myuser --password mypass pages
```



## Architecture

### Data Flow
1. **Static Database**: Field definitions loaded from `field_database.json`
2. **Live Connection**: Current values fetched from controller XML endpoints
3. **Hybrid Display**: Combined static metadata with live values

### File Structure
- `xcc_cli.py` - Main CLI application (Click-based)
- `xcc` - Shell wrapper script with virtual environment activation
- `xcc_client.py` - Reusable XCC client library
- `scripts/analyze_known_pages.py` - Database generator
- `field_database.json` - Field database (auto-generated)
- `requirements.txt` - Python dependencies (includes Click)

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
