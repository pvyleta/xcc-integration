# XCC Integration Deployment Guide

This guide explains how to test, deploy, and distribute your XCC Home Assistant integration.

## 🧪 Testing Your Integration

### 1. Local Testing with Docker

The easiest way to test your integration is using the provided Docker environment:

```bash
# Start the development environment
./start_dev_environment.sh

# This will start:
# - Home Assistant at http://localhost:8123
# - Mock XCC controller at http://localhost:8080
# - MQTT broker at localhost:1883
```

**Testing Steps:**
1. Open Home Assistant at http://localhost:8123
2. Complete the initial setup
3. Go to Settings > Devices & Services
4. Click "Add Integration"
5. Search for "XCC Heat Pump Controller"
6. Configure with:
   - IP: `xcc-mock` (or `localhost:8080`)
   - Username: `xcc`
   - Password: `xcc`
7. Verify entities are created and updating

### 2. Manual Testing on Real Home Assistant

```bash
# Copy integration to your HA custom_components
cp -r custom_components/xcc /path/to/homeassistant/custom_components/

# Restart Home Assistant
# Then add the integration via UI
```

### 3. Automated Testing

```bash
# Run all tests
./run_tests.sh

# Or run individual test suites
python -m pytest tests/test_config_flow.py -v
python -m pytest tests/test_coordinator.py -v
python -m pytest tests/test_init.py -v
```

## 📦 Distribution Methods

### Method 1: HACS (Home Assistant Community Store) - Recommended

HACS is the preferred way to distribute custom integrations.

**Prerequisites:**
- GitHub repository with your integration
- Proper repository structure
- Valid `hacs.json` file
- Releases with proper tags

**Steps to get into HACS:**

1. **Prepare Repository Structure:**
   ```
   your-repo/
   ├── custom_components/
   │   └── xcc/
   │       ├── __init__.py
   │       ├── manifest.json
   │       └── ... (all integration files)
   ├── hacs.json
   ├── README.md
   └── .github/workflows/
   ```

2. **Create GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial XCC integration"
   git remote add origin https://github.com/pvyleta/xcc-integration.git
   git push -u origin main
   ```

3. **Create First Release:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **Submit to HACS:**
   - Go to [HACS Integration Requests](https://github.com/hacs/default/issues/new?assignees=&labels=integration&template=integration.yml)
   - Fill out the form with your repository details
   - Wait for approval (usually takes a few days)

### Method 2: Manual Distribution

**Create Release Package:**
```bash
# Create ZIP file for manual installation
cd custom_components
zip -r xcc-v1.0.0.zip xcc/
```

**Users install by:**
1. Downloading the ZIP file
2. Extracting to `custom_components/xcc/`
3. Restarting Home Assistant

### Method 3: Home Assistant Core Integration

For inclusion in Home Assistant core (official distribution):

**Requirements:**
- High code quality
- Comprehensive tests (>90% coverage)
- Popular device/service
- Active maintenance commitment
- Follows HA development guidelines

**Process:**
1. Meet all quality requirements
2. Submit PR to [home-assistant/core](https://github.com/home-assistant/core)
3. Pass code review process
4. Integration gets included in next HA release

## 🚀 Deployment Checklist

### Before First Release

- [ ] All tests pass (`./run_tests.sh`)
- [ ] Integration validates (`python validate_integration.py`)
- [ ] Docker environment works (`./start_dev_environment.sh`)
- [ ] Manual testing completed
- [ ] Documentation is complete
- [ ] `hacs.json` is configured
- [ ] GitHub repository is public
- [ ] CI/CD pipeline is working

### Release Process

1. **Update Version:**
   ```bash
   # Update version in manifest.json files
   # Update CHANGELOG.md
   ```

2. **Create Git Tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **GitHub Actions will automatically:**
   - Run tests
   - Validate integration
   - Create release ZIP
   - Publish to GitHub Releases

### Post-Release

- [ ] Test installation via HACS
- [ ] Monitor for user issues
- [ ] Update documentation as needed
- [ ] Plan next features/fixes

## 🔧 Making Your Integration Installable in HAOS

Home Assistant Operating System (HAOS) users can install your integration through:

### 1. HACS (Easiest for Users)
- Once approved in HACS, users can install with a few clicks
- Automatic updates
- No technical knowledge required

### 2. SSH/Terminal Access
Users with SSH access can install manually:
```bash
# SSH into HAOS
ssh root@homeassistant.local

# Navigate to custom_components
cd /config/custom_components

# Download and extract your integration
wget https://github.com/pvyleta/xcc-integration/releases/latest/download/xcc.zip
unzip xcc.zip

# Restart Home Assistant
ha core restart
```

### 3. File Editor Add-on
Users can use the File Editor add-on to upload files directly through the web interface.

## 📊 Monitoring and Maintenance

### User Feedback
- Monitor GitHub issues
- Check Home Assistant community forum
- Respond to HACS integration issues

### Updates
- Regular dependency updates
- Home Assistant compatibility updates
- Bug fixes and new features

### Quality Metrics
- Test coverage
- User adoption (GitHub stars, HACS downloads)
- Issue resolution time
- Code quality scores

## 🎯 Success Metrics

Your integration is successful when:
- [ ] Users can easily install it
- [ ] It works reliably with their XCC controllers
- [ ] Entities are properly discovered and functional
- [ ] MQTT integration works as expected
- [ ] Multi-language support works correctly
- [ ] No major bugs reported
- [ ] Positive user feedback

## 🆘 Troubleshooting Common Issues

### Integration Not Appearing in HACS
- Check `hacs.json` format
- Ensure repository is public
- Verify release tags exist
- Check HACS submission status

### Installation Fails
- Verify manifest.json format
- Check Python dependencies
- Ensure all required files are present
- Test with Docker environment first

### Entities Not Created
- Check coordinator data fetching
- Verify XCC client communication
- Review entity type determination logic
- Check Home Assistant logs

### MQTT Not Working
- Verify MQTT broker configuration
- Check discovery message format
- Ensure topics are correct
- Test MQTT manually

Remember: Start with local testing, then Docker environment, then real Home Assistant, and finally distribute via HACS for the best user experience!
