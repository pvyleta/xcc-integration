"""Runtime coverage of system-fault sensor availability and attributes."""
from unittest.mock import Mock
import pytest

pytest.importorskip("homeassistant")
from custom_components.xcc.binary_sensor import XCCSystemFaultBinarySensor
from custom_components.xcc.system_faults import FaultTracker


def test_fault_entity_retains_details_but_is_unavailable_during_outage():
    coordinator = Mock()
    coordinator.ip_address = "192.0.2.1"
    coordinator.last_update_success = True
    coordinator.system_faults = FaultTracker()
    tracker = coordinator.system_faults
    tracker.definitions = {"A0B": "Flow error HP1"}
    entity = XCCSystemFaultBinarySensor(coordinator)
    assert not entity.available
    assert entity.is_on is None
    tracker.update('<PAGE><INPUT P="A0B" VALUE="1"/></PAGE>')
    assert entity.available
    assert entity.is_on is True
    assert entity.extra_state_attributes["active_faults"] == {"A0B": "Flow error HP1"}
    coordinator.last_update_success = False
    assert not entity.available
    assert entity.is_on is None
    assert entity.extra_state_attributes["fault_count"] == 1
    coordinator.last_update_success = True
    tracker.available = False
    assert not entity.available
    tracker.update('<PAGE><INPUT P="A0B" VALUE="0"/></PAGE>')
    assert entity.available
    assert entity.is_on is False
