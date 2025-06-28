# XCC CLI Changelog

## Version 3.0 - Professional CLI Framework

### 🚀 **Major Architecture Upgrade**

#### **Click Framework Migration**
- **Migrated from argparse to Click** - Professional CLI framework with better UX
- **Flexible option positioning** - Global options work regardless of position
- **Enhanced help system** - Rich, contextual help messages
- **Robust argument parsing** - Better error handling and validation

#### **Shell Integration**
- **`xcc` shell script** - Clean wrapper for easy execution
- **PATH integration** - Install as system command
- **Cross-platform compatibility** - Works on macOS, Linux, Windows

#### **Reusable Architecture**
- **`xcc_client.py`** - Reusable client library for CLI, pyscript, and HA integration
- **Auto-generated database** - Field database creates itself if missing
- **Simplified installation** - No manual database generation required

### 📋 **New Files**
- **`xcc`** - Shell wrapper script with virtual environment activation
- **`xcc_client.py`** - Reusable XCC client library
- **`field_database.json`** - Auto-generated field database

### 🔧 **Improved Command Structure**

#### **Before (argparse):**
```bash
# Options had to be in specific positions
python xcc_cli.py --lang cz spot --list  # ✓ Worked
python xcc_cli.py spot --list --lang cz  # ✗ Failed
```

#### **After (Click):**
```bash
# Global options must come before subcommand (Click standard)
xcc --lang cz spot --list               # ✓ Works
xcc --username admin --password secret123 -v pages  # ✓ Works
```

## Version 2.0 - Enhanced User Experience

### 🎯 **Major Improvements**

#### **Cleaner Output**
- **Entity output suppressed by default** - No more verbose entity listings cluttering the output
- **`--show-entities` flag** - Enable entity output when needed for debugging
- **Compact access indicators** - Just 🔧 for settable fields (instead of "🔧 Settable")

#### **Bilingual Support**
- **`--lang {en,cz}` option** - Choose between English and Czech descriptions
- **Smart language fallback** - Falls back to available language if preferred not found
- **Consistent language usage** - Applied to tables, field details, and option lists

#### **Enhanced Authentication**
- **`--username` and `--password` options** - Override default xcc/xcc credentials
- **Secure credential handling** - Credentials passed directly via command line
- **Connection flexibility** - Support for different controller configurations

#### **Improved Debugging**
- **`-v, --verbose` flag** - Detailed logging with timestamps
- **Connection diagnostics** - Session reuse, authentication status
- **Data fetching insights** - XML parsing, entity resolution statistics

### 📊 **Table Display Enhancements**

#### **Before:**
```
| Access     |
|============|
| 🔧 Settable |
```

#### **After:**
```
| Access |
|========|
| 🔧      |
```

### 🌐 **Language Support Examples**

#### **English (default):**
```bash
python xcc_cli.py fve --show FVE-USEMODE
# Name (EN): Battery mode
# Options:
#   3: Economic ← current
```

#### **Czech:**
```bash
python xcc_cli.py --lang cz fve --show FVE-USEMODE
# Name (CS): Režim baterie
# Options:
#   3: Ekonomický ← current
```

### 🔧 **New Command Line Options**

```bash
# Global options
--username USER         # Custom username (default: xcc)
--password PASS         # Custom password (default: xcc)
--lang {en,cz}         # Language for descriptions (default: en)
-v, --verbose          # Enable verbose debugging output
--show-entities        # Show entity output during data fetching

# Usage examples
python xcc_cli.py --lang cz spot --list
python xcc_cli.py --username admin --password secret123 pages
python xcc_cli.py -v --show-entities fve --list
```

### 📚 **Documentation**

#### **New Files:**
- **`README.md`** - Comprehensive English documentation
- **`README_CZ.md`** - Complete Czech documentation
- **`CHANGELOG.md`** - This changelog

#### **Documentation Features:**
- **Installation guide** with step-by-step instructions
- **Quick start examples** for immediate productivity
- **Command reference** with all options explained
- **Troubleshooting section** for common issues
- **Architecture overview** explaining hybrid data approach

### 🔄 **Backward Compatibility**

All existing commands continue to work exactly as before:
```bash
# These still work unchanged
python xcc_cli.py pages
python xcc_cli.py spot --list
python xcc_cli.py fve --get FVE-USEMODE
python xcc_cli.py refresh-db
```

### 🚀 **Performance Improvements**

- **Reduced output noise** - Faster visual scanning of results
- **Efficient language handling** - No performance impact from bilingual support
- **Smart entity suppression** - Faster execution when entity output not needed

### 🎨 **User Experience**

#### **Cleaner Tables:**
- Compact access indicators save horizontal space
- Language-appropriate descriptions improve readability
- Consistent formatting across all commands

#### **Better Debugging:**
- Verbose mode provides detailed insights without cluttering normal usage
- Entity output available when needed for troubleshooting
- Clear connection status and session management

#### **Flexible Authentication:**
- Support for different controller setups
- Easy credential override for testing
- Secure handling of authentication parameters

### 📈 **Statistics**

- **470+ settable fields** across 6 configuration pages
- **2 languages** supported (English/Czech)
- **6 new command line options** for enhanced control
- **100% backward compatibility** maintained

### 🔮 **Future Ready**

The enhanced architecture supports:
- Easy addition of new languages
- Extensible authentication methods
- Scalable output formatting options
- Modular debugging capabilities

---

## Migration Guide

### From Version 1.x to 2.0

**No changes required!** All existing scripts and commands continue to work.

**Optional enhancements:**
```bash
# Add language preference
python xcc_cli.py --lang cz spot --list

# Use custom credentials
python xcc_cli.py --username myuser --password mypass pages

# Enable debugging when needed
python xcc_cli.py -v fve --get FVE-USEMODE
```

### New Users

Start with the README.md for complete setup and usage instructions.
