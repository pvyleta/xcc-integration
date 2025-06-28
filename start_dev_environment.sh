#!/bin/bash

echo "🚀 Starting XCC Integration Development Environment"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
mkdir -p ha-config/custom_components
mkdir -p mqtt-data mqtt-logs

# Set permissions
chmod 755 ha-config mqtt-data mqtt-logs

echo "📦 Building and starting containers..."

# Start the development environment
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Development environment started successfully!"
    echo ""
    echo "🌐 Services available at:"
    echo "  - Home Assistant: http://localhost:8123"
    echo "  - XCC Mock Controller: http://localhost:8080"
    echo "  - MQTT Broker: localhost:1883"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Open Home Assistant at http://localhost:8123"
    echo "  2. Complete the initial setup"
    echo "  3. Go to Settings > Devices & Services"
    echo "  4. Click 'Add Integration'"
    echo "  5. Search for 'XCC Heat Pump Controller'"
    echo "  6. Configure with IP: xcc-mock (or localhost:8080)"
    echo "  7. Use credentials: xcc/xcc"
    echo ""
    echo "🔧 Development commands:"
    echo "  - View logs: docker-compose logs -f homeassistant"
    echo "  - Restart HA: docker-compose restart homeassistant"
    echo "  - Stop all: docker-compose down"
    echo ""
else
    echo "❌ Failed to start some services. Check logs:"
    docker-compose logs
    exit 1
fi
