# XCC Heat Pump Controller Integration

Home Assistant integration for XCC heat pump controllers with photovoltaic integration. Monitor and control your heat pump system directly from Home Assistant with automatic entity discovery and bilingual support.

## 🏠 Home Assistant Integration Features

- 🔧 **470+ settable fields** automatically discovered across 6 configuration pages
- 📊 **Live data monitoring** with real-time sensor values
- 🌐 **Bilingual support** (English/Czech with auto-detection)
- 📋 **Organized by device** (heating, PV, hot water, auxiliary source, etc.)

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
   - Enter your XCC controller details

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
```

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

