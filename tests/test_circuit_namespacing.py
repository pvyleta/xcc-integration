"""Per-circuit (okruh) entity namespacing.

Every heating circuit's data page carries the same unprefixed ``TO-*`` props and
shares one descriptor, so circuits above 0 are namespaced to ``OKRUH<n>-*``.
Circuit 0 must stay bare — its entity_ids/unique_ids are already in service.
"""

import importlib.util
import os
import random
import sys
from pathlib import Path
from types import ModuleType

import pytest

# custom_components/xcc/__init__.py imports Home Assistant, so load the HA-free
# helper modules straight from their file paths (same idiom as
# test_entity_naming.py).
_XCC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "custom_components", "xcc")
)


def _load_module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, os.path.join(_XCC_DIR, filename))
    assert spec and spec.loader, f"cannot load {filename}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# descriptor_parser first: xcc_client falls back to a top-level import of it.
_load_module("descriptor_parser", "descriptor_parser.py")
_entity_helpers = _load_module("_xcc_entity_helpers_ns", "entity_helpers.py")
_xcc_client = _load_module("_xcc_client_ns", "xcc_client.py")

_circuit_base_prop = _entity_helpers._circuit_base_prop
_normalize_page_to_device = _entity_helpers._normalize_page_to_device
circuit_of_prop = _entity_helpers.circuit_of_prop
lookup_with_normalized_fallback = _entity_helpers.lookup_with_normalized_fallback
process_entities = _entity_helpers.process_entities

circuit_from_okruh_page = _xcc_client.circuit_from_okruh_page
okruh_data_page = _xcc_client.okruh_data_page
ordered_unique_pages = _xcc_client.ordered_unique_pages
parse_xml_entities = _xcc_client.parse_xml_entities
qualify_circuit_prop = _xcc_client.qualify_circuit_prop
unqualify_circuit_prop = _xcc_client.unqualify_circuit_prop

SAMPLE_DIR = Path(__file__).parent / "sample_data"


class TestCircuitPageMapping:
    def test_page_to_circuit(self):
        assert circuit_from_okruh_page("OKRUH10.XML") == 0
        assert circuit_from_okruh_page("OKRUH12.XML") == 2
        assert circuit_from_okruh_page("okruh12.xml") == 2

    def test_non_circuit_pages(self):
        for page in ("TUV11.XML", "FVE4.XML", "STAVJED1.XML", "okruh.xml", ""):
            assert circuit_from_okruh_page(page) is None

    def test_circuit_to_page(self):
        assert okruh_data_page(0) == "OKRUH10.XML"
        assert okruh_data_page(2) == "OKRUH12.XML"


class TestPropNamespacing:
    def test_circuit_zero_left_bare(self):
        """Circuit 0 keeps existing entity_ids — no namespacing, ever."""
        assert qualify_circuit_prop("TO-KONSTANTA", 0) == "TO-KONSTANTA"
        assert qualify_circuit_prop("TO-KONSTANTA", None) == "TO-KONSTANTA"

    def test_secondary_circuit_namespaced(self):
        assert qualify_circuit_prop("TO-KONSTANTA", 2) == "OKRUH2-KONSTANTA"
        assert qualify_circuit_prop("TO-CONFIG-CHLAZENI", 2) == "OKRUH2-CONFIG-CHLAZENI"

    def test_system_wide_props_untouched(self):
        """Only TO-* is circuit-scoped; shared props must keep global names."""
        for prop in ("SVENKU", "BLOKYSPOTREBY-OK", "FVE-STATS", "SCHYBA"):
            assert qualify_circuit_prop(prop, 2) == prop

    def test_roundtrip(self):
        assert unqualify_circuit_prop("OKRUH2-KONSTANTA") == ("TO-KONSTANTA", 2)
        assert unqualify_circuit_prop("TO-KONSTANTA") == ("TO-KONSTANTA", None)
        assert unqualify_circuit_prop("SVENKU") == ("SVENKU", None)

    def test_helpers_agree(self):
        assert _circuit_base_prop("OKRUH2-KONSTANTA") == "TO-KONSTANTA"
        assert _circuit_base_prop("TO-KONSTANTA") is None
        assert circuit_of_prop("OKRUH2-KONSTANTA") == 2
        assert circuit_of_prop("TO-KONSTANTA") is None


class TestDeviceMapping:
    @pytest.mark.parametrize("page", ["OKRUH10.XML", "OKRUH11.XML", "OKRUH12.XML"])
    def test_all_circuits_fold_into_one_device(self, page):
        """Regression: OKRUH11/OKRUH12 normalized to keys absent from
        _DEVICE_PRIORITY, so their entities were silently dropped."""
        assert _normalize_page_to_device(page, "TO-KONSTANTA") == "OKRUH"

    def test_other_pages_unaffected(self):
        assert _normalize_page_to_device("TUV11.XML", "TUV-X") == "TUV1"
        assert _normalize_page_to_device("FVE4.XML", "FVE-X") == "FVE"


class TestDescriptorFallback:
    def test_namespaced_prop_inherits_base_descriptor(self):
        table = {"TO-KONSTANTA": {"entity_type": "number", "friendly_name": "Constant"}}
        assert lookup_with_normalized_fallback("OKRUH2-KONSTANTA", table) == table["TO-KONSTANTA"]

    def test_exact_match_still_wins(self):
        table = {
            "TO-KONSTANTA": {"entity_type": "number"},
            "OKRUH2-KONSTANTA": {"entity_type": "select"},
        }
        assert lookup_with_normalized_fallback("OKRUH2-KONSTANTA", table)["entity_type"] == "select"

    def test_missing_stays_missing(self):
        assert lookup_with_normalized_fallback("OKRUH2-NOPE", {}, "dflt") == "dflt"


@pytest.mark.skipif(
    not (SAMPLE_DIR / "OKRUH12.XML").exists(), reason="OKRUH12.XML sample missing"
)
class TestParseRealCircuitPage:
    def _props(self, filename, page_name):
        xml = (SAMPLE_DIR / filename).read_bytes().decode("windows-1250", errors="replace")
        entities = parse_xml_entities(xml, page_name)
        return {e["attributes"]["field_name"]: e["state"] for e in entities}

    def test_circuit_two_props_namespaced(self):
        props = self._props("OKRUH12.XML", "OKRUH12.XML")
        assert "OKRUH2-KONSTANTA" in props
        assert "TO-KONSTANTA" not in props

    def test_shared_props_not_namespaced(self):
        props = self._props("OKRUH12.XML", "OKRUH12.XML")
        assert "SVENKU" in props
        assert not any(p.startswith("OKRUH2-SVENKU") for p in props)

    def test_circuit_zero_unchanged(self):
        props = self._props("OKRUH10.XML", "OKRUH10.XML")
        assert "TO-KONSTANTA" in props
        assert not any(p.startswith("OKRUH0-") for p in props)

    def test_two_circuits_do_not_collide(self):
        """The whole point: both circuits' values survive a merged dict."""
        merged = {}
        merged.update(self._props("OKRUH10.XML", "OKRUH10.XML"))
        merged.update(self._props("OKRUH12.XML", "OKRUH12.XML"))
        assert merged["TO-KONSTANTA"] != merged["OKRUH2-KONSTANTA"]
        assert merged["OKRUH2-CONFIG-CHLAZENI"] == "1"


class TestPageOrder:
    """Fetch order decides which page owns a bare prop several okruh pages carry.

    Set order follows per-process string hashing, so before ordering was pinned
    every HA start re-rolled whether circuit 0 or circuit 2 owned e.g.
    ``BLOKYSPOTREBY-SET``.
    """

    _PAGES = [
        "STATUS.XML", "OKRUH12.XML", "TUV11.XML", "OKRUH10.XML",
        "OKRUH11.XML", "OKRUH110.XML", "FVE4.XML", "OKRUH12.XML",
    ]

    def test_independent_of_input_order(self):
        rng = random.Random(0)
        expected = ordered_unique_pages(self._PAGES)
        for _ in range(50):
            shuffled = self._PAGES[:]
            rng.shuffle(shuffled)
            assert ordered_unique_pages(shuffled) == expected

    def test_deduped_and_circuit_zero_first(self):
        ordered = ordered_unique_pages(self._PAGES)
        assert len(ordered) == len(set(self._PAGES))
        okruh = [p for p in ordered if circuit_from_okruh_page(p) is not None]
        assert okruh[0] == "OKRUH10.XML"

    @pytest.mark.skipif(
        not (SAMPLE_DIR / "OKRUH12.XML").exists(), reason="OKRUH12.XML sample missing"
    )
    @pytest.mark.parametrize(
        "pages",
        [["OKRUH10.XML", "OKRUH12.XML"], ["OKRUH12.XML", "OKRUH10.XML"]],
    )
    def test_shared_bare_props_owned_by_circuit_zero(self, pages):
        raw = []
        for page in ordered_unique_pages(pages):
            xml = (SAMPLE_DIR / page).read_bytes().decode("windows-1250", errors="replace")
            raw.extend(parse_xml_entities(xml, page))
        _, metadata = process_entities(raw, {}, "english")
        for entity_id in ("xcc_pagename", "xcc_blokyspotreby_set", "xcc_us_mon_ton1"):
            assert metadata[entity_id]["page"] == "OKRUH10.XML", entity_id
