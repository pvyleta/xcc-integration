#!/usr/bin/env python3
"""
XCC Page Scraper CLI Tool

A simple command-line tool to discover and download all pages from an XCC heat pump controller.
Based on the XCC Home Assistant integration code.

Usage:
    python xcc_scraper.py --host 192.168.1.100 --username xcc --password your_password
    python xcc_scraper.py --host 192.168.1.100 --username xcc --password your_password --output-dir ./xcc_data
    python xcc_scraper.py --config config.json
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Try to import the XCC client, create standalone version if not available
try:
    # Add the custom_components directory to the Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))
    from xcc.xcc_client import XCCClient
    XCC_CLIENT_AVAILABLE = True
except ImportError:
    # Create a standalone XCC client for scraping
    import aiohttp
    import re

    class XCCClient:
        """Standalone XCC client for scraping (without Home Assistant dependencies)."""

        def __init__(self, host: str, username: str, password: str):
            self.host = host
            self.username = username
            self.password = password
            self.session = None
            self.base_url = f"http://{host}"

        async def authenticate(self):
            """Authenticate with the XCC controller."""
            self.session = aiohttp.ClientSession()

            # Test connection
            async with self.session.get(f"{self.base_url}/main.xml") as response:
                if response.status != 200:
                    raise Exception(f"Cannot connect to XCC controller at {self.host}")

        async def fetch_page(self, page: str) -> str:
            """Fetch a page from the XCC controller."""
            if not self.session:
                await self.authenticate()

            url = f"{self.base_url}/{page}"
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch {page}: HTTP {response.status}")

                content = await response.text(encoding='utf-8', errors='replace')
                return content

        async def auto_discover_all_pages(self) -> tuple[list[str], list[str]]:
            """Discover all pages using the same logic as the integration."""
            try:
                # Try the full discovery logic first
                main_content = await self.fetch_page("main.xml")

                # Parse with regex (simplified version)
                xml_content = f'<PAGE>{main_content}</PAGE>'

                # Find all F elements
                f_pattern = r'<F[^>]*U="([^"]+)"[^>]*>(.*?)</F>'
                f_matches = re.findall(f_pattern, xml_content, re.DOTALL)

                descriptor_pages = []

                for page_url, content in f_matches:
                    is_active = False

                    # Method 1: INPUTV with VALUE="1"
                    if 'INPUTV' in content and 'VALUE="1"' in content:
                        is_active = True

                    # Method 2: INPUTI with non-zero VALUE
                    elif not is_active:
                        inputi_pattern = r'INPUTI[^>]*VALUE="([^"]+)"'
                        inputi_matches = re.findall(inputi_pattern, content)
                        for value in inputi_matches:
                            try:
                                int_value = int(value)
                                if int_value > 0:
                                    is_active = True
                                    break
                            except ValueError:
                                pass

                    # Method 3: Special handling for essential pages
                    if not is_active and page_url in ['biv.xml', 'bivtuv.xml', 'stavjed.xml']:
                        if 'INPUTI' in content and 'VALUE=' in content:
                            is_active = True

                    if is_active:
                        desc_page = page_url.split('?')[0]
                        if desc_page not in descriptor_pages:
                            descriptor_pages.append(desc_page)

                # Add essential pages that might not be in main.xml
                essential_pages = ['stavjed.xml', 'okruh.xml', 'tuv1.xml', 'biv.xml', 'fve.xml', 'spot.xml']
                for essential_page in essential_pages:
                    if essential_page not in descriptor_pages:
                        try:
                            content = await self.fetch_page(essential_page)
                            if len(content) > 100 and '<LOGIN>' not in content:
                                descriptor_pages.append(essential_page)
                        except:
                            pass

                # Generate data pages using the same patterns as the integration
                data_pages = []

                # Use the same data page mapping as the integration
                data_page_mapping = {
                    'stavjed.xml': ['STAVJED1.XML'],
                    'okruh.xml': ['OKRUH10.XML'],
                    'tuv1.xml': ['TUV11.XML'],
                    'biv.xml': ['BIV1.XML'],
                    'fve.xml': ['FVE4.XML'],
                    'spot.xml': ['SPOT1.XML'],
                }

                # Add mapped data pages
                for desc_page in descriptor_pages:
                    if desc_page in data_page_mapping:
                        for data_page in data_page_mapping[desc_page]:
                            try:
                                content = await self.fetch_page(data_page)
                                if len(content) > 100 and '<LOGIN>' not in content:
                                    data_pages.append(data_page)
                            except:
                                pass

                # Also try common patterns for discovered pages
                for desc_page in descriptor_pages:
                    if desc_page not in data_page_mapping:
                        base_name = desc_page.replace('.xml', '').upper()
                        potential_data = [
                            f"{base_name}1.XML",
                            f"{base_name}4.XML",
                            f"{base_name}10.XML",
                            f"{base_name}11.XML"
                        ]

                        for data_page in potential_data:
                            if data_page not in data_pages:
                                try:
                                    content = await self.fetch_page(data_page)
                                    if len(content) > 100 and '<LOGIN>' not in content:
                                        data_pages.append(data_page)
                                except:
                                    pass

                return descriptor_pages, data_pages

            except Exception as e:
                # Fallback to integration defaults if discovery fails
                print(f"Discovery failed, using integration defaults: {e}")
                default_descriptors = ["stavjed.xml", "okruh.xml", "tuv1.xml", "biv.xml", "fve.xml", "spot.xml"]
                default_data = ["STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"]
                return default_descriptors, default_data

        async def close(self):
            """Close the session."""
            if self.session:
                await self.session.close()

    # Set flag after successful class definition
    XCC_CLIENT_AVAILABLE = True


class XCCPageScraper:
    """XCC page scraper using the integration's XCC client."""
    
    def __init__(self, host: str, username: str, password: str, output_dir: str = "./xcc_data"):
        self.host = host
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.client: Optional[XCCClient] = None
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def initialize_client(self) -> bool:
        """Initialize and authenticate the XCC client."""
        try:
            self.logger.info(f"🔌 Connecting to XCC controller at {self.host}")
            self.client = XCCClient(self.host, self.username, self.password)
            
            # Test authentication
            await self.client.authenticate()
            self.logger.info("✅ Authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to XCC controller: {e}")
            return False

    async def discover_pages(self) -> tuple[list[str], list[str]]:
        """Discover all available pages using the integration's discovery logic."""
        try:
            self.logger.info("🔍 Starting automatic page discovery...")

            # Use the integration's auto-discovery functionality
            descriptor_pages, data_pages = await self.client.auto_discover_all_pages()

            self.logger.info(f"📋 Discovery complete:")
            self.logger.info(f"   Descriptor pages: {len(descriptor_pages)}")
            self.logger.info(f"   Data pages: {len(data_pages)}")

            # If discovery found nothing, use integration defaults
            if not descriptor_pages and not data_pages:
                self.logger.warning("🔄 Discovery found no pages, using integration defaults...")
                descriptor_pages = ["stavjed.xml", "okruh.xml", "tuv1.xml", "biv.xml", "fve.xml", "spot.xml"]
                data_pages = ["STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"]

                self.logger.info(f"📋 Using defaults:")
                self.logger.info(f"   Descriptor pages: {len(descriptor_pages)}")
                self.logger.info(f"   Data pages: {len(data_pages)}")

            return descriptor_pages, data_pages

        except Exception as e:
            self.logger.error(f"❌ Page discovery failed: {e}")
            self.logger.warning("🔄 Falling back to integration defaults...")

            # Use the same defaults as the integration
            descriptor_pages = ["stavjed.xml", "okruh.xml", "tuv1.xml", "biv.xml", "fve.xml", "spot.xml"]
            data_pages = ["STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"]

            self.logger.info(f"📋 Fallback defaults:")
            self.logger.info(f"   Descriptor pages: {len(descriptor_pages)}")
            self.logger.info(f"   Data pages: {len(data_pages)}")

            return descriptor_pages, data_pages

    async def download_pages(self, pages: list[str], page_type: str) -> dict[str, str]:
        """Download a list of pages and save them to files."""
        downloaded = {}
        
        self.logger.info(f"📥 Downloading {len(pages)} {page_type} pages...")
        
        for page in pages:
            try:
                self.logger.info(f"   Fetching {page}...")
                content = await self.client.fetch_page(page)
                
                # Save to file
                filename = page.replace('?', '_').replace('=', '_')
                file_path = self.output_dir / f"{page_type}_{filename}"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                downloaded[page] = str(file_path)
                self.logger.info(f"   ✅ Saved {page} -> {file_path}")
                
            except Exception as e:
                self.logger.error(f"   ❌ Failed to download {page}: {e}")
        
        return downloaded

    async def save_discovery_info(self, descriptor_pages: list[str], data_pages: list[str], 
                                 downloaded_descriptors: dict, downloaded_data: dict):
        """Save discovery information to a summary file."""
        summary = {
            "discovery_timestamp": asyncio.get_event_loop().time(),
            "xcc_controller": {
                "host": self.host,
                "username": self.username
            },
            "discovery_results": {
                "descriptor_pages": {
                    "count": len(descriptor_pages),
                    "pages": descriptor_pages,
                    "downloaded": len(downloaded_descriptors),
                    "files": downloaded_descriptors
                },
                "data_pages": {
                    "count": len(data_pages),
                    "pages": data_pages,
                    "downloaded": len(downloaded_data),
                    "files": downloaded_data
                }
            },
            "total_pages": len(descriptor_pages) + len(data_pages),
            "total_downloaded": len(downloaded_descriptors) + len(downloaded_data)
        }
        
        summary_file = self.output_dir / "discovery_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"📊 Discovery summary saved to {summary_file}")

    async def scrape_all(self) -> bool:
        """Main scraping function - discover and download all pages."""
        try:
            # Initialize client
            if not await self.initialize_client():
                return False
            
            # Discover pages
            descriptor_pages, data_pages = await self.discover_pages()
            
            if not descriptor_pages and not data_pages:
                self.logger.error("❌ No pages discovered")
                return False
            
            # Download descriptor pages
            downloaded_descriptors = await self.download_pages(descriptor_pages, "descriptor")
            
            # Download data pages
            downloaded_data = await self.download_pages(data_pages, "data")
            
            # Save summary
            await self.save_discovery_info(
                descriptor_pages, data_pages, 
                downloaded_descriptors, downloaded_data
            )
            
            # Print summary
            total_downloaded = len(downloaded_descriptors) + len(downloaded_data)
            total_pages = len(descriptor_pages) + len(data_pages)
            
            self.logger.info(f"\n🎉 Scraping complete!")
            self.logger.info(f"📊 Summary:")
            self.logger.info(f"   Total pages discovered: {total_pages}")
            self.logger.info(f"   Total pages downloaded: {total_downloaded}")
            self.logger.info(f"   Descriptor pages: {len(downloaded_descriptors)}/{len(descriptor_pages)}")
            self.logger.info(f"   Data pages: {len(downloaded_data)}/{len(data_pages)}")
            self.logger.info(f"   Output directory: {self.output_dir}")
            
            return total_downloaded > 0
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return False
        
        finally:
            if self.client:
                await self.client.close()


def load_config(config_file: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config file {config_file}: {e}")
        sys.exit(1)


def create_sample_config(filename: str = "xcc_config.json"):
    """Create a sample configuration file."""
    sample_config = {
        "host": "192.168.1.100",
        "username": "xcc",
        "password": "your_password_here",
        "output_dir": "./xcc_data"
    }
    
    with open(filename, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"📝 Sample configuration created: {filename}")
    print("Edit the file with your XCC controller details and run:")
    print(f"python xcc_scraper.py --config {filename}")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="XCC Page Scraper - Download all pages from XCC heat pump controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python xcc_scraper.py --host 192.168.1.100 --username xcc --password mypass
  python xcc_scraper.py --config xcc_config.json
  python xcc_scraper.py --create-config
        """
    )
    
    parser.add_argument("--host", help="XCC controller IP address")
    parser.add_argument("--username", help="XCC username")
    parser.add_argument("--password", help="XCC password")
    parser.add_argument("--output-dir", default="./xcc_data", help="Output directory for downloaded pages")
    parser.add_argument("--config", help="JSON configuration file")
    parser.add_argument("--create-config", action="store_true", help="Create sample configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if XCC client is available
    if not XCC_CLIENT_AVAILABLE:
        print("❌ XCC client not available. Make sure you're in the xcc-integration directory.")
        sys.exit(1)
    
    # Handle create-config option
    if args.create_config:
        create_sample_config()
        return
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
        host = config.get("host")
        username = config.get("username")
        password = config.get("password")
        output_dir = config.get("output_dir", "./xcc_data")
    else:
        host = args.host
        username = args.username
        password = args.password
        output_dir = args.output_dir
    
    # Validate required parameters
    if not all([host, username, password]):
        print("❌ Error: Missing required parameters")
        print("Use --host, --username, --password or --config file")
        print("Use --create-config to create a sample configuration file")
        sys.exit(1)
    
    # Run the scraper
    scraper = XCCPageScraper(host, username, password, output_dir)
    success = await scraper.scrape_all()
    
    if success:
        print("\n🎉 XCC page scraping completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ XCC page scraping failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
