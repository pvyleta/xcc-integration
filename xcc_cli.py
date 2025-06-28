#!/usr/bin/env python3
"""XCC Heat Pump Controller CLI - Professional interface for XCC controllers."""

import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from tabulate import tabulate
import click
from xcc_client import XCCClient

class XCCController:
    def __init__(self, ip: str, username: str = "xcc", password: str = "xcc",
                 verbose: bool = False, show_entities: bool = False, language: str = "en"):
        self.ip = ip
        self.username = username
        self.password = password
        self.verbose = verbose
        self.show_entities = show_entities
        self.language = language.lower()
        self.session = None
        self.field_database = {}
        self.current_values = {}
        self.pages_info = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def get_field_description(self, field_info: Dict[str, Any]) -> str:
        """Get field description in the selected language"""
        if self.language == "cz":
            return field_info.get("friendly_name", field_info.get("friendly_name_en", ""))
        else:
            return field_info.get("friendly_name_en", field_info.get("friendly_name", ""))

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self):
        """Establish connection and authenticate"""
        self.log("Establishing connection...")
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)

        # Try to load existing cookie
        cookie_file = "xcc_data/session.cookie"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, "r") as f:
                    saved = json.load(f)
                    session_cookie = saved.get("SoftPLC")
                    if session_cookie:
                        self.log(f"Found existing session cookie: {session_cookie}")
                        from yarl import URL
                        self.session.cookie_jar.update_cookies(
                            {"SoftPLC": session_cookie}, response_url=URL(f"http://{self.ip}/")
                        )
                        # Test if cookie is still valid
                        if await self._validate_session():
                            print("✓ Reusing existing session")
                            return
            except Exception as e:
                self.log(f"Failed to load existing cookie: {e}")

        # Perform fresh authentication
        self.log("Performing fresh authentication...")
        await self._authenticate()
        print("✓ Authenticated successfully")
        
    async def _validate_session(self) -> bool:
        """Check if existing session is still valid"""
        try:
            url = f"http://{self.ip}/INDEX.XML"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    return "<LOGIN>" not in content and "500" not in content
        except Exception:
            pass
        return False
        
    async def _authenticate(self):
        """Perform authentication"""
        # Get login page
        login_xml_url = f"http://{self.ip}/LOGIN.XML"
        async with self.session.get(login_xml_url) as resp:
            if resp.status != 200:
                raise Exception("Failed to get LOGIN.XML")
                
        # Get session ID
        session_id = next((c.value for c in self.session.cookie_jar if c.key == "SoftPLC"), None)
        if not session_id:
            raise Exception("No SoftPLC cookie found")
            
        # Login
        passhash = hashlib.sha1(f"{session_id}{self.password}".encode()).hexdigest()
        login_url = f"http://{self.ip}/RPC/WEBSES/create.asp"
        payload = {"USER": self.username, "PASS": passhash}
        
        async with self.session.post(login_url, data=payload) as resp:
            if resp.status != 200:
                raise Exception("Login failed")
                
        # Save cookie
        session_cookie = next((c.value for c in self.session.cookie_jar if c.key == "SoftPLC"), None)
        if session_cookie:
            os.makedirs("xcc_data", exist_ok=True)
            with open("xcc_data/session.cookie", "w") as f:
                json.dump({"SoftPLC": session_cookie}, f)
                
    async def disconnect(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            
    def load_field_database(self, filename: str = "field_database.json"):
        """Load the field database from analysis file, generate if missing"""
        if not os.path.exists(filename):
            print(f"Field database not found, will generate on first use...")
            # Don't auto-generate during initialization, only when actually needed
            self.field_database = {}
            self.pages_info = {}
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Store page information
            for page_name, page_data in data["pages"].items():
                if "page_info" in page_data:
                    self.pages_info[page_name] = page_data["page_info"]

            # Flatten all fields from all pages
            for page_name, page_data in data["pages"].items():
                if "settable_fields" in page_data:
                    for field_name, field_info in page_data["settable_fields"].items():
                        field_info["source_page"] = page_name
                        self.field_database[field_name] = field_info

            self.log(f"Loaded {len(self.field_database)} settable fields from {len(self.pages_info)} pages")
            print(f"✓ Loaded {len(self.field_database)} settable fields from database")

        except FileNotFoundError:
            print("⚠ Field database not found and generation failed.")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Error loading field database: {e}")
            sys.exit(1)

    def _generate_field_database(self):
        """Generate field database by running analyze script"""
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "scripts/analyze_known_pages.py", self.ip, self.username, self.password
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print("✓ Field database generated successfully")
            else:
                print(f"⚠️ Database generation failed: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Could not generate database: {e}")
            print(f"Please run 'python scripts/analyze_known_pages.py {self.ip}' manually")
            
    async def get_current_values(self):
        """Fetch current values from the controller"""
        if not self.show_entities:
            print("Fetching current values...")

        try:
            # Use the new XCC client
            async with XCCClient(
                ip=self.ip,
                username=self.username,
                password=self.password,
                cookie_file="xcc_data/session.cookie"
            ) as client:
                # Fetch all standard pages
                from xcc_client import STANDARD_PAGES
                pages_data = await client.fetch_pages(STANDARD_PAGES)

                # Parse entities from all pages
                all_entities = []
                for page_name, xml_content in pages_data.items():
                    if not xml_content.startswith("Error:"):
                        from xcc_client import parse_xml_entities
                        entities = parse_xml_entities(xml_content, page_name)
                        all_entities.extend(entities)

                # Convert to current_values format
                for entity in all_entities:
                    field_name = entity["attributes"]["field_name"]
                    self.current_values[field_name] = entity["state"]

                if self.show_entities:
                    print(f"Fetched {len(all_entities)} entities from {len(pages_data)} pages")

        except Exception as e:
            print(f"⚠️ Failed to fetch current values: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
        
        # Parse the current values from the XML files
        pairs = [
            ("STAVJED.XML", "STAVJED1.XML"),
            ("OKRUH.XML", "OKRUH10.XML"),
            ("TUV1.XML", "TUV11.XML"),
            ("BIV.XML", "BIV1.XML"),
            ("FVE.XML", "FVE4.XML"),
            ("SPOT.XML", "SPOT1.XML")
        ]
        
        from lxml import etree
        
        for desc_file, val_file in pairs:
            val_path = f"xcc_data/{val_file}"
            if os.path.exists(val_path):
                try:
                    with open(val_path, "rb") as f:
                        root = etree.parse(f).getroot()
                        
                    for node in root.findall(".//INPUT"):
                        prop = node.attrib.get("P")
                        value = node.attrib.get("VALUE")
                        if prop and value is not None:
                            self.current_values[prop] = value
                            
                except Exception as e:
                    print(f"⚠ Error parsing {val_file}: {e}")
                    
        print(f"✓ Loaded {len(self.current_values)} current values")

    def get_page_fields(self, page_name: str) -> Dict[str, Any]:
        """Get all settable fields for a specific page"""
        return {k: v for k, v in self.field_database.items()
                if v.get("source_page") == page_name}

    def get_all_page_fields(self, page_name: str) -> Dict[str, Any]:
        """Get all fields (settable + read-only) for a specific page"""
        # This would need to fetch from the live XML descriptors
        # For now, we'll enhance the existing method to show settable status
        settable_fields = self.get_page_fields(page_name)

        # Add settable indicator to each field
        for field_name, field_info in settable_fields.items():
            field_info["is_settable"] = True

        # TODO: In the future, we could also fetch read-only fields from XML descriptors
        # and add them with is_settable = False

        return settable_fields

    def get_available_pages(self) -> List[str]:
        """Get list of available pages"""
        if not self.field_database and not os.path.exists("field_database.json"):
            print("Field database not found. Please generate it first:")
            print(f"  python scripts/analyze_known_pages.py {self.ip}")
            return []
        pages = set()
        for field_info in self.field_database.values():
            if "source_page" in field_info:
                pages.add(field_info["source_page"])
        return sorted(list(pages))

    def format_page_table(self, page_name: str, show_all: bool = False) -> str:
        """Format page fields as a nice table"""
        if show_all:
            fields = self.get_all_page_fields(page_name)
        else:
            fields = self.get_page_fields(page_name)

        if not fields:
            return f"No fields found for page {page_name}"

        # Prepare table data
        table_data = []
        headers = ["Field", "Type", "Current Value", "Description", "Constraints", "Access"]

        for field_name, field_info in sorted(fields.items()):
            # Get current value
            current_value = self.current_values.get(field_name, "N/A")

            # Format current value based on type
            if field_info.get("data_type") == "enum" and "options" in field_info:
                # Find the option text for current value
                for option in field_info["options"]:
                    if option["value"] == str(current_value):
                        current_value = f"{current_value} ({option.get('text_en', option.get('text', ''))})"
                        break
            elif field_info.get("data_type") == "boolean":
                current_value = "✓" if current_value == "1" else "✗"

            # Get description in selected language
            description = self.get_field_description(field_info)
            if len(description) > 40:
                description = description[:37] + "..."

            # Get constraints
            constraints = []
            if field_info.get("data_type") == "numeric":
                if "min_value" in field_info:
                    constraints.append(f"min: {field_info['min_value']}")
                if "max_value" in field_info:
                    constraints.append(f"max: {field_info['max_value']}")
                if "unit" in field_info:
                    constraints.append(f"unit: {field_info['unit']}")
            elif field_info.get("data_type") == "enum" and "options" in field_info:
                option_count = len(field_info["options"])
                constraints.append(f"{option_count} options")

            constraint_str = ", ".join(constraints) if constraints else ""

            # Determine access type
            is_settable = field_info.get("is_settable", True)  # Default to settable for existing fields
            access_indicator = "🔧" if is_settable else "👁️"

            table_data.append([
                field_name,
                field_info.get("data_type", "unknown"),
                current_value,
                description,
                constraint_str,
                access_indicator
            ])

        return tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[25, 10, 15, 35, 18, 5])

    def search_fields(self, query: str) -> Dict[str, Any]:
        """Search for fields matching the query"""
        results = {}
        query_lower = query.lower()
        
        for field_name, field_info in self.field_database.items():
            # Search in field name
            if query_lower in field_name.lower():
                results[field_name] = field_info
                continue
                
            # Search in friendly names
            friendly_name = field_info.get("friendly_name", "")
            friendly_name_en = field_info.get("friendly_name_en", "")
            
            if (query_lower in friendly_name.lower() or 
                query_lower in friendly_name_en.lower()):
                results[field_name] = field_info
                
        return results
        
    def display_field_info(self, field_name: str, field_info: Dict[str, Any], show_current: bool = True):
        """Display detailed information about a field"""
        print(f"\n📋 Field: {field_name}")
        print(f"   Type: {field_info.get('data_type', 'unknown')}")
        print(f"   Element: {field_info.get('element_type', 'unknown')}")
        
        # Friendly name in selected language
        description = self.get_field_description(field_info)
        if description:
            lang_label = "CS" if self.language == "cz" else "EN"
            print(f"   Name ({lang_label}): {description}")
            
        # Current value
        if show_current and field_name in self.current_values:
            current_val = self.current_values[field_name]
            print(f"   Current: {current_val}")
            
        # Constraints
        if field_info.get("data_type") == "numeric":
            if "min_value" in field_info:
                print(f"   Min: {field_info['min_value']}")
            if "max_value" in field_info:
                print(f"   Max: {field_info['max_value']}")
            if "unit" in field_info:
                print(f"   Unit: {field_info['unit']}")
                
        # Options for enum fields
        if field_info.get("data_type") == "enum" and "options" in field_info:
            print("   Options:")
            for option in field_info["options"]:
                value = option["value"]
                if self.language == "cz":
                    text = option.get("text", option.get("text_en", value))
                else:
                    text = option.get("text_en", option.get("text", value))
                current_marker = " ← current" if show_current and self.current_values.get(field_name) == value else ""
                print(f"     {value}: {text}{current_marker}")
                
        print(f"   Source: {field_info.get('source_page', 'unknown')}")

# Global Click context for sharing controller instance
@click.group()
@click.option('--ip', required=True, help='Controller IP address')
@click.option('--username', default='xcc', help='Username (default: xcc)')
@click.option('--password', default='xcc', help='Password (default: xcc)')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--show-entities', is_flag=True, help='Show entity output during data fetching')
@click.option('--lang', type=click.Choice(['en', 'cz']), default='en', help='Language for descriptions (default: en)')
@click.pass_context
def cli(ctx, ip, username, password, verbose, show_entities, lang):
    """XCC Heat Pump Controller CLI Tool

    Command-line tool for managing XCC heat pump controllers with photovoltaic integration.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj['ip'] = ip
    ctx.obj['username'] = username
    ctx.obj['password'] = password
    ctx.obj['verbose'] = verbose
    ctx.obj['show_entities'] = show_entities
    ctx.obj['lang'] = lang

def get_controller(ctx) -> XCCController:
    """Get controller instance from context"""
    return XCCController(
        ip=ctx.obj['ip'],
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        verbose=ctx.obj['verbose'],
        show_entities=ctx.obj['show_entities'],
        language=ctx.obj['lang']
    )

@cli.command()
@click.pass_context
def pages(ctx):
    """List all available configuration pages"""
    controller = get_controller(ctx)
    controller.load_field_database()

    click.echo("\n📋 Available Configuration Pages:")
    click.echo("=" * 35)

    for page_name in controller.get_available_pages():
        page_info = controller.pages_info.get(page_name, {})
        page_title = page_info.get("name", page_name)
        field_count = len(controller.get_page_fields(page_name))

        # Map page names to command names
        cmd_name = page_name.replace(".xml", "")
        click.echo(f"  {cmd_name:<12} - {page_title} ({field_count} fields)")

    # Show database info
    db_file = "settable_fields_analysis.json"
    if os.path.exists(db_file):
        try:
            import json
            with open(db_file, "r") as f:
                data = json.load(f)
                timestamp = data.get("metadata", {}).get("timestamp", "unknown")
                if timestamp != "unknown":
                    from datetime import datetime
                    db_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    age = datetime.now() - db_time.replace(tzinfo=None)
                    age_str = f"{age.total_seconds()/60:.1f} minutes ago"
                    click.echo(f"\nDatabase last updated: {age_str}")
                else:
                    click.echo(f"\nDatabase timestamp: {timestamp}")
        except Exception:
            pass

    click.echo(f"\nUse 'xcc_cli.py <page> --list' to see all fields in a page")
    click.echo(f"Use 'xcc_cli.py refresh-db' to update field database")

@cli.command()
@click.argument('query')
@click.pass_context
def search(ctx, query):
    """Search across all pages for fields matching QUERY"""
    controller = get_controller(ctx)
    controller.load_field_database()

    async def do_search():
        async with controller:
            await controller.get_current_values()
            results = controller.search_fields(query)
            if results:
                click.echo(f"\n🔍 Found {len(results)} matching fields across all pages:")
                for field_name, field_info in results.items():
                    controller.display_field_info(field_name, field_info)
            else:
                click.echo(f"❌ No fields found matching '{query}'")

    asyncio.run(do_search())

@cli.command('refresh-db')
@click.option('--force', is_flag=True, help='Force refresh even if database is recent')
@click.pass_context
def refresh_db(ctx, force):
    """Refresh the field database from controller"""
    controller = get_controller(ctx)
    asyncio.run(refresh_field_database(controller, force))

def create_page_command(page_name: str, page_info: Dict[str, Any]):
    """Create a Click command for a specific page"""
    cmd_name = page_name.replace(".xml", "")
    page_title = page_info.get("name", page_name)

    @cli.command(cmd_name)
    @click.option('--list', 'action', flag_value='list', help='List all settable fields in this page')
    @click.option('--list-all', 'action', flag_value='list_all', help='List all fields (settable + read-only) in this page')
    @click.option('--show', 'field_name', help='Show detailed info for a specific field')
    @click.option('--get', 'field_name', help='Get current value of a field')
    @click.option('--search', 'search_query', help='Search fields in this page')
    @click.pass_context
    def page_command(ctx, action, field_name, search_query):
        f"""Manage {page_title} settings"""
        controller = get_controller(ctx)
        controller.load_field_database()

        async def handle_page():
            page_fields = controller.get_page_fields(page_name)

            if action == 'list' or action == 'list_all':
                # Show table of fields in this page
                await controller.get_current_values()
                table = controller.format_page_table(page_name, show_all=(action == 'list_all'))
                page_info = controller.pages_info.get(page_name, {})
                page_title = page_info.get("name", page_name)

                field_type = "All" if action == 'list_all' else "Settable"
                click.echo(f"\n📋 {page_title} Configuration ({field_type} Fields)")
                click.echo("=" * (len(page_title) + len(field_type) + 25))
                click.echo(table)

                if action == 'list_all':
                    all_fields = controller.get_all_page_fields(page_name)
                    settable_count = sum(1 for f in all_fields.values() if f.get("is_settable", True))
                    readonly_count = len(all_fields) - settable_count
                    click.echo(f"\nTotal: {len(all_fields)} fields ({settable_count} settable, {readonly_count} read-only)")
                else:
                    click.echo(f"\nTotal: {len(page_fields)} settable fields")
                    click.echo("Use --list-all to see read-only fields too")

            elif field_name and '--show' in sys.argv:
                if field_name in page_fields:
                    await controller.get_current_values()
                    controller.display_field_info(field_name, page_fields[field_name])
                else:
                    click.echo(f"❌ Field '{field_name}' not found in {page_name}")
                    available = list(page_fields.keys())
                    if available:
                        click.echo(f"Available fields: {', '.join(available[:5])}")
                        if len(available) > 5:
                            click.echo(f"... and {len(available) - 5} more")

            elif field_name and '--get' in sys.argv:
                if field_name in page_fields:
                    await controller.get_current_values()
                    if field_name in controller.current_values:
                        value = controller.current_values[field_name]
                        field_info = page_fields[field_name]

                        # Format the value nicely
                        if field_info.get("data_type") == "enum" and "options" in field_info:
                            for option in field_info["options"]:
                                if option["value"] == str(value):
                                    if controller.language == "cz":
                                        value_text = option.get("text", option.get("text_en", ""))
                                    else:
                                        value_text = option.get("text_en", option.get("text", ""))
                                    click.echo(f"{field_name} = {value} ({value_text})")
                                    break
                            else:
                                click.echo(f"{field_name} = {value}")
                        elif field_info.get("data_type") == "boolean":
                            bool_text = "enabled" if value == "1" else "disabled"
                            click.echo(f"{field_name} = {value} ({bool_text})")
                        else:
                            unit = field_info.get("unit", "")
                            unit_str = f" {unit}" if unit else ""
                            click.echo(f"{field_name} = {value}{unit_str}")
                    else:
                        click.echo(f"❌ No current value available for '{field_name}'")
                else:
                    click.echo(f"❌ Field '{field_name}' not found in {page_name}")

            elif search_query:
                await controller.get_current_values()
                query = search_query.lower()
                results = {}

                for field_name, field_info in page_fields.items():
                    # Search in field name and descriptions
                    if (query in field_name.lower() or
                        query in field_info.get("friendly_name", "").lower() or
                        query in field_info.get("friendly_name_en", "").lower()):
                        results[field_name] = field_info

                if results:
                    click.echo(f"\n🔍 Found {len(results)} matching fields in {page_name}:")
                    for field_name, field_info in results.items():
                        controller.display_field_info(field_name, field_info)
                else:
                    click.echo(f"❌ No fields found matching '{search_query}' in {page_name}")
            else:
                click.echo(f"No action specified for {page_name}. Use --list, --show, --get, or --search")

        asyncio.run(handle_page())

    return page_command

# Initialize page commands dynamically
def init_page_commands():
    """Initialize page-specific commands"""
    # Create a temporary controller to get page info
    temp_controller = XCCController(ip="127.0.0.1", verbose=False)
    temp_controller.load_field_database()

    # Create commands for each page
    for page_name in temp_controller.get_available_pages():
        page_info = temp_controller.pages_info.get(page_name, {})
        create_page_command(page_name, page_info)

async def refresh_field_database(controller: XCCController, force: bool = False):
    """Refresh the field database by running the analysis script"""
    import subprocess
    import os
    from datetime import datetime, timedelta

    db_file = "field_database.json"

    # Check if refresh is needed
    if not force and os.path.exists(db_file):
        try:
            stat = os.stat(db_file)
            file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            if file_age < timedelta(hours=1):
                print(f"📋 Database is recent (modified {file_age.total_seconds()/60:.1f} minutes ago)")
                print("Use --force to refresh anyway")
                return
        except Exception:
            pass

    print("🔄 Refreshing field database from controller...")
    print("This may take a few moments...")

    try:
        # Run the analysis script
        result = subprocess.run([
            "python", "scripts/analyze_known_pages.py", controller.ip, controller.username, controller.password
        ], capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("✅ Field database refreshed successfully!")

            # Reload the database in the current controller instance
            try:
                controller.load_field_database()
                print(f"✅ Loaded {len(controller.field_database)} fields from updated database")
            except Exception as e:
                print(f"⚠ Database updated but failed to reload: {e}")
                print("Please restart the CLI to use the updated database")
        else:
            print("❌ Failed to refresh database:")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")

    except subprocess.TimeoutExpired:
        print("❌ Database refresh timed out (>2 minutes)")
        print("The controller might be slow to respond or unreachable")
    except FileNotFoundError:
        print("❌ analyze_known_pages.py not found")
        print("Make sure you're running from the correct directory")
    except Exception as e:
        print(f"❌ Unexpected error during refresh: {e}")

if __name__ == "__main__":
    # Initialize page commands
    init_page_commands()

    # Run the CLI
    cli()
