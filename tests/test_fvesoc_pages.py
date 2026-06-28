"""Regression tests for the FVE-SOC (battery SOC-curve) page.

``fvesoc.xml`` / ``FVESOC1.XML`` are not referenced from ``main.xml`` so they
are registered explicitly (``_check_additional_pages`` + the static page
lists). This module pins the behaviour that makes the page usable:

* the descriptor yields the 12 writable monthly ``FVE-SOCCONFIG-SOCCURVE*``
  number setpoints (unit ``%``), and
* their data page routes to the ``FVE`` device, so ``process_entities`` keeps
  them instead of silently dropping an unknown ``FVESOC`` device key.

Loaded with the flat ``_load_module`` pattern so the test also runs in the
no-Home-Assistant unit job.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from types import ModuleType

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_XCC_DIR = os.path.join(_REPO_ROOT, "custom_components", "xcc")
_SAMPLE_DIR = os.path.join(_REPO_ROOT, "tests", "sample_data")

_SOC_PROPS = [f"FVE-SOCCONFIG-SOCCURVE{i}" for i in range(12)]
_MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _load_module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_XCC_DIR, filename)
    )
    assert spec and spec.loader, f"cannot load {filename}"
    module = importlib.util.module_from_spec(spec)
    module._LOGGER = logging.getLogger("test")
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_descriptor_parser = _load_module("_xcc_descriptor_parser_fvesoc", "descriptor_parser.py")
_entity_helpers = _load_module("_xcc_entity_helpers_fvesoc", "entity_helpers.py")

XCCDescriptorParser = _descriptor_parser.XCCDescriptorParser
process_entities = _entity_helpers.process_entities
_normalize_page_to_device = _entity_helpers._normalize_page_to_device
_DEVICE_PRIORITY = _entity_helpers._DEVICE_PRIORITY


def _read_sample(name: str, encoding: str) -> str:
    path = os.path.join(_SAMPLE_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"sample file {name} not found")
    with open(path, "rb") as fh:
        return fh.read().decode(encoding)


def _parse_descriptor() -> dict:
    desc = _read_sample("fvesoc.xml", "utf-8")
    return XCCDescriptorParser(ignore_visibility=True).parse_descriptor_files(
        {"fvesoc.xml": desc}
    )


def test_descriptor_yields_twelve_writable_percent_numbers():
    configs = _parse_descriptor()
    for i, (prop, month) in enumerate(zip(_SOC_PROPS, _MONTHS_EN)):
        assert prop in configs, f"{prop} missing from descriptor"
        cfg = configs[prop]
        assert cfg["entity_type"] == "number", f"{prop} should be a number"
        assert cfg["writable"] is True, f"{prop} should be writable"
        assert cfg["unit"] == "%", f"{prop} unit should be %"
        assert cfg["friendly_name_en"] == month, (
            f"{prop} English name should be {month}, got {cfg['friendly_name_en']!r}"
        )


@pytest.mark.parametrize("page", ["FVESOC1.XML", "fvesoc.xml"])
def test_fvesoc_page_routes_to_fve_device(page):
    """A bare ``FVESOC`` key is not in _DEVICE_PRIORITY; it must fold into FVE."""
    device = _normalize_page_to_device(page, "FVE-SOCCONFIG-SOCCURVE0")
    assert device == "FVE"
    assert device in _DEVICE_PRIORITY


def test_soc_numbers_survive_process_entities_on_fve_device():
    configs = _parse_descriptor()
    raw_entities = [
        {
            "entity_type": "number",
            "state": "35",
            "attributes": {
                "field_name": prop,
                "page": "FVESOC1.XML",
                "value": "35",
                "data_type": "numeric",
                "internal_name": "__R69666_USINT_u",
            },
        }
        for prop in _SOC_PROPS
    ]

    processed, _meta = process_entities(raw_entities, configs, language="english")

    numbers = {
        data["prop"]: data["device"]
        for data in processed["numbers"].values()
        if data["prop"] in _SOC_PROPS
    }
    assert set(numbers) == set(_SOC_PROPS), (
        f"missing SOC numbers: {set(_SOC_PROPS) - set(numbers)}"
    )
    assert set(numbers.values()) == {"FVE"}, f"unexpected devices: {numbers}"

    # None leaked into another bucket.
    for bucket in ("sensors", "switches", "binary_sensors", "selects", "buttons"):
        leaked = {
            d["prop"] for d in processed[bucket].values()
            if d.get("prop", "") in _SOC_PROPS
        }
        assert not leaked, f"{bucket} bucket leaked {leaked}"


def test_data_sample_contains_all_soc_props():
    """The committed FVESOC1.XML fixture carries every SOC-curve value."""
    data = _read_sample("FVESOC1.XML", "windows-1250")
    for prop in _SOC_PROPS:
        assert f'P="{prop}"' in data, f"{prop} missing from FVESOC1.XML sample"
