"""Unit leakage regressions using compact controller descriptor examples."""
import pytest
from tests.test_real_descriptor_parser import _load_descriptor_parser
from tests.test_circuit_namespacing import _entity_helpers


@pytest.mark.parametrize("readonly", ["", 'config="readonly"'])
def test_explicit_empty_unit_is_respected(readonly):
    parser = _load_descriptor_parser().XCCDescriptorParser()
    xml = f'<page><block><row text_en="Power"><number prop="PRIORITY" unit="" {readonly}/></row></block></page>'
    config = parser._parse_single_descriptor(xml, "test.xml")["PRIORITY"]
    assert config["unit"] == ""
    assert not config.get("device_class")


def test_multi_field_row_does_not_leak_units():
    parser = _load_descriptor_parser().XCCDescriptorParser()
    xml = '''<page><block><row text_en="PV power">
      <number prop="PRIORITY" unit=""/>
      <number prop="SURPLUS" unit="W"/>
      <number prop="UPLIFT"/>
    </row><row text_en="External heating">
      <label prop="ACTIVE"><option value="0" text_en="Inactive"/><option value="1" text_en="Active"/></label>
      <number prop="HOURS" unit="h"/><label text_en="Runhours"/>
    </row></block></page>'''
    config = parser._parse_single_descriptor(xml, "test.xml")
    assert config["SURPLUS"]["unit"] == "W"
    for prop in ("PRIORITY", "UPLIFT", "ACTIVE"):
        assert not config[prop].get("unit")


def test_adaptive_band_uses_each_circuits_live_selector():
    data = {"selects": {
        "xcc_to_adaptace_rozptylpct": {"state": "0"},
        "xcc_okruh1_adaptace_rozptylpct": {"state": "1"},
    }}
    unit = _entity_helpers.adaptive_band_unit
    assert unit("TO-ADAPTACE-ROZPTYLEKV", data) == "°C"
    assert unit("OKRUH1-ADAPTACE-ROZPTYLEKV", data) == "%"
    assert unit("OKRUH2-ADAPTACE-ROZPTYLEKV", data) is None
    data["selects"]["xcc_okruh1_adaptace_rozptylpct"]["state"] = "0"
    assert unit("OKRUH1-ADAPTACE-ROZPTYLEKV", data) == "°C"
    data["selects"]["xcc_to_adaptace_rozptylpct"]["state"] = "unknown"
    assert unit("TO-ADAPTACE-ROZPTYLEKV", data) is None


def test_unit_does_not_follow_previous_row_used_for_friendly_name():
    parser = _load_descriptor_parser().XCCDescriptorParser()
    xml = '''<page><block><row text_en="PV power"><label text_en="W"/></row>
      <row prop="PAGENAME"><number prop="PRIORITY" unit=""/>
      <number prop="SURPLUS" unit="W"/><number prop="TO-FVEPRETOPENI-T"/></row>
    </block></page>'''
    config = parser._parse_single_descriptor(xml, "test.xml")
    assert not config["TO-FVEPRETOPENI-T"].get("unit")
