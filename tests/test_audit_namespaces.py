"""Regression tests for schedule and prioritizer collisions."""
import ast
from pathlib import Path
import pytest
from tests.test_entity_naming import process_entities
from tests.test_circuit_namespacing import (
    _xcc_client, _entity_helpers, parse_xml_entities,
    qualify_circuit_prop, unqualify_circuit_prop,
)


@pytest.mark.parametrize("prop", ["US-MON-TON1", "CS-SUN-TOFF2", "CT-FRI-TON2",
                                 "PAGENAME", "ICONNO"])
def test_page_local_properties_are_unique(prop):
    pages = ["OKRUH10.XML", "OKRUH11.XML", "TUV11.XML", "TUV21.XML"]
    keys = [_xcc_client.qualify_page_prop(prop, page) for page in pages]
    assert len(set(keys)) == 4
    for key in keys:
        assert _entity_helpers.lookup_with_normalized_fallback(key, {prop: 42}) == 42
    assert _xcc_client.qualify_page_prop("SVENKU", pages[0]) == "SVENKU"


@pytest.mark.parametrize("status", ["BOOST", "ECO", "OFF", "IGNORED"])
def test_prioritizer_status_is_circuit_local(status):
    prop = f"MAIN-PRIORIZATORSPOTREBY-PRITOPNEOKRUHY-SPOTSTATS-{status}"
    assert qualify_circuit_prop(prop, 0) == prop
    key = qualify_circuit_prop(prop, 1)
    assert key != prop
    assert unqualify_circuit_prop(key) == (prop, 1)
    assert _entity_helpers._circuit_base_prop(key) == prop


def test_four_schedules_survive_processing_with_correct_sources():
    raw = []
    pages = ["OKRUH10.XML", "OKRUH11.XML", "TUV11.XML", "TUV21.XML"]
    for i, page in enumerate(pages):
        xml = f'<ROOT><INPUT P="US-MON-TON1" NAME="__R{100+i}_TIME_Thh:mm" VALUE="0{i}:00"/></ROOT>'
        raw.extend(parse_xml_entities(xml, page))
    data, metadata = process_entities(raw, {}, "english")
    assert len(data["sensors"]) == 4
    assert {v["page"] for v in data["sensors"].values()} == set(pages)
    assert {v["state"] for v in data["sensors"].values()} == {"00:00", "01:00", "02:00", "03:00"}
    assert all(not v["descriptor_config"]["writable"] for v in metadata.values())


@pytest.mark.parametrize("prop", ["MZ", "WEB-VOLBYVLIVUPROSTORU",
    "WEB-BLOKREZIM-UTLUMBIVALENCE", "WEB-BLOKREZIM-PROSTORADAPTIVNI",
    "WEB-VLIVPROSTORU-ADAPTIVNIMAXT", "WEB-VLIVPROSTORU-ADAPTIVNIMINT",
    "OKRUHDOCASNEBEZCIDLA"])
def test_additional_local_registers_preserve_page_and_descriptor(prop):
    key = qualify_circuit_prop(prop, 1)
    assert key == f"OKRUH1-{prop}"
    assert unqualify_circuit_prop(key) == (prop, 1)
    config = {"entity_type": "switch", "writable": True}
    assert _entity_helpers.lookup_with_normalized_fallback(key, {prop: config}) == config
    assert qualify_circuit_prop(prop, 0) == prop


@pytest.mark.parametrize("prop", ["TOPNEOKRUHYADAPTACEOUT", "TOPNEOKRUHYOUT-POCASIVLIV"])
def test_influences_are_circuit_local(prop):
    key = qualify_circuit_prop(prop, 1)
    assert key == f"OKRUH1-{prop}"
    assert unqualify_circuit_prop(key) == (prop, 1)
    assert _entity_helpers._circuit_base_prop(key) == prop


def test_page_snapshots_cannot_be_written_even_with_writable_descriptor():
    source = Path(__file__).parents[1] / "custom_components/xcc/coordinator.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "XCCDataUpdateCoordinator")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "is_writable")
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(source), "exec"), namespace)
    # No self attributes are needed: the namespace guard must run first.
    assert namespace["is_writable"](object(), "PAGE-TUV11-US-MON-TON1") is False
