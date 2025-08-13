# XCC Page Scraper CLI Tool

A simple command-line tool to discover and download all pages from your XCC heat pump controller using the same logic as the Home Assistant integration.

## 🚀 Quick Start

### 1. Setup Environment
```bash
python setup_scraper.py
```

### 2. Configure Your XCC Controller
Edit `xcc_config.json`:
```json
{
  "host": "192.168.1.100",
  "username": "xcc",
  "password": "your_password",
  "output_dir": "./xcc_data"
}
```

### 3. Run the Scraper
```bash
scraper_venv/Scripts/python.exe xcc_scraper.py --config xcc_config.json
```

## 📋 Usage Options

### Option 1: Configuration File (Recommended)
```bash
python xcc_scraper.py --config xcc_config.json
```

### Option 2: Command Line Arguments
```bash
python xcc_scraper.py --host 192.168.1.100 --username xcc --password your_password
```

### Option 3: Custom Output Directory
```bash
python xcc_scraper.py --config xcc_config.json --output-dir ./my_xcc_backup
```

### Option 4: Verbose Logging
```bash
python xcc_scraper.py --config xcc_config.json --verbose
```

## 🔍 What It Does

### **Automatic Page Discovery**
- **Fetches main.xml** to discover all available pages
- **Identifies active systems** using the same logic as the HA integration
- **Finds data pages** (e.g., FVE4.XML, OKRUH10.XML) automatically
- **Detects all page types**: heating, hot water, photovoltaics, weather, pools, etc.

### **Comprehensive Download**
- **Descriptor pages**: Configuration and setup pages (fve.xml, okruh.xml, etc.)
- **Data pages**: Real-time data pages (FVE4.XML, OKRUH10.XML, etc.)
- **Organized output**: Separate files for each page type
- **Summary report**: JSON file with discovery and download results

## 📁 Output Structure

```
xcc_data/
├── descriptor_fve.xml              # Photovoltaics descriptor
├── descriptor_okruh.xml            # Heating circuits descriptor
├── descriptor_tuv1.xml             # Hot water descriptor
├── descriptor_biv.xml              # Bivalent heating descriptor
├── descriptor_pocasi.xml           # Weather forecast descriptor
├── data_FVE4.XML                   # Photovoltaics data
├── data_OKRUH10.XML                # Heating circuits data
├── data_TUV11.XML                  # Hot water data
├── data_BIV1.XML                   # Bivalent heating data
├── data_POCASI1.XML                # Weather data
└── discovery_summary.json          # Discovery and download summary
```

## 📊 Discovery Summary

The `discovery_summary.json` file contains:
```json
{
  "discovery_timestamp": 1692123456.789,
  "xcc_controller": {
    "host": "192.168.1.100",
    "username": "xcc"
  },
  "discovery_results": {
    "descriptor_pages": {
      "count": 8,
      "pages": ["okruh.xml", "tuv1.xml", "fve.xml", "biv.xml", ...],
      "downloaded": 8,
      "files": {"okruh.xml": "./xcc_data/descriptor_okruh.xml", ...}
    },
    "data_pages": {
      "count": 10,
      "pages": ["OKRUH10.XML", "TUV11.XML", "FVE4.XML", ...],
      "downloaded": 10,
      "files": {"OKRUH10.XML": "./xcc_data/data_OKRUH10.XML", ...}
    }
  },
  "total_pages": 18,
  "total_downloaded": 18
}
```

## 🛠️ Advanced Usage

### Create Configuration File
```bash
python xcc_scraper.py --create-config
```

### Manual Setup (if setup script fails)
```bash
# Create virtual environment
python -m venv scraper_venv

# Activate virtual environment (Windows)
scraper_venv\Scripts\activate

# Install dependencies
pip install -r requirements-scraper.txt

# Run scraper
python xcc_scraper.py --config xcc_config.json
```

## 🔧 Troubleshooting

### Import Errors
- Make sure you're running from the `xcc-integration` directory
- The script needs access to `custom_components/xcc/` modules

### Connection Errors
- Verify your XCC controller IP address and credentials
- Ensure the XCC controller is accessible on your network
- Check firewall settings

### Authentication Errors
- Verify username and password are correct
- Try accessing the XCC web interface manually first

### Missing Dependencies
- Run `python setup_scraper.py` to install all dependencies
- Or manually install: `pip install aiohttp lxml aiofiles`

## 🎯 Use Cases

### **Backup Your XCC Configuration**
- Download all configuration and data pages
- Create a complete snapshot of your system
- Useful before making changes to your XCC setup

### **Development and Testing**
- Get sample data for integration development
- Test parsing logic with real controller data
- Analyze page structures and data formats

### **System Analysis**
- Discover all available systems in your XCC controller
- Find pages you might not know existed
- Analyze system configuration and status

### **Integration Debugging**
- Compare scraped data with integration behavior
- Verify page discovery logic
- Troubleshoot missing entities

---

This tool uses the exact same discovery and fetching logic as the Home Assistant integration, ensuring consistency and reliability!
