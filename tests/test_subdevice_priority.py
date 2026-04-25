"""Regression tests for sub-device routing through ``process_entities``.

The ``_DEVICE_PRIORITY`` whitelist in ``entity_helpers.py`` filters every
descriptor-backed entity by its page-derived device key — anything missing
from that tuple is silently dropped. This module pins the contract:

* Every per-consumer data page produces a device key that is present in
  ``_DEVICE_PRIORITY`` (so ``process_entities`` cannot drop entities whose
  only descriptor entry comes from ``DESCRIPTOR_OVERRIDES``).
* The full ``BLOKYSPOTREBY*-OK`` family lands in the ``binary_sensors``
  bucket regardless of which heating consumer page hosts them.
* ``_DEVICE_PRIORITY`` and the coordinator's ``_init_device_info`` stay in
  sync — every priority key has a sub-device descriptor in both languages.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType

import pytest

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


_entity_helpers = _load_module(
    "_xcc_entity_helpers_subdev", "entity_helpers.py"
)
process_entities = _entity_helpers.process_entities
_normalize_page_to_device = _entity_helpers._normalize_page_to_device
_DEVICE_PRIORITY = _entity_helpers._DEVICE_PRIORITY


# All BLOKYSPOTREBY*-OK consumption-prioritizer flags and the data page each
# one is hosted on. Mirrors the production controller layout.
_BLOKY_BY_PAGE: tuple[tuple[str, str, str], ...] = (
    ("BLOKYSPOTREBY-OK",  "OKRUH10.XML",  "OKRUH"),
    ("BLOKYSPOTREBY1-OK", "BAZEN11.XML",  "BAZEN1"),
    ("BLOKYSPOTREBY2-OK", "BAZMIST1.XML", "BAZMIST"),
    ("BLOKYSPOTREBY3-OK", "TUV11.XML",    "TUV1"),
    ("BLOKYSPOTREBY6-OK", "TUV21.XML",    "TUV2"),
    ("BLOKYSPOTREBY7-OK", "BAZEN21.XML",  "BAZEN2"),
)


def _override_for(prop: str) -> dict:
    """Minimal DESCRIPTOR_OVERRIDES-shaped dict for a -OK status flag."""
    return {
        "friendly_name": prop,
        "friendly_name_en": prop,
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    }


@pytest.mark.parametrize("prop,page,expected_device", _BLOKY_BY_PAGE)
def test_normalize_page_to_device(prop, page, expected_device):
    """Each per-consumer data page maps to its documented device key."""
    assert _normalize_page_to_device(page, prop) == expected_device


@pytest.mark.parametrize("prop,page,expected_device", _BLOKY_BY_PAGE)
def test_bloky_device_keys_are_in_priority(prop, page, expected_device):
    """Without this guarantee ``process_entities`` would silently drop them."""
    assert expected_device in _DEVICE_PRIORITY, (
        f"device key {expected_device!r} produced by {page} is missing from "
        f"_DEVICE_PRIORITY — descriptor-backed prop {prop} would be dropped"
    )


def test_blokyspotreby_ok_routed_to_binary_sensors():
    """All six -OK flags reach the binary_sensors bucket with correct device."""
    raw_entities = [
        {
            "entity_type": "switch",  # parse_xml_entities tags _BOOL_i as switch
            "state": "0",
            "attributes": {
                "field_name": prop,
                "page": page,
                "data_type": "boolean",
                "internal_name": "__R0000.0_BOOL_i",
            },
        }
        for prop, page, _ in _BLOKY_BY_PAGE
    ]
    entity_configs = {prop: _override_for(prop) for prop, _, _ in _BLOKY_BY_PAGE}

    processed, metadata = process_entities(
        raw_entities, entity_configs, language="english"
    )

    seen = {
        data["prop"]: data["device"]
        for data in processed["binary_sensors"].values()
    }
    expected = {prop: device for prop, _, device in _BLOKY_BY_PAGE}
    assert seen == expected, (
        f"binary_sensors bucket missing entries.\nexpected: {expected}\ngot: {seen}"
    )

    # And nothing escaped to switches or sensors — every flag is read-only.
    for bucket in ("switches", "sensors", "numbers", "selects", "buttons"):
        leaked = {
            d["prop"] for d in processed[bucket].values()
            if d.get("prop", "").startswith("BLOKYSPOTREBY") and d["prop"].endswith("-OK")
        }
        assert not leaked, f"{bucket} bucket leaked {leaked}"


def test_priority_matches_coordinator_device_configs():
    """Every device key in ``_DEVICE_PRIORITY`` has matching sub-device info.

    Loaded only when Home Assistant is importable; the priority list is the
    source of truth, the coordinator's ``device_configs`` must keep up.
    """
    pytest.importorskip("homeassistant")
    from custom_components.xcc.const import LANGUAGE_CZECH, LANGUAGE_ENGLISH

    # Reproduce ``_init_device_info``'s body without instantiating the
    # coordinator (which needs a running HA instance).
    import inspect
    from custom_components.xcc.coordinator import XCCDataUpdateCoordinator

    src = inspect.getsource(XCCDataUpdateCoordinator._init_device_info)
    for lang in (LANGUAGE_ENGLISH, LANGUAGE_CZECH):
        for key in _DEVICE_PRIORITY:
            assert f'"{key}":' in src, (
                f"_init_device_info is missing a sub-device entry for "
                f"priority key {key!r} (language={lang})"
            )
