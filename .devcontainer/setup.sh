#!/bin/bash

set -e

echo "🔧 Setting up XCC Integration Development Environment"

# Update package lists
sudo apt-get update

# Install Python requirements
echo "📦 Installing Python requirements..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-test.txt

# Create config directory for Home Assistant
echo "📁 Creating Home Assistant config directory..."
mkdir -p /config
mkdir -p /config/custom_components

# Copy XCC integration to config
echo "📋 Setting up XCC integration..."
cp -r custom_components/xcc /config/custom_components/

# Create basic Home Assistant configuration
if [[ ! -f "/config/configuration.yaml" ]]; then
    echo "📝 Creating Home Assistant configuration..."
    cat > /config/configuration.yaml << 'EOF'
# Home Assistant Configuration for XCC Development
default_config:

# Enable logging for XCC
logger:
  default: info
  logs:
    custom_components.xcc: debug

# MQTT Configuration
mqtt:
  broker: localhost
  port: 1883
  discovery: true
  discovery_prefix: homeassistant

# HTTP Configuration
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - ::1

# Enable developer tools
developer:

# Example automation for XCC testing
automation:
  - alias: "XCC Temperature Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.xcc_outdoor_temperature
      below: 0
    action:
      service: persistent_notification.create
      data:
        title: "XCC Alert"
        message: "Outdoor temperature is below freezing!"
EOF
fi

# Start MQTT broker
echo "📡 Starting MQTT broker..."
sudo systemctl enable mosquitto || echo "Mosquitto service not available"
sudo systemctl start mosquitto || echo "Mosquitto service not available"

# Set up git (if not already configured)
if [[ -z "$(git config --global user.name)" ]]; then
    echo "🔧 Setting up git configuration..."
    git config --global user.name "XCC Developer"
    git config --global user.email "developer@xcc-integration.local"
fi

echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Available commands:"
echo "  hass --config /config --debug    - Start Home Assistant"
echo "  python run_ha_tests.py           - Run integration tests"
echo "  python xcc_mock_server.py        - Start mock XCC controller"
echo "  mosquitto_pub -t test -m hello   - Test MQTT"
echo ""
echo "🌐 Services will be available at:"
echo "  - Home Assistant: http://localhost:8123"
echo "  - XCC Mock Controller: http://localhost:8080"
echo "  - MQTT Broker: localhost:1883"
