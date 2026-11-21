"""Per-circuit (okruh) entity namespacing.

Every heating circuit's data page carries the same prop names and shares one
descriptor, so circuits above 0 are namespaced to ``OKRUH<n>-*``, except the
few props that sit on one system-wide register. Circuit 0 must stay bare — its
entity_ids/unique_ids are already in service.
"""

import importlib.util
import os
import random
import re
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.sample_io import read_sample_xml

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
_descriptor_parser = _load_module("descriptor_parser", "descriptor_parser.py")
_const = _load_module("_xcc_const_ns", "const.py")
_entity_helpers = _load_module("_xcc_entity_helpers_ns", "entity_helpers.py")
_xcc_client = _load_module("_xcc_client_ns", "xcc_client.py")

_circuit_base_props = _entity_helpers._circuit_base_props
_normalize_page_to_device = _entity_helpers._normalize_page_to_device
circuit_of_prop = _entity_helpers.circuit_of_prop
circuit_label = _entity_helpers.circuit_label
circuit_page_name = _entity_helpers.circuit_page_name
qualify_circuit_name = _entity_helpers.qualify_circuit_name
lookup_with_normalized_fallback = _entity_helpers.lookup_with_normalized_fallback
process_entities = _entity_helpers.process_entities

CIRCUIT_GLOBAL_PROPS = _xcc_client.CIRCUIT_GLOBAL_PROPS
XCCClient = _xcc_client.XCCClient
circuit_from_okruh_page = _xcc_client.circuit_from_okruh_page
okruh_data_page = _xcc_client.okruh_data_page
ordered_unique_pages = _xcc_client.ordered_unique_pages
parse_xml_entities = _xcc_client.parse_xml_entities
qualify_circuit_prop = _xcc_client.qualify_circuit_prop
unqualify_circuit_prop = _xcc_client.unqualify_circuit_prop

SAMPLE_DIR = Path(__file__).parent / "sample_data"
# Captured together from one controller (2026-11-21), so registers compare.
CIRCUIT_PAGES = ("OKRUH10.XML", "OKRUH11.XML", "OKRUH12.XML")
_REGISTER_RE = re.compile(r"^__R(\d+(?:\.\d+)?)")

needs_circuit_pages = pytest.mark.skipif(
    not all((SAMPLE_DIR / p).exists() for p in CIRCUIT_PAGES),
    reason="circuit page samples missing",
)


def _registers(page: str) -> dict[str, str]:
    """Map each prop on a sample page to its register (``NAME`` minus type)."""
    xml = read_sample_xml(SAMPLE_DIR / page)
    out = {}
    for prop, name in re.findall(r'<INPUT P="([^"]+)" NAME="([^"]*)"', xml):
        match = _REGISTER_RE.match(name)
        out[prop] = match.group(1) if match else name
    return out


def _props(page: str) -> dict[str, str]:
    entities = parse_xml_entities(read_sample_xml(SAMPLE_DIR / page), page)
    return {e["attributes"]["field_name"]: e["state"] for e in entities}


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
        for prop in ("TO-KONSTANTA", "BLOKYSPOTREBY-SET"):
            assert qualify_circuit_prop(prop, 0) == prop
            assert qualify_circuit_prop(prop, None) == prop

    def test_to_props_drop_their_prefix(self):
        """The v1.15.17 form; its unique_ids are in service."""
        assert qualify_circuit_prop("TO-KONSTANTA", 2) == "OKRUH2-KONSTANTA"
        assert qualify_circuit_prop("TO-CONFIG-CHLAZENI", 2) == "OKRUH2-CONFIG-CHLAZENI"

    def test_page_local_props_namespaced_whole(self):
        assert qualify_circuit_prop("BLOKYSPOTREBY-SET", 2) == "OKRUH2-BLOKYSPOTREBY-SET"
        assert qualify_circuit_prop("PAGENAME", 1) == "OKRUH1-PAGENAME"
        assert qualify_circuit_prop("US-MON-TON1", 2) == "OKRUH2-US-MON-TON1"

    def test_global_props_untouched(self):
        for prop in CIRCUIT_GLOBAL_PROPS:
            assert qualify_circuit_prop(prop, 2) == prop

    def test_roundtrip(self):
        assert unqualify_circuit_prop("OKRUH2-KONSTANTA") == (("TO-KONSTANTA", "KONSTANTA"), 2)
        assert unqualify_circuit_prop("OKRUH2-BLOKYSPOTREBY-OK") == (
            ("TO-BLOKYSPOTREBY-OK", "BLOKYSPOTREBY-OK"),
            2,
        )
        assert unqualify_circuit_prop("TO-KONSTANTA") == (("TO-KONSTANTA",), None)
        assert unqualify_circuit_prop("SVENKU") == (("SVENKU",), None)

    def test_helpers_agree(self):
        assert _circuit_base_props("OKRUH2-KONSTANTA") == ("TO-KONSTANTA", "KONSTANTA")
        assert _circuit_base_props("TO-KONSTANTA") == ()
        assert circuit_of_prop("OKRUH2-KONSTANTA") == 2
        assert circuit_of_prop("TO-KONSTANTA") is None
        for prop in ("OKRUH2-KONSTANTA", "OKRUH2-PAGENAME", "SVENKU"):
            assert _circuit_base_props(prop) == (
                unqualify_circuit_prop(prop)[0] if circuit_of_prop(prop) is not None else ()
            )


class TestDeviceMapping:
    @pytest.mark.parametrize("page", CIRCUIT_PAGES)
    def test_all_circuits_fold_into_one_device(self, page):
        """Regression: OKRUH11/OKRUH12 normalized to keys absent from
        _DEVICE_PRIORITY, so their entities were silently dropped."""
        assert _normalize_page_to_device(page, "TO-KONSTANTA") == "OKRUH"

    def test_other_pages_unaffected(self):
        assert _normalize_page_to_device("TUV11.XML", "TUV-X") == "TUV1"
        assert _normalize_page_to_device("FVE4.XML", "FVE-X") == "FVE"


class TestDescriptorFallback:
    def test_namespaced_to_prop_inherits_base_descriptor(self):
        table = {"TO-KONSTANTA": {"entity_type": "number", "friendly_name": "Constant"}}
        assert lookup_with_normalized_fallback("OKRUH2-KONSTANTA", table) == table["TO-KONSTANTA"]

    def test_namespaced_bare_prop_inherits_base_descriptor(self):
        table = {"BLOKYSPOTREBY-OK": {"entity_type": "binary_sensor"}}
        assert (
            lookup_with_normalized_fallback("OKRUH2-BLOKYSPOTREBY-OK", table)
            == table["BLOKYSPOTREBY-OK"]
        )

    def test_to_form_preferred(self):
        table = {"TO-X": {"entity_type": "number"}, "X": {"entity_type": "select"}}
        assert lookup_with_normalized_fallback("OKRUH2-X", table)["entity_type"] == "number"

    def test_exact_match_still_wins(self):
        table = {
            "TO-KONSTANTA": {"entity_type": "number"},
            "OKRUH2-KONSTANTA": {"entity_type": "select"},
        }
        assert lookup_with_normalized_fallback("OKRUH2-KONSTANTA", table)["entity_type"] == "select"

    def test_missing_stays_missing(self):
        assert lookup_with_normalized_fallback("OKRUH2-NOPE", {}, "dflt") == "dflt"


@needs_circuit_pages
class TestCircuitRegisters:
    """CIRCUIT_GLOBAL_PROPS is a static list; the capture keeps it honest."""

    def test_global_props_share_one_register(self):
        regs = [_registers(p) for p in CIRCUIT_PAGES]
        for prop in CIRCUIT_GLOBAL_PROPS:
            assert all(prop in r for r in regs), prop
            assert len({r[prop] for r in regs}) == 1, prop

    def test_every_other_prop_is_page_local(self):
        regs = [_registers(p) for p in CIRCUIT_PAGES]
        shared = set.intersection(*(set(r) for r in regs)) - CIRCUIT_GLOBAL_PROPS
        assert shared
        for prop in shared:
            values = [r[prop] for r in regs]
            assert len(set(values)) == len(values), (prop, values)

    @pytest.mark.parametrize("page", CIRCUIT_PAGES)
    def test_no_page_publishes_to_and_bare_pair(self, page):
        """Both would qualify to the same OKRUH<n>-X."""
        props = set(_registers(page))
        pairs = {p for p in props if p.startswith("TO-") and p[3:] in props}
        assert not pairs

    def test_no_native_prop_looks_namespaced(self):
        for page in sorted(SAMPLE_DIR.glob("*.XML")):
            for prop in _registers(page.name):
                assert circuit_of_prop(prop) is None, (page.name, prop)


@needs_circuit_pages
class TestParseRealCircuitPage:
    def test_circuit_two_props_namespaced(self):
        props = _props("OKRUH12.XML")
        assert "OKRUH2-KONSTANTA" in props
        assert "OKRUH2-BLOKYSPOTREBY-SET" in props
        assert "TO-KONSTANTA" not in props
        assert "BLOKYSPOTREBY-SET" not in props

    def test_global_props_not_namespaced(self):
        props = _props("OKRUH12.XML")
        assert "SVENKU" in props
        assert not any(p.startswith("OKRUH2-SVENKU") for p in props)

    def test_circuit_zero_unchanged(self):
        props = _props("OKRUH10.XML")
        assert "TO-KONSTANTA" in props
        assert "BLOKYSPOTREBY-SET" in props
        assert not any(p.startswith("OKRUH0-") for p in props)

    def test_circuits_do_not_collide(self):
        """The whole point: every circuit's values survive a merged dict."""
        merged = {}
        for page in CIRCUIT_PAGES:
            merged.update(_props(page))
        assert merged["PAGENAME"] != merged["OKRUH2-PAGENAME"]
        assert merged["OKRUH1-PAGENAME"] not in (merged["PAGENAME"], merged["OKRUH2-PAGENAME"])
        assert merged["TO-KONSTANTA"] != merged["OKRUH2-KONSTANTA"]
        assert merged["OKRUH2-CONFIG-CHLAZENI"] == "1"


def _circuit_processed():
    descriptors = {
        name: read_sample_xml(SAMPLE_DIR / name)
        for name in ("okruh.xml", "tuv1.xml", "fve.xml", "spot.xml", "biv.xml", "stavjed.xml")
        if (SAMPLE_DIR / name).exists()
    }
    configs = _descriptor_parser.XCCDescriptorParser().parse_descriptor_files(descriptors)
    configs = {**configs, **_const.DESCRIPTOR_OVERRIDES}
    raw = []
    for page in ordered_unique_pages(list(CIRCUIT_PAGES)):
        raw.extend(parse_xml_entities(read_sample_xml(SAMPLE_DIR / page), page))
    return process_entities(raw, configs, "english")


def _circuit_entities():
    return _circuit_processed()[1]


@needs_circuit_pages
class TestNamespacedEntityTypes:
    """A namespaced prop must become the same kind of entity as its circuit-0
    twin; in particular a read-only pin must not fall back to the writable
    ``_BOOL_i`` switch default."""

    def test_twin_type_and_device(self):
        metadata = _circuit_entities()
        by_prop = {m["prop"]: m for m in metadata.values()}
        checked = 0
        for prop, meta in by_prop.items():
            bases = _circuit_base_props(prop)
            if not bases:
                continue
            twin = next((by_prop[b] for b in bases if b in by_prop), None)
            assert twin is not None, prop
            assert (meta["type"], meta["device"]) == (twin["type"], twin["device"]), prop
            checked += 1
        assert checked

    def test_read_only_pins_reach_secondary_circuits(self):
        metadata = _circuit_entities()
        for n in (1, 2):
            for suffix in ("blokyspotreby_ok", "blokyspotreby_utlum"):
                assert metadata[f"xcc_okruh{n}_{suffix}"]["type"] == "binary_sensor"

    def test_every_page_local_prop_reaches_ha(self):
        metadata = _circuit_entities()
        for page in CIRCUIT_PAGES[1:]:
            circuit = circuit_from_okruh_page(page)
            owned = {m["prop"] for m in metadata.values() if m["page"] == page}
            for prop in _props(page):
                if prop in CIRCUIT_GLOBAL_PROPS:
                    assert prop not in owned
                else:
                    assert circuit_of_prop(prop) == circuit and prop in owned, prop


class TestCircuitNames:
    def test_label_prefers_page_name(self):
        assert circuit_label(2, "Chlazení") == "Chlazení"

    def test_label_default_matches_controller_numbering(self):
        """main.xml lists okruh.xml?page=n as entry n+1, default name "Okruh n+1"."""
        assert circuit_label(2) == "Okruh 3"
        assert circuit_label(2, "  ") == "Okruh 3"

    def test_qualify_secondary_circuit_only(self):
        assert qualify_circuit_name("Constant", "OKRUH2-KONSTANTA", "Chlazení") == "Chlazení Constant"
        assert qualify_circuit_name("Constant", "TO-KONSTANTA", "Chlazení") == "Constant"
        assert qualify_circuit_name("Outside temperature", "SVENKU") == "Outside temperature"

    def test_raw_prop_name_falls_back_to_bare_prop(self):
        assert qualify_circuit_name("OKRUH2-MZ", "OKRUH2-MZ") == "Okruh 3 MZ"
        assert qualify_circuit_name("", "OKRUH2-US-MON-TON1", "Chlazení") == "Chlazení US-MON-TON1"

    def test_page_name_from_metadata(self):
        entities = {"xcc_okruh2_pagename": {"data": {"state": "Chlazení"}}}
        assert circuit_page_name(entities, "OKRUH2-KONSTANTA") == "Chlazení"
        assert circuit_page_name(entities, "OKRUH1-KONSTANTA") is None
        assert circuit_page_name(entities, "TO-KONSTANTA") is None


@needs_circuit_pages
class TestCircuitNamesFromCapture:
    def test_twin_descriptor_and_qualified_name(self):
        processed, metadata = _circuit_processed()
        names = {
            eid: data["name"]
            for bucket in ("sensors", "binary_sensors", "switches", "numbers", "selects")
            for eid, data in processed[bucket].items()
        }
        labels = {1: "Podlahovka", 2: "Chlazení"}
        by_prop = {m["prop"]: m for m in metadata.values()}
        checked = 0
        for meta in metadata.values():
            circuit = circuit_of_prop(meta["prop"])
            if circuit is None:
                continue
            twin = next(by_prop[b] for b in _circuit_base_props(meta["prop"]) if b in by_prop)
            assert meta["descriptor_config"] == twin["descriptor_config"], meta["prop"]
            twin_name = names[twin["entity_id"]]
            if twin_name == twin["prop"]:
                # Undescribed: named by the prop, minus the namespace (and TO-).
                twin_name = meta["prop"].split("-", 1)[1]
            assert names[meta["entity_id"]] == f"{labels[circuit]} {twin_name}", meta["prop"]
            checked += 1
        assert checked


@needs_circuit_pages
class TestCircuitWriteRouting:
    @staticmethod
    def _client():
        client = XCCClient("192.168.1.100", "xcc", "xcc")
        client.fetch_page = AsyncMock(side_effect=lambda page: read_sample_xml(SAMPLE_DIR / page))
        response = MagicMock(status=200)
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=False)
        client.session = MagicMock()
        client.session.post = MagicMock(return_value=cm)
        return client

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("prop", "base"),
        [
            ("OKRUH2-KONSTANTA", "TO-KONSTANTA"),
            ("OKRUH2-BLOKYSPOTREBY-SET", "BLOKYSPOTREBY-SET"),
            ("OKRUH1-US-MON-TON1", "US-MON-TON1"),
        ],
    )
    async def test_posts_circuit_register_to_circuit_page(self, prop, base):
        page = okruh_data_page(circuit_of_prop(prop))
        client = self._client()

        assert await client.set_value(prop, "1") is True

        client.fetch_page.assert_awaited_once_with(page)
        (url,), kwargs = client.session.post.call_args
        assert url.endswith(f"/{page}")
        xml = read_sample_xml(SAMPLE_DIR / page)
        name = re.search(rf'<INPUT P="{re.escape(base)}" NAME="([^"]+)"', xml).group(1)
        assert kwargs["data"] == {name: "1"}


class TestPageOrder:
    """Fetch order decides which page owns a bare prop several okruh pages carry.

    Set order follows per-process string hashing, so before ordering was pinned
    every HA start re-rolled whether circuit 0 or circuit 2 owned e.g.
    ``BLOKYSPOTREBY-SET``. Namespacing removed that case; the global props
    still dedupe in this order.
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

    @needs_circuit_pages
    @pytest.mark.parametrize(
        "pages",
        [["OKRUH10.XML", "OKRUH12.XML"], ["OKRUH12.XML", "OKRUH10.XML"]],
    )
    def test_bare_props_owned_by_circuit_zero(self, pages):
        raw = []
        for page in ordered_unique_pages(pages):
            raw.extend(parse_xml_entities(read_sample_xml(SAMPLE_DIR / page), page))
        _, metadata = process_entities(raw, {}, "english")
        for entity_id in ("xcc_pagename", "xcc_blokyspotreby_set", "xcc_us_mon_ton1", "xcc_svenku"):
            assert metadata[entity_id]["page"] == "OKRUH10.XML", entity_id
        assert metadata["xcc_okruh2_pagename"]["page"] == "OKRUH12.XML"
