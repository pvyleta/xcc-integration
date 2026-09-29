"""Read-only decoding of the controller's Current errors diagnostics block.

These flags are deliberately separate from generic entity/control discovery.
In particular, diagnostic acknowledgement/reset buttons must never become controls.
"""
from __future__ import annotations

from xml.etree import ElementTree as ET


def _root(xml: str) -> ET.Element:
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        raise ValueError("Unexpected diagnostic XML declaration")
    return ET.fromstring(xml)


def fault_definitions(xml: str, english: bool = True) -> dict[str, str]:
    """Read labels from current-error rows only, never history/configuration rows."""
    root = _root(xml)
    block = root.find("block")
    if block is None or block.get("data", "").upper() != "DIAG1":
        raise ValueError("Current errors block not found")
    result = {}
    for row in block.findall("row"):
        condition = row.get("visData", "")
        if not condition:
            continue
        parts = condition.split(";")
        if len(parts) != 3 or parts[0] != "1" or parts[2] != "1" or not parts[1]:
            raise ValueError("Unsupported diagnostic visibility condition")
        code = parts[1]
        result[code] = (row.get("text_en") if english else row.get("text")) or row.get("text") or code
    if not result:
        raise ValueError("No diagnostic fault definitions")
    return result


def fault_snapshot(xml: str, definitions: dict[str, str]) -> dict[str, bool]:
    """Decode P and packed PS flags (LSB first, including empty bit slots).

Require a complete snapshot. Missing/invalid data is not a cleared fault.
The bit order matches main.js's successive (value & 1), value >> 1.
"""
    root = _root(xml)
    values = {}
    for item in root.findall("INPUT"):
        prop, packed = item.get("P"), item.get("PS")
        codes = [prop] if prop else (packed or "").split(";")
        if not any(code in definitions for code in codes):
            continue
        value = int(item.get("VALUE", ""))
        if value < 0 or (prop and value not in (0, 1)):
            raise ValueError("Invalid diagnostic flag value")
        for bit, code in enumerate(codes):
            if code in definitions:
                decoded = bool(value) if prop else bool(value & (1 << bit))
                if code in values and values[code] != decoded:
                    raise ValueError("Conflicting diagnostic flag values")
                values[code] = decoded
    if not definitions or set(values) != set(definitions):
        raise ValueError("Incomplete diagnostic snapshot")
    return values


class FaultTracker:
    """Retain the last good snapshot across outages; emit transitions only."""

    def __init__(self) -> None:
        self.definitions: dict[str, str] = {}
        self.previous: dict[str, bool] = {}
        self.available = False

    @property
    def active(self) -> dict[str, str]:
        return {code: self.definitions.get(code, code)
                for code in sorted(self.previous) if self.previous[code]}

    def update(self, xml: str) -> list[tuple[str, str, bool]]:
        self.available = False
        current = fault_snapshot(xml, self.definitions)
        changes = [(code, self.definitions[code], active)
                   for code, active in sorted(current.items())
                   if active != self.previous.get(code, False)]
        self.previous = current
        self.available = True
        return changes
