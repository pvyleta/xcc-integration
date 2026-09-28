"""Controller names are page-local presentation, never entity identity."""
import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tests.test_entity_naming import _entity_helpers as helpers, XCCDescriptorParser, parse_xml_entities

@pytest.mark.parametrize("index,name", [(0, "Ground floor"), (1, "Bedrooms"), (12, "Annexe")])
def test_page_name(index, name):
    prop = "TO-VSTUPNIT" if index == 0 else f"OKRUH{index}-VSTUPNIT"
    result = helpers.configured_name_config(prop, f"OKRUH1{index}.XML",
        {"friendly_name_en": "Temperature"}, {f"PAGE-OKRUH1{index}-PAGENAME": name})
    assert result["friendly_name_en"] == f"{name} — Temperature"

def test_raw_page_names_do_not_collide():
    raw = []
    for index, name in [(0, "Living"), (1, "Bedrooms")]:
        raw.extend(parse_xml_entities(f'<root><INPUT P="PAGENAME" VALUE="{name}"/><INPUT P="TO-VSTUPNIT" VALUE="20"/></root>', f"OKRUH1{index}.XML"))
    _, metadata = helpers.process_entities(raw, {"TO-VSTUPNIT": {"entity_type": "sensor", "friendly_name_en": "Temperature"}}, language="english")
    assert metadata["xcc_to_vstupnit"]["descriptor_config"]["friendly_name_en"] == "Living — Temperature"
    assert metadata["xcc_okruh1_vstupnit"]["descriptor_config"]["friendly_name_en"] == "Bedrooms — Temperature"

def test_block_reference_is_not_circuit_index():
    parser = XCCDescriptorParser(ignore_visibility=True)
    config = parser._parse_single_descriptor('<page><row prop="B4-CONFIG-NAZEV"><choice prop="H4"><option value="1" text_en="Enable"/></choice></row></page>', "nast.xml")["H4"]
    assert config["name_reference"] == "B4-CONFIG-NAZEV"
    result = helpers.configured_name_config("H4", "NAST1.XML", config, {"B4-CONFIG-NAZEV": "Bedrooms"})
    assert result["friendly_name_en"] == "Bedrooms — Power restriction enabled"
    assert helpers.configured_name_config("H4", "NAST1.XML", config, {})["friendly_name_en"].startswith("Block 4 —")

@pytest.mark.parametrize("name,cleared", [(None, False), ("My custom label", False), ("Old generated", True)])
def test_custom_registry_names_preserved(name, cleared):
    source = Path(__file__).parents[1] / "custom_components/xcc/entity.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_update_entity_registry_name")
    registry = SimpleNamespace(async_get=Mock(return_value=SimpleNamespace(name=name)), async_update_entity=Mock())
    ns = {"er": SimpleNamespace(async_get=lambda _: registry), "_LOGGER": logging.getLogger(__name__)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), ns)
    entity = SimpleNamespace(hass=None, entity_id="sensor.stable", _entity_data={"descriptor_config": {"configured_name": True, "legacy_generated_names": ["Old generated"]}})
    asyncio.run(ns[node.name](entity))
    assert registry.async_update_entity.called == cleared
