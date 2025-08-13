# XCC Home Assistant Integration Changelog

All notable changes to the XCC Heat Pump Controller Home Assistant integration.

## [1.12.1] - 2025-08-13

### 🎯 Feature Release: NAST Page Integration

This release adds the previously undiscovered `nast.xml` page, providing advanced heat pump settings and controls.

### ✨ New Features

#### **NAST Page Integration**
- **ADDED**: `nast.xml` (Heat Pump Settings) page discovery and integration
- **ADDED**: 145 additional entities from NAST page (+18.7% increase)
- **ADDED**: Advanced heat pump configuration capabilities
- **IMPROVED**: Complete XCC system coverage including professional settings

#### **New Entity Categories**
- **🌡️ Sensor Corrections**: 12 temperature sensor calibration controls (B0-I, B4-I, etc.)
- **🏠 Multi-Zone Controls**: 16 zone temperature offset controls (MZO-ZONA0-OFFSET through MZO-ZONA15-OFFSET)
- **🔧 Power Management**: 22 power restriction controls (global, time-based, external, thermal)
- **🔄 Heat Pump Controls**: 10 heat pump unit on/off switches (TCODSTAVENI0-9)
- **💾 System Management**: 10 backup/restore buttons and configuration controls
- **📋 Circuit Priorities**: Priority settings for heating circuits

### 📊 Impact

#### **Entity Count Improvements**
- **Before**: ~858 entities (v1.12.0)
- **After**: ~1,003 entities (v1.12.1)
- **Improvement**: +145 additional entities
- **Coverage**: Complete XCC system including advanced settings

#### **New Capabilities**
- **Sensor Calibration**: Fine-tune temperature sensor accuracy
- **Power Management**: Control heat pump power consumption limits
- **Multi-Zone Heating**: Manage temperature offsets for up to 16 zones
- **Heat Pump Control**: Individual on/off control for multiple heat pump units
- **System Administration**: Backup and restore system configurations

### 🎯 User Impact

#### **New Entities Available**
- ✅ `number.xcc_b0_i` - Sensor B0 temperature correction
- ✅ `number.xcc_offsetbaz` - Pool temperature offset
- ✅ `number.xcc_mzo_zona0_offset` - Multi-zone 0 temperature offset
- ✅ `number.xcc_omezenivykonuglobalni` - Global power restriction (%)
- ✅ `select.xcc_tcodstaveni0` - Heat pump I on/off control
- ✅ `button.xcc_flash_readwrite` - System backup/restore
- ✅ And 139 more advanced heat pump settings

#### **Professional Features**
- ✅ **Sensor Calibration**: Correct temperature readings for optimal performance
- ✅ **Power Optimization**: Manage electricity consumption and costs
- ✅ **Multi-Zone Comfort**: Fine-tune heating for different areas
- ✅ **System Reliability**: Backup and restore configurations
- ✅ **Advanced Control**: Professional-level heat pump management

### 🔄 Migration

#### **Automatic**
- No configuration changes required
- All existing entities remain unchanged
- New NAST entities appear automatically after restart

#### **Recommended**
1. **Restart Home Assistant** to discover new NAST entities
2. **Check Developer Tools → States** for new entities (search for "nast", "offset", "omezeni")
3. **Review** new advanced controls and add to dashboards as needed
4. **Configure** sensor corrections and power restrictions as desired

### 🧪 Testing

#### **Comprehensive Validation**
- **4 new tests** specifically for NAST page integration
- **All tests PASSING** with real XCC controller data
- **Entity parsing verified** for all 145 new entities
- **Integration completeness** confirmed

---

## [1.12.0] - 2025-08-13

### 🎉 Major Release: Complete Entity Coverage & Platform Stability

This release resolves critical issues with missing entities and platform setup failures, providing comprehensive coverage of XCC controller capabilities.

### 🔧 Critical Fixes

#### **Missing Number Entities Resolved**
- **FIXED**: Number platform setup failure causing 0 number entities despite 109 being available
- **FIXED**: `ConfigEntryNotReady` timeout errors during platform setup  
- **FIXED**: Missing entities like `TUVMINIMALNI` due to platform setup issues
- **IMPROVED**: Non-blocking, resilient number platform setup

#### **Complete Entity Coverage**
- **CHANGED**: Load ALL entities with available data values, ignoring XCC visibility conditions
- **ADDED**: Support for visibility condition parsing (configurable)
- **IMPROVED**: Maximum entity coverage approach for Home Assistant integration

### ✨ New Features

#### **Enhanced Sample Data & Testing**
- **ADDED**: Real XCC controller data in sample files (200KB+ of actual data)
- **UPDATED**: All 9 sample files with real controller data instead of login pages
- **ADDED**: Comprehensive test suite with 15+ new test cases
- **ADDED**: Integration testing with real XCC data validation

#### **Improved Platform Reliability**
- **ADDED**: Timeout protection in all platform setups
- **ADDED**: Graceful error handling and recovery
- **ADDED**: Comprehensive logging for troubleshooting
- **IMPROVED**: Platform setup resilience and stability

### 📊 Impact

#### **Entity Coverage Improvements**
- **Before**: ~661 entities (with visibility filtering)
- **After**: ~858 entities (maximum coverage)
- **Improvement**: +197 additional entities now available
- **Specific**: TUVMINIMALNI and other conditional entities now included

#### **Platform Stability**
- **Before**: Number platform setup failures due to timeouts
- **After**: Resilient, non-blocking platform setup
- **Result**: All entity types (sensors, switches, numbers, selects) working

#### **Testing Coverage**
- **Added**: 6 new comprehensive test files
- **Coverage**: Real XCC data validation, platform setup testing, visibility handling
- **Verification**: All 13 tests passing with real controller data

### 🎯 User Impact

#### **New Entities Available**
After upgrading to v1.12.0, users will see:
- ✅ `number.xcc_tuvminimalni` - TUV Minimum Temperature
- ✅ `number.xcc_tuvpozadovana` - TUV Requested Temperature  
- ✅ `number.xcc_ttuv` - TUV Current Temperature
- ✅ ~109 total number entities (previously 0)
- ✅ ~197 additional entities with visibility conditions
- ✅ Complete coverage of XCC system capabilities

#### **Improved Reliability**
- ✅ No more platform setup timeout errors
- ✅ No more `ConfigEntryNotReady` exceptions
- ✅ Faster, more reliable integration startup
- ✅ Better error handling and recovery

### 🔄 Migration

#### **Automatic**
- No configuration changes required
- Existing entities remain unchanged
- New entities appear automatically after restart

#### **Recommended**
1. **Restart Home Assistant** to apply the updates
2. **Check Developer Tools → States** for new number entities
3. **Verify** `number.xcc_tuvminimalni` and other missing entities appear
4. **Review** new entities and configure dashboards as needed

### 🐛 Bug Fixes

- Fixed number platform setup timeout causing missing entities
- Fixed visibility condition handling for conditional entities
- Fixed test coverage gaps that masked platform setup issues
- Fixed sample data containing login pages instead of real data
- Fixed entity parsing to respect data availability over UI visibility

### 🔧 Technical Improvements

- Enhanced descriptor parser with visibility condition support
- Improved coordinator entity processing and data structuring
- Added comprehensive error handling and logging throughout
- Optimized platform setup for better performance and reliability
- Enhanced test coverage with real XCC controller data validation

---

## [1.11.2] - Previous Release

### Bug Fixes
- Fixed XCC scraper authentication and page discovery
- Improved scraper file organization
- Updated documentation

---

**Full Changelog**: https://github.com/pvyleta/xcc-integration/compare/v1.11.2...v1.12.0
