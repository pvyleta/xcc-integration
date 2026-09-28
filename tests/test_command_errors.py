"""Exercise real service handlers offline with minimal HA stand-ins."""
import ast
import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest

class HomeAssistantError(Exception):
    pass

@pytest.mark.parametrize("filename,name,args", [
    ("number.py", "async_set_native_value", (20.5,)),
    ("select.py", "async_select_option", ("Enabled",)),
    ("switch.py", "_async_set_state", (True,)),
    ("button.py", "async_press", ()),
])
@pytest.mark.parametrize("outcome", [False, True, OSError("offline"), asyncio.CancelledError()])
def test_command_outcomes(filename, name, args, outcome):
    source = Path(__file__).parents[1] / "custom_components/xcc" / filename
    tree = ast.parse(source.read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    namespace = {"HomeAssistantError": HomeAssistantError, "_LOGGER": logging.getLogger(__name__)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), namespace)
    command = AsyncMock()
    if isinstance(outcome, BaseException):
        command.side_effect = outcome
    else:
        command.return_value = outcome
    coordinator = SimpleNamespace(async_set_entity_value=command, async_set_value=command, async_request_refresh=AsyncMock())
    entity = SimpleNamespace(name="Test", _prop="H4", _entity_data={"entity_id": "xcc_h4", "prop": "H4"},
        _option_to_value={"Enabled": "1"}, _button_value="1", coordinator=coordinator,
        _attr_is_on=False, async_write_ha_state=Mock())
    call = namespace[name](entity, *args)
    if outcome is True:
        asyncio.run(call)
    else:
        error = asyncio.CancelledError if isinstance(outcome, asyncio.CancelledError) else HomeAssistantError
        with pytest.raises(error):
            asyncio.run(call)
        coordinator.async_request_refresh.assert_not_called()
        entity.async_write_ha_state.assert_not_called()
        assert entity._attr_is_on is False
    command.assert_awaited_once()
