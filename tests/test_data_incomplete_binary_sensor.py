"""Runtime tests for the data-incomplete diagnostic binary sensor.

HA-gated (the entity module imports Home Assistant); runs in CI's Home Assistant
job. Uses a ``Mock(spec=...)`` coordinator like the other entity tests so the
entity's HA wiring — is_on, the always-available override, attributes, identity —
is exercised without a full coordinator/hass setup.
"""

import pytest

pytest.importorskip("homeassistant")

from unittest.mock import Mock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from custom_components.xcc.binary_sensor import XCCDataIncompleteBinarySensor
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator


def _coordinator(**overrides):
    c = Mock(spec=XCCDataUpdateCoordinator)
    c.ip_address = "192.168.1.100"
    c.missing_page_alert_polls = 5
    c.consecutive_incomplete_polls = 0
    c.consecutive_failed_polls = 0
    c.last_missing_pages = []
    c.last_poll_failed = False
    c.expected_page_count = 21
    c.gathered_page_count = 21
    c.data_gathering_degraded = False
    for key, value in overrides.items():
        setattr(c, key, value)
    return c


def test_identity_and_default_off():
    ent = XCCDataIncompleteBinarySensor(_coordinator())
    assert ent.available is True
    assert ent.is_on is False
    assert ent.entity_id == "binary_sensor.xcc_data_incomplete"
    assert ent.unique_id == "192.168.1.100_xcc_data_incomplete"
    assert ent.device_class == BinarySensorDeviceClass.PROBLEM
    assert ent.entity_category == EntityCategory.DIAGNOSTIC
    assert ent.device_info == {"identifiers": {("xcc", "192.168.1.100")}}


def test_on_and_attributes_when_pages_missing():
    ent = XCCDataIncompleteBinarySensor(
        _coordinator(
            data_gathering_degraded=True,
            consecutive_incomplete_polls=5,
            last_missing_pages=["FVESOC1.XML"],
            gathered_page_count=20,
        )
    )
    assert ent.is_on is True
    attrs = ent.extra_state_attributes
    assert attrs["missing_pages"] == ["FVESOC1.XML"]
    assert attrs["consecutive_incomplete_polls"] == 5
    assert attrs["alert_after_polls"] == 5
    assert attrs["pages_gathered"] == 20
    assert attrs["pages_expected"] == 21
    assert attrs["last_poll_failed"] is False


def test_stays_available_through_total_failure():
    ent = XCCDataIncompleteBinarySensor(
        _coordinator(
            data_gathering_degraded=True,
            consecutive_failed_polls=5,
            last_poll_failed=True,
        )
    )
    # Must keep reporting through the very outage it alarms on.
    assert ent.available is True
    assert ent.is_on is True
    assert ent.extra_state_attributes["last_poll_failed"] is True
