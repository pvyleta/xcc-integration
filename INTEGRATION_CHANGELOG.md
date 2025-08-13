# XCC Home Assistant Integration Changelog

All notable changes to the XCC Heat Pump Controller Home Assistant integration.

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
