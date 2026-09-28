"""Integration loggers must inherit Home Assistant's configured log level."""
import ast
from pathlib import Path


def test_sensor_logger_does_not_force_debug():
    source = Path(__file__).parents[1] / "custom_components/xcc/sensor.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            function = node.value.func
            assert not (isinstance(function, ast.Attribute)
                        and function.attr in ("setLevel", "basicConfig"))
