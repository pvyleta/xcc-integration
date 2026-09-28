"""Regression coverage for indicator/control and descriptor fallback audit."""
from tests.test_entity_naming import _load_module, process_entities

const = _load_module("_xcc_audit_const", "const.py")


def test_verified_statuses_are_read_only():
    for prop in ("TCRVYSTUP", "BIVALENCE", "ALTERNATIVNIREZIMAKTIVNI",
                 "TO-NATOP-STAT-RUN", "TUVEXTERNIVYSTUP"):
        config = const.DESCRIPTOR_OVERRIDES[prop]
        assert config["entity_type"] == "binary_sensor"
        assert config["writable"] is False
        assert config["unit"] == ""


def test_secondary_circuit_inherits_readonly_descriptor_and_name():
    prop = "OKRUH1-NATOP-STAT-RUN"
    raw = [{"entity_type": "switch", "state": "1", "attributes": {
        "field_name": prop, "page": "OKRUH11.XML", "value": "1"}}]
    data, metadata = process_entities(raw, const.DESCRIPTOR_OVERRIDES, "english")
    key = "xcc_okruh1_natop_stat_run"
    assert key in data["binary_sensors"]
    assert data["binary_sensors"][key]["name"].endswith("Slow heating up active")
    assert metadata[key]["descriptor_config"]["writable"] is False


def test_readonly_sensor_fallback_is_not_replaced_by_raw_switch():
    raw = [{"entity_type": "switch", "state": "1", "attributes": {
        "field_name": "OKRUH1-EXAMPLE", "page": "OKRUH11.XML"}}]
    data, _ = process_entities(raw, {"TO-EXAMPLE": {
        "entity_type": "sensor", "writable": False,
        "friendly_name_en": "Example diagnostic"}}, "english")
    assert data["sensors"]["xcc_okruh1_example"]["name"].endswith("Example diagnostic")
