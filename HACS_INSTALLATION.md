# HACS Installation Guide

## 🚀 Quick Installation via HACS Custom Repository

### Step 1: Add Custom Repository

1. **Open HACS** in your Home Assistant
2. **Click the 3 dots** (⋮) in the top right corner  
3. **Select "Custom repositories"**
4. **Add this repository**:
   - **Repository**: `https://github.com/pvyleta/xcc-integration`
   - **Category**: `Integration`
5. **Click "Add"**

### Step 2: Install Integration

1. **Go to HACS > Integrations**
2. **Search for "XCC Heat Pump Controller"**
3. **Click "Download"**
4. **Restart Home Assistant**

### Step 3: Configure Integration

1. **Go to** Settings > Devices & Services
2. **Click "Add Integration"**
3. **Search for "XCC Heat Pump Controller"**
4. **Enter your XCC controller details**:
   - IP Address: Your XCC controller IP
   - Username: Your XCC username  
   - Password: Your XCC password
   - Scan Interval: 30 seconds (recommended)

## ✅ What You'll Get

- 🌡️ **Temperature sensors** (outdoor, indoor, water temperatures)
- 🔄 **Status sensors** (compressor, pump, operation mode)
- 🎛️ **Controls** (switches, temperature setpoints, operation modes)
- 📊 **Performance metrics** (power consumption, efficiency)
- 🌐 **Multi-language** support (English/Czech with auto-detection)
- 📡 **MQTT discovery** (automatic if MQTT configured)

## 🔧 Troubleshooting

### Integration Not Appearing
- Ensure you added the repository correctly
- Refresh HACS and search again
- Check HACS logs for any errors

### Connection Issues  
- Verify XCC controller IP is reachable from Home Assistant
- Check username/password are correct
- Ensure XCC controller web interface is accessible

### MQTT Issues
- MQTT features are optional - integration works without MQTT
- If you want MQTT discovery, ensure MQTT broker is configured in HA

## 📚 More Information

- [Full Documentation](README-integration.md)
- [Testing Guide](TESTING.md)
- [GitHub Repository](https://github.com/pvyleta/xcc-integration)

## 🆘 Support

If you encounter issues:
1. Check Home Assistant logs (Settings > System > Logs)
2. Look for "xcc" or "custom_components" errors
3. [Open an issue](https://github.com/pvyleta/xcc-integration/issues) on GitHub
