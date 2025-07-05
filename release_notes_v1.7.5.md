## 🔧 Bug Fixes

### Fixed Sensor Value Updates
This release resolves the critical issue where sensor values were not updating in Home Assistant despite the integration successfully fetching data from the XCC controller.

**Key Changes:**
- Fixed coordinator data structure to store state values correctly
- Fixed entity value retrieval for proper data access  
- Enhanced logging to track data flow and debugging
- Added fallback logic for better sensor platform reliability

**What's Fixed:**
- ✅ Sensor values now update properly in Home Assistant
- ✅ Temperature, power, and other readings display current values
- ✅ Values refresh according to configured scan interval

**Upgrade Instructions:**
1. Update through HACS or manually
2. Restart Home Assistant  
3. Verify sensor values are updating

The root cause was a data structure mismatch between how the coordinator stored data and how entities retrieved values. This is now resolved.
