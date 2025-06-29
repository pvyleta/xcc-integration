import hashlib
import aiohttp
import os
import json
import re
import lxml.etree
from lxml import etree
from yarl import URL
from builtins import open
from dateutil.parser import parse

COOKIE_FILE = "/config/xcc/session.cookie"
ENTITY_PREFIX = "xcc"
TARGET_DIR = "/config/xcc"
PAGES = [
    "stavjed.xml", "STAVJED1.XML",
    "okruh.xml", "OKRUH10.XML",
    "tuv1.xml", "TUV11.XML",
    "biv.xml", "BIV1.XML",
    "fve.xml", "FVE4.XML",
    "spot.xml", "SPOT1.XML",
]

LANG = "cs"  # 'cs' for Czech, 'en' for English

@service
async def xcc_fetch_data():
    """Main entry point: handles session, authentication, download, and parsing."""
    ip = "192.168.0.50"
    username = "xcc"
    password = "xcc"
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    has_valid_cookie = False

    # Reuse existing session cookie if available
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, "r") as f:
                saved = json.load(f)
                session_cookie = saved.get("SoftPLC")
                if session_cookie:
                    cookie_jar.update_cookies(
                        {"SoftPLC": session_cookie}, response_url=URL(f"http://{ip}/")
                    )
                    has_valid_cookie = True
                    log.warning(f"Loaded SoftPLC cookie from file: {session_cookie}")
        except Exception as e:
            log.warning(f"Failed to load session cookie: {e}")

    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    try:
        if has_valid_cookie:
            if await validate_existing_session(session, ip):
                await fetch_and_save_pages(session, ip, TARGET_DIR, PAGES)
                run_entity_parsers()
                return

        if not await perform_login(session, ip, username, password):
            return

        await fetch_and_save_pages(session, ip, TARGET_DIR, PAGES)
        run_entity_parsers()

    finally:
        await session.close()
        log.warning("XCC: Session closed.")

async def validate_existing_session(session, ip):
    """Checks if existing session cookie is still valid."""
    check_url = f"http://{ip}/INDEX.XML"
    async with session.get(check_url) as resp:
        raw = await resp.read()
        text = raw.decode(resp.get_encoding() or "utf-8")
        if resp.status == 200 and "<LOGIN>" not in text and "500" not in text:
            log.warning("Reused session cookie — session still valid.")
            return True
        log.warning(f"Session invalid or expired. Check status: {resp.status}")
        return False

async def perform_login(session, ip, username, password):
    """Performs session login using hashed password."""
    login_xml_url = f"http://{ip}/LOGIN.XML"
    async with session.get(login_xml_url) as resp:
        if resp.status != 200:
            log.error("XCC: LOGIN.XML failed — server may be overloaded or session limit reached.")
            return False

    session_id = next((c.value for c in session.cookie_jar if c.key == "SoftPLC"), None)
    if not session_id:
        log.error("XCC: SoftPLC cookie not found in jar after LOGIN.XML")
        return False

    passhash = hashlib.sha1(f"{session_id}{password}".encode()).hexdigest()
    login_url = f"http://{ip}/RPC/WEBSES/create.asp"
    payload = {"USER": username, "PASS": passhash}

    async with session.post(login_url, data=payload) as resp:
        if resp.status != 200 or "<LOGIN>" in await resp.text():
            log.error("XCC: Login failed — bad credentials or session exhaustion")
            return False

    session_cookie = next((c.value for c in session.cookie_jar if c.key == "SoftPLC"), None)
    if session_cookie:
        with open(COOKIE_FILE, "w") as f:
            json.dump({"SoftPLC": session_cookie}, f)

    return True

def extract_declared_encoding(xml_bytes):
    """Parses encoding from the XML header (e.g., windows-1250)."""
    match = re.search(br'<\?xml[^>]+encoding=["\']([^"\']+)["\']', xml_bytes[:200])
    if match:
        return match.group(1).decode("ascii", errors="replace").lower()
    return "utf-8"

async def fetch_and_save_pages(session, ip, target_dir, page_list):
    """Downloads XML files and writes them in their original encoding with basic sanitization."""
    os.makedirs(target_dir, exist_ok=True)

    for filename in page_list:
        url = f"http://{ip}/{filename}"
        async with session.get(url) as resp:
            if resp.status != 200:
                log.warning(f"Failed to fetch {filename}: Status {resp.status}")
                continue

            raw_bytes = await resp.read()
            encoding = extract_declared_encoding(raw_bytes)

            try:
                data_text = raw_bytes.decode(encoding, errors="replace")
            except Exception as e:
                log.error(f"{filename}: Failed to decode as '{encoding}': {e}")
                continue

            # Replace problem characters but preserve encoding
            sanitized_text = (
                data_text
                .replace('\u00A0', ' ')
                .replace('\u202F', ' ')
                .replace('\u200B', '')
                .replace('\uFEFF', '')
            )

            path = os.path.join(target_dir, filename.upper())
            try:
                with open(path, "w", encoding=encoding, errors="replace") as f:
                    f.write(sanitized_text)
            except Exception as e:
                log.error(f"{filename}: Failed to save with encoding '{encoding}': {e}")

def run_entity_parsers():
    """Parses all configured descriptor/value file pairs and registers entities."""
    pairs = [
        ("STAVJED.XML", "STAVJED1.XML"),
        ("OKRUH.XML", "OKRUH10.XML"),
        ("TUV1.XML", "TUV11.XML"),
        ("BIV.XML", "BIV1.XML"),
        ("FVE.XML", "FVE4.XML"),
        ("SPOT.XML", "SPOT1.XML")
    ]
    descriptor_paths = [os.path.join(TARGET_DIR, d) for d, _ in pairs]
    value_paths = [os.path.join(TARGET_DIR, v) for _, v in pairs]
    entities = parse_entities_from_multiple_sources(descriptor_paths, value_paths, LANG)
    register_entities(entities)

def parse_entities_from_multiple_sources(descriptor_paths, value_paths, lang="cs"):
    """
    Parses XML files into structured entities.
    Uses lang to prefer *_en fields for display, but always includes unit_en for device_class mapping.
    """

    def get_attr(elem, key):
        if elem is None:
            return ""
        return elem.attrib.get(f"{key}_en" if lang == "en" else key, "").strip()

    used_props = set()
    value_nodes = []

    # Step 1: collect all <INPUT> props from value XMLs
    for value_path in value_paths:
        log.warning(f"Parsing XML descriptor: {value_path}")
        try:
            with open(value_path, "rb") as f:
                root = etree.parse(f).getroot()
        except Exception as e:
            log.error(f"Failed to parse {value_path}: {e}")
            continue

        for node in root.findall(".//INPUT"):
            if "P" in node.attrib:
                used_props.add(node.attrib["P"])
                value_nodes.append(node)

    # Step 2: resolve descriptors to names/units
    prop_info = {}
    resolution_sources = {k: 0 for k in [
        "row_elements", "calc_or_data", "block_prop", "label_or_time_fallback", "row_prop_fallback"
    ]}
    resolved = set()

    for descriptor_path in descriptor_paths:
        try:
            root = etree.parse(descriptor_path).getroot()
        except Exception as e:
            log.error(f"Failed to parse {descriptor_path}: {e}")
            continue

        def register(prop, friendly, unit, unit_en, source_key):
            if prop not in resolved:
                prop_info[prop] = {
                    "friendly_name": friendly or prop,
                    "unit": unit,
                    "unit_en": unit_en
                }
                resolved.add(prop)
                resolution_sources[source_key] += 1

        # Prefer specific UI-bound tags
        for tag in ["number", "label", "option", "switch", "choice", "date"]:
            for elem in root.findall(f".//{tag}"):
                prop = elem.attrib.get("prop")
                if not prop or prop not in used_props:
                    continue
                label = get_attr(elem, "text")
                row = elem.find("..")
                while row is not None and row.tag != "row":
                    row = row.find("..")
                row_label = get_attr(row, "text")
                friendly = f"{row_label} — {label}" if label else row_label or prop
                unit = get_attr(elem, "unit")
                unit_en = elem.attrib.get("unit_en", "").strip()
                register(prop, friendly, unit, unit_en, "row_elements")

        for tag in root.findall(".//calc") + root.findall(".//data"):
            prop = tag.attrib.get("prop")
            if prop and prop in used_props and prop not in resolved:
                register(prop, prop, "", "", "calc_or_data")

        for block in root.findall(".//block"):
            prop = block.attrib.get("prop")
            if prop and prop in used_props and prop not in resolved:
                name = get_attr(block, "name")
                register(prop, name or prop, "", "", "block_prop")

        for tag in ["label", "time"]:
            for elem in root.findall(f".//{tag}"):
                prop = elem.attrib.get("prop")
                if not prop or prop in resolved or prop not in used_props:
                    continue
                row = elem.find("..")
                while row is not None and row.tag != "row":
                    row = row.find("..")
                label = get_attr(elem, "text")
                row_label = get_attr(row, "text")
                friendly = f"{row_label} — {label}" if label else row_label or prop
                unit = get_attr(elem, "unit")
                unit_en = elem.attrib.get("unit_en", "").strip()
                register(prop, friendly, unit, unit_en, "label_or_time_fallback")

        for row in root.findall(".//row"):
            prop = row.attrib.get("prop")
            if prop and prop in used_props and prop not in resolved:
                label = get_attr(row, "text")
                register(prop, label or prop, "", "", "row_prop_fallback")

    # Step 3: build Home Assistant entities
    entity_results = []
    skipped_count = 0
    missing_name_count = 0

    for node in value_nodes:
        prop = node.attrib.get("P")
        value = node.attrib.get("VALUE")
        type_str = node.attrib.get("NAME", "")

        if prop not in prop_info:
            log.debug(f"Property '{prop}' has no friendly name definition.")
            missing_name_count += 1
            continue
        if not value:
            log.warning(f"No value provided for prop '{prop}'")
            skipped_count += 1
            continue

        entity_id = f"{ENTITY_PREFIX}_{re.sub(r'[^a-zA-Z0-9_]', '_', prop.lower())}"

        try:
            if "BOOL" in type_str:
                value = value == "1"
                entity_type = "binary_sensor"
            elif "REAL" in type_str:
                value = float(value)
                entity_type = "sensor"
            elif "INT" in type_str:
                value = int(value)
                entity_type = "sensor"
            elif "STRING" in type_str:
                value = str(value)
                entity_type = "sensor"
            elif "DT_" in type_str or "TIME_" in type_str:
                value = parse(value, dayfirst=True).isoformat()
                entity_type = "sensor"
            else:
                raise ValueError(f"Unknown type '{type_str}' for prop '{prop}'")

            entity_results.append((entity_type, entity_id, value, prop_info[prop]))

        except Exception as e:
            log.warning(f"Failed to parse '{entity_id}': {e}")
            skipped_count += 1

    # Summary log
    log.warning("Entity resolution summary:")
    for source, count in resolution_sources.items():
        log.warning(f"  - {source.replace('_', ' ').capitalize()}: {count} props")

    log.warning(
        f"Entity parsing summary: {len(entity_results)} entities created, "
        f"{skipped_count} skipped, {missing_name_count} missing definitions."
    )

    return entity_results

def register_entities(entity_results):
    """Registers entities into Home Assistant, inferring device class from English unit."""
    for entity_type, entity_id, value, meta in entity_results:
        unit = meta["unit"]
        friendly = meta["friendly_name"]

        # Infer device_class from English version of unit (regardless of selected language)
        english_unit = meta.get("unit_en", unit).strip()
        device_class = get_device_class_by_unit(english_unit)

        attributes = {
            "friendly_name": friendly,
            "unit_of_measurement": unit,
            "source": "xcc"
        }

        if device_class:
            attributes["device_class"] = device_class
        elif english_unit:  # Log unrecognized units
            log.debug(f"Unrecognized unit for device_class: '{english_unit}'")

        state.set(f"{entity_type}.{entity_id}", value, attributes)

def get_device_class_by_unit(unit: str) -> str | None:
    """Maps known English units to Home Assistant device classes."""
    unit = unit.strip().lower()
    device_class_map = {
        "°c": "temperature",
        "c": "temperature",
        "°f": "temperature",
        "kwh": "energy",
        "wh": "energy",
        "kw": "power",
        "w": "power",
        "v": "voltage",
        "a": "current",
        "pa": "pressure",
        "hpa": "pressure",
        "bar": "pressure",
        "hz": "frequency",
        "l": "volume",
        "l/min": "volume_flow_rate",
        "m³": "gas",
        "m³/h": "gas",
        "rpm": "rotational_speed",
        "s": "duration",
        "ms": "duration",
        "hours": "duration",
        "days": "duration",
        "°": "angle",
        "mm": "length",
        "cm": "length",
        "m": "length",
        "lux": "illuminance",
        "€/mwh": None,
    }

    if unit and unit not in device_class_map:
        log.warning(f"Unrecognized unit for device_class: '{unit}'")

    return device_class_map.get(unit)

