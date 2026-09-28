"""Execute the real description builder without importing the HA runtime.

HA enum/description types are minimal stand-ins; this tests integration logic,
not HA platform setup or registry behaviour.
"""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest


def build_description(prop, unit, value, data_type, nested=False):
    source = Path(__file__).parents[1] / "custom_components/xcc/sensor.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    namespace = {"PERCENTAGE": "%", "_LOGGER": logging.getLogger(__name__),
                 "SensorEntityDescription": SimpleNamespace}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            name = node.value.id
            if name.startswith("UnitOf") or name in ("SensorDeviceClass", "SensorStateClass"):
                namespace.setdefault(name, SimpleNamespace())
                setattr(namespace[name], node.attr, node.attr.lower())
    selected = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in ("UNIT_MAPPING", "DEVICE_CLASS_MAPPING", "STATE_CLASS_MAPPING")
            for t in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.ClassDef) and node.name == "XCCSensor":
            selected.extend(n for n in node.body if isinstance(n, ast.FunctionDef)
                            and n.name == "_create_entity_description")
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, str(source), "exec"), namespace)
    coordinator = SimpleNamespace(get_entity_config=lambda _: {"unit": unit},
                                  _get_friendly_name=lambda config, p: p)
    data = {
        "entity_id": "xcc_" + prop.lower(), "prop": prop, "state": value,
        "attributes": {"data_type": data_type},
    }
    if nested:
        data = {"entity_id": data["entity_id"], "prop": prop,
                "data": {"state": value, "attributes": data["attributes"]}}
    return namespace["_create_entity_description"](None, coordinator, data)


def test_registry_metadata_shape_keeps_numeric_protocol_type():
    result = build_description("TOPNEOKRUHYADAPTACEOUT", "", "-9.8", "numeric", nested=True)
    assert result.state_class == "measurement"


def test_unitless_temperature_named_field_has_no_invalid_device_class():
    result = build_description("MZOSTATS-ZONA1-TEPLOTA", "", "20", "numeric")
    assert result.device_class is None


@pytest.mark.parametrize("prop", ["SVYKON", "TCSTAV0-VYKON", "FVE-SOC"])
def test_generic_percentages_are_not_power_factor(prop):
    description = build_description(prop, "%", "10", "numeric")
    assert description.device_class is None
    assert description.state_class == "measurement"


def test_humidity_percentage_class():
    assert build_description("POCASI-PREDPOVEDI0-VLHKOST", "%", "70", "numeric").device_class == "humidity"


def test_numeric_unitless_influence_supports_statistics():
    result = build_description("OKRUH1-TOPNEOKRUHYADAPTACEOUT", "", "0", "numeric")
    assert result.native_unit_of_measurement is None
    assert result.device_class is None
    assert result.state_class == "measurement"


@pytest.mark.parametrize("kind,value", [("boolean", "1"), ("time", "08:00"),
                                       ("datetime", "01.01.2026 08:00"), ("enum", "1")])
def test_non_numeric_types_never_inherit_numeric_metadata(kind, value):
    result = build_description("EXAMPLE", "W", value, kind)
    assert result.native_unit_of_measurement is None
    assert result.device_class is None
    assert result.state_class is None
