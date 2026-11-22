"""Sub-devices link to the controller by registry id where the core supports it.

HA 2026.8 added ``via_device_id`` and deprecated the ``(domain, identifier)``
``via_device`` tuple (removed in 2027.8); cores before 2026.8 reject
``via_device_id``. The version gate is pinned against the installed core's
``async_get_or_create`` signature so it can't drift from what the core accepts.
"""

import inspect
from types import SimpleNamespace

import pytest

pytest.importorskip("homeassistant")

from homeassistant.helpers import device_registry as dr  # noqa: E402

from custom_components.xcc import coordinator as coordinator_module  # noqa: E402

_link = coordinator_module.XCCDataUpdateCoordinator._parent_device_link


def test_version_gate_matches_core_signature():
    params = inspect.signature(dr.DeviceRegistry.async_get_or_create).parameters
    assert coordinator_module._HAS_VIA_DEVICE_ID == ("via_device_id" in params)


def test_link_uses_registry_id_when_supported(monkeypatch):
    monkeypatch.setattr(coordinator_module, "_HAS_VIA_DEVICE_ID", True)
    coord = SimpleNamespace(main_device_id="abc123", ip_address="192.168.1.100")
    assert _link(coord) == {"via_device_id": "abc123"}


def test_link_falls_back_to_tuple_on_old_core(monkeypatch):
    monkeypatch.setattr(coordinator_module, "_HAS_VIA_DEVICE_ID", False)
    coord = SimpleNamespace(main_device_id="abc123", ip_address="192.168.1.100")
    assert _link(coord) == {"via_device": ("xcc", "192.168.1.100")}


def test_link_falls_back_to_tuple_before_main_device_registered(monkeypatch):
    monkeypatch.setattr(coordinator_module, "_HAS_VIA_DEVICE_ID", True)
    coord = SimpleNamespace(main_device_id=None, ip_address="192.168.1.100")
    assert _link(coord) == {"via_device": ("xcc", "192.168.1.100")}
