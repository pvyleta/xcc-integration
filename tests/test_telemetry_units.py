"""Regression coverage for all 46 unintentionally stripped telemetry units."""
from pathlib import Path
import pytest
from tests.test_real_descriptor_parser import _load_descriptor_parser
from tests.test_audit_sensor_metadata import build_description

TEMPERATURES = [f"TCSTAV{i}-{suffix}" for i in range(8)
                for suffix in ("TCJ", "TS", "TD", "TE", "TL")] + ["TTUVDRUHA"]
RUNTIMES = ["BIVALENCEMOTOHODINY", "TUVEXTERNIOHREVMOTOHODINY"] + [
    f"BIVALENCEMOTOHODINYSTUPNE{i}" for i in (1, 2, 3)]


@pytest.mark.parametrize("prop,unit", [(p, "°C") for p in TEMPERATURES] + [(p, "h") for p in RUNTIMES])
def test_recorded_descriptor_to_runtime_units(prop, unit):
    parser = _load_descriptor_parser().XCCDescriptorParser(ignore_visibility=True)
    sample = Path(__file__).parent / "sample_data"
    configs = parser.parse_descriptor_files({name: (sample / name).read_text(encoding="utf-8")
        for name in ("stavjed.xml", "tuv1.xml", "biv.xml")})
    assert configs[prop]["unit"] == unit
    result = build_description(prop, configs[prop]["unit"], "17", "numeric", nested=True)
    assert result.native_unit_of_measurement == ("celsius" if unit == "°C" else "hours")
    if unit == "°C":
        assert result.device_class == "temperature"
    assert result.state_class == "measurement"


@pytest.mark.parametrize("prop", ["TOPNEOKRUHYADAPTACEOUT", "TOPNEOKRUHYOUT-POCASIVLIV"])
def test_influences_stay_unitless(prop):
    parser = _load_descriptor_parser().XCCDescriptorParser()
    config = parser._parse_single_descriptor(
        f'<page><row text_en="Room temperature influence"><number config="readonly" prop="{prop}"/></row></page>',
        "okruh.xml")
    assert config[prop]["unit"] == ""


def test_explicit_unit_wins_and_unknown_channels_are_not_guessed():
    parser = _load_descriptor_parser().XCCDescriptorParser()
    configs = parser._parse_single_descriptor('''<page><row>
      <number config="readonly" prop="TCSTAV0-TCJ" unit="°F"/>
      <number config="readonly" prop="TCSTAV0-UNKNOWN" unit=""/>
      <number prop="BIVALENCEMOTOHODINY" unit=""/>
    </row></page>''', "test.xml")
    assert configs["TCSTAV0-TCJ"]["unit"] == "°F"
    assert configs["TCSTAV0-UNKNOWN"]["unit"] == ""
    assert configs["BIVALENCEMOTOHODINY"]["unit"] == ""
