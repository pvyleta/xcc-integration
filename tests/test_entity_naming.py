"""End-to-end entity-naming verification against recorded controller samples.

Runs every descriptor and data file under ``tests/sample_data`` through the
real parsing pipeline (``parse_xml_entities`` →
``entity_helpers.process_entities``) and asserts that the resulting
entity_ids obey the ``xcc_<slug>`` convention — no IP addresses, no
legacy ``<device>_<ip>_<prop>`` shape, no bare property-name leftovers.

Also spot-checks a handful of known friendly-name mappings that come from
``DESCRIPTOR_OVERRIDES`` (STATUS_XML_DESCRIPTOR, HIDDEN_BINARY_SENSORS,
HIDDEN_SWITCHES) so a regression in the override merge is caught here too.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from types import ModuleType

import pytest

# The integration's ``__init__.py`` imports ``homeassistant`` at module load,
# so we cannot ``from custom_components.xcc.const import ...`` in a pure-unit
# environment. Load the three HA-free helper modules directly from their file
# paths — same files the integration ships, no package side-effects.

_XCC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "custom_components", "xcc")
)


def _load_module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_XCC_DIR, filename)
    )
    assert spec and spec.loader, f"cannot load {filename}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Order matters: xcc_client.py falls back to ``from descriptor_parser import …``
# when its relative import fails, so descriptor_parser must be importable first.
_descriptor_parser = _load_module("descriptor_parser", "descriptor_parser.py")
_const = _load_module("_xcc_const_standalone", "const.py")
_entity_helpers = _load_module("_xcc_entity_helpers_standalone", "entity_helpers.py")
_xcc_client = _load_module("_xcc_client_standalone", "xcc_client.py")

DESCRIPTOR_OVERRIDES = _const.DESCRIPTOR_OVERRIDES
XCCDescriptorParser = _descriptor_parser.XCCDescriptorParser
process_entities = _entity_helpers.process_entities
parse_xml_entities = _xcc_client.parse_xml_entities

# Descriptor (lowercase) files map to the data (uppercase) files they describe.
# STATUS.XML has no paired descriptor; its fields are covered by
# STATUS_XML_DESCRIPTOR via DESCRIPTOR_OVERRIDES.
_DESCRIPTOR_FILES: tuple[str, ...] = (
    "stavjed.xml",
    "okruh.xml",
    "tuv1.xml",
    "biv.xml",
    "fve.xml",
    "fveinv.xml",
    "spot.xml",
)
_DATA_FILES: tuple[str, ...] = (
    "STAVJED1.XML",
    "STATUS.XML",
    "OKRUH10.XML",
    "TUV11.XML",
    "BIV1.XML",
    "FVE4.XML",
    "FVEINV10.XML",
    "SPOT1.XML",
)

_IP_IN_ID = re.compile(r"(?:^|_)(?:[0-9]{1,3}_){3}[0-9]{1,3}(?:_|$)")
_VALID_ID_SUFFIX = re.compile(r"^xcc_[a-z0-9_]+$")


def _load_all(sample_dir: str) -> tuple[dict, list]:
    """Parse every descriptor + data file and merge with DESCRIPTOR_OVERRIDES."""
    descriptor_data: dict[str, str] = {}
    for name in _DESCRIPTOR_FILES:
        path = os.path.join(sample_dir, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            descriptor_data[name] = fh.read()

    parser = XCCDescriptorParser()
    entity_configs = parser.parse_descriptor_files(descriptor_data)
    # Matches XCCDataUpdateCoordinator._load_descriptors: overrides win.
    entity_configs = {**entity_configs, **DESCRIPTOR_OVERRIDES}

    raw_entities: list[dict] = []
    for name in _DATA_FILES:
        path = os.path.join(sample_dir, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            raw_entities.extend(parse_xml_entities(fh.read(), name))

    return entity_configs, raw_entities


def test_entity_ids_have_xcc_prefix_and_no_ip(sample_data_dir):
    """Every processed entity_id must be ``xcc_<slug>`` with no IP-like run."""
    entity_configs, raw_entities = _load_all(sample_data_dir)
    assert raw_entities, "expected at least one parsed entity from sample data"

    processed_data, entities_metadata = process_entities(
        raw_entities, entity_configs, language="english"
    )

    # Every id the pipeline emits appears on both sides (bucket state dicts
    # and the entities_metadata map); verifying both catches bucket drift too.
    seen_ids: set[str] = set()
    for bucket in (
        "sensors",
        "binary_sensors",
        "switches",
        "numbers",
        "selects",
        "buttons",
    ):
        seen_ids.update(processed_data[bucket].keys())
    seen_ids.update(entities_metadata.keys())

    assert seen_ids, "pipeline produced no entity ids"

    bad_prefix = [eid for eid in seen_ids if not eid.startswith("xcc_")]
    assert not bad_prefix, f"entity_ids missing xcc_ prefix: {sorted(bad_prefix)[:5]}"

    bad_chars = [eid for eid in seen_ids if not _VALID_ID_SUFFIX.fullmatch(eid)]
    assert not bad_chars, f"entity_ids with invalid chars: {sorted(bad_chars)[:5]}"

    with_ip = [eid for eid in seen_ids if _IP_IN_ID.search(eid)]
    assert not with_ip, f"entity_ids contain IP-address runs: {sorted(with_ip)[:5]}"

    # Legacy shape: ``<domain>.<device>_<ip>_<prop>`` used to prepend device
    # slugs such as ``stav_jednotky_`` or ``heating_circuit_``. None of these
    # should appear in ids derived from pure prop names.
    legacy_prefixes = (
        "xcc_stav_jednotky_",
        "xcc_heating_circuit_",
        "xcc_hot_water_",
        "xcc_photovoltaics_",
    )
    with_legacy = [eid for eid in seen_ids if eid.startswith(legacy_prefixes)]
    assert not with_legacy, f"legacy device-prefixed ids leaked: {with_legacy[:5]}"


@pytest.mark.parametrize(
    "prop, expected_id, expected_en",
    [
        # HIDDEN_BINARY_SENSORS override (was surfacing as stav_jednotky_obeh_5_aktivni)
        ("BLOKYSPOTREBY-OK", "xcc_blokyspotreby_ok", "HP heating circuit"),
        ("BLOKYSPOTREBY3-OK", "xcc_blokyspotreby3_ok", "HP heating DHW"),
        # STATUS_XML_DESCRIPTOR entry (STATUS.XML has no paired descriptor file)
        ("SVYKON", "xcc_svykon", "HP power"),
        # HIDDEN_SWITCHES override
        ("TO-CONFIG-CHLAZENI", "xcc_to_config_chlazeni",
         "Heating circuit cooling mode configuration"),
    ],
)
def test_known_friendly_names(sample_data_dir, prop, expected_id, expected_en):
    """Spot-check that override-backed props keep their canonical names."""
    entity_configs, raw_entities = _load_all(sample_data_dir)
    _, entities_metadata = process_entities(
        raw_entities, entity_configs, language="english"
    )
    meta = entities_metadata.get(expected_id)
    if meta is None:
        pytest.skip(f"{prop} not present in sample data; nothing to verify")
    assert meta["prop"] == prop
    assert meta["descriptor_config"].get("friendly_name_en") == expected_en
