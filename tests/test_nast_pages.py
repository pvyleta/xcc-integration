"""Regression tests for the NAST (heat-pump settings) pages.

``nast.xml`` is the descriptor; it is not referenced from ``main.xml`` and is
registered via ``_check_additional_pages``. Unlike every other descriptor it
spans THREE data pages -- ``NAST1/2/3.XML``, one per ``<block data="NASTn">`` --
and those carry the live ``<INPUT ... VALUE=...>`` values. ``NAST.XML`` is NOT a
data page: the controller echoes the descriptor back for it, so fetching it
yields no values (this was the original bug -- the integration fetched only
``NAST.XML`` and every NAST setting came up empty).

This module pins the behaviour that makes ``OMEZENIVYKONUGLOBALNI`` (global
power restriction, defined in the NAST2 block) and its ~144 siblings populate:

* the descriptor yields it as a writable ``number`` in ``%``,
* every NAST data page routes to the single ``NAST`` device -- ``NAST2.XML`` /
  ``NAST3.XML`` must not normalize to ``NAST2`` / ``NAST3`` (absent from
  ``_DEVICE_PRIORITY``), which would silently drop their entities, and
* end to end, parsing ``NAST1/2/3.XML`` + the descriptor produces the number
  with its real value on the ``NAST`` device.

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

# NAST descriptor + its three data pages. Encodings mirror what the controller
# serves and how the fixtures are stored on disk: the descriptor is UTF-8, the
# data pages are windows-1250 (raw bytes, same as FVESOC1.XML).
_DESCRIPTOR = "nast.xml"
_DATA_PAGES = ("NAST1.XML", "NAST2.XML", "NAST3.XML")


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


# Order matters: xcc_client.py falls back to ``from descriptor_parser import …``
# when its relative import fails, so descriptor_parser must be importable under
# that bare name first.
_descriptor_parser = _load_module("descriptor_parser", "descriptor_parser.py")
_entity_helpers = _load_module("_xcc_entity_helpers_nast", "entity_helpers.py")
_xcc_client = _load_module("_xcc_client_nast", "xcc_client.py")

XCCDescriptorParser = _descriptor_parser.XCCDescriptorParser
process_entities = _entity_helpers.process_entities
_normalize_page_to_device = _entity_helpers._normalize_page_to_device
_DEVICE_PRIORITY = _entity_helpers._DEVICE_PRIORITY
parse_xml_entities = _xcc_client.parse_xml_entities


def _read_sample(name: str, encoding: str) -> str:
    path = os.path.join(_SAMPLE_DIR, name)
    if not os.path.exists(path):
        pytest.skip(f"sample file {name} not found")
    with open(path, "rb") as fh:
        return fh.read().decode(encoding)


def _parse_descriptor() -> dict:
    desc = _read_sample(_DESCRIPTOR, "utf-8")
    return XCCDescriptorParser(ignore_visibility=True).parse_descriptor_files(
        {_DESCRIPTOR: desc}
    )


def test_descriptor_yields_omezeni_as_writable_percent_number():
    configs = _parse_descriptor()
    assert "OMEZENIVYKONUGLOBALNI" in configs, "OMEZENIVYKONUGLOBALNI missing from descriptor"
    cfg = configs["OMEZENIVYKONUGLOBALNI"]
    assert cfg["entity_type"] == "number", "OMEZENIVYKONUGLOBALNI should be a number"
    assert cfg["writable"] is True, "OMEZENIVYKONUGLOBALNI should be writable"
    assert cfg["unit"] == "%", "OMEZENIVYKONUGLOBALNI unit should be %"


@pytest.mark.parametrize("page", ["NAST.XML", "NAST1.XML", "NAST2.XML", "NAST3.XML", "nast.xml"])
def test_every_nast_page_routes_to_nast_device(page):
    """NAST2/NAST3 must fold into NAST, not normalize to bare NAST2/NAST3
    (which are not in _DEVICE_PRIORITY and would be silently dropped)."""
    device = _normalize_page_to_device(page, "OMEZENIVYKONUGLOBALNI")
    assert device == "NAST", f"{page} routed to {device!r}, expected 'NAST'"
    assert device in _DEVICE_PRIORITY


def test_nast2_data_sample_carries_omezeni_value():
    """The committed NAST2.XML fixture holds the live INPUT value; the
    descriptor (nast.xml / NAST.XML echo) only declares the prop, no value."""
    data = _read_sample("NAST2.XML", "windows-1250")
    assert 'P="OMEZENIVYKONUGLOBALNI"' in data, "value missing from NAST2.XML sample"
    descriptor = _read_sample(_DESCRIPTOR, "utf-8")
    # Descriptor uses prop="…" (declaration), never P="…" (a live value).
    assert 'P="OMEZENIVYKONUGLOBALNI"' not in descriptor
    assert 'prop="OMEZENIVYKONUGLOBALNI"' in descriptor


def test_full_pipeline_populates_omezeni_on_nast_device():
    """End to end: descriptor + NAST1/2/3.XML -> OMEZENIVYKONUGLOBALNI is a
    number carrying its real value, assigned to the NAST device.

    This is the regression for the original bug: fetching only NAST.XML (the
    descriptor echo) produced no value, and even with the data pages fetched,
    NAST2.XML entities were dropped by device routing.
    """
    configs = _parse_descriptor()
    raw_entities: list[dict] = []
    for page in _DATA_PAGES:
        raw_entities.extend(parse_xml_entities(_read_sample(page, "windows-1250"), page))

    processed, _meta = process_entities(raw_entities, configs, language="english")

    numbers = processed["numbers"]
    omezeni = next(
        (d for d in numbers.values() if d.get("prop") == "OMEZENIVYKONUGLOBALNI"), None
    )
    assert omezeni is not None, "OMEZENIVYKONUGLOBALNI not produced as a number"
    assert omezeni["device"] == "NAST", f"expected NAST device, got {omezeni['device']!r}"
    assert float(omezeni["state"]) == 10.0, f"expected value 10, got {omezeni['state']!r}"

    # A NAST3-block prop must also survive (guards the NAST3 -> NAST routing).
    devices = {d["device"] for d in numbers.values() if d.get("device") == "NAST"}
    assert devices == {"NAST"}
    assert sum(1 for d in numbers.values() if d.get("device") == "NAST") > 40, (
        "far fewer NAST numbers survived than expected -- a data page is being dropped"
    )
