"""Binary sensor platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator
from .entity import XCCEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC binary sensor entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get all binary sensor entities from coordinator
    sensors = coordinator.get_entities_by_type("binary_sensor")

    entities = []
    for entity_id, entity_data in sensors.items():
        try:
            entity = XCCBinarySensor(coordinator, entity_data)
            entities.append(entity)
            _LOGGER.debug("Created binary sensor entity: %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error creating binary sensor entity %s: %s", entity_id, err)

    # Always-present diagnostic: fires when the controller keeps dropping data
    # pages (or the update keeps failing) for several consecutive polls, so a
    # stuck/partial integration surfaces instead of silently going stale. Wrapped
    # like the loop above so a construction error can't abort the whole platform.
    try:
        entities.append(XCCDataIncompleteBinarySensor(coordinator))
    except Exception as err:
        _LOGGER.error("Error creating XCC data-incomplete diagnostic sensor: %s", err)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d XCC binary sensor entities", len(entities))


class XCCBinarySensor(XCCEntity, BinarySensorEntity):
    """Representation of an XCC binary sensor."""

    def __init__(
        self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]
    ) -> None:
        """Initialize the XCC binary sensor."""
        try:
            entity_id = entity_data.get("entity_id", "")
            if not entity_id:
                prop = entity_data.get("prop", "")
                if prop:
                    entity_id = f"xcc_{prop.lower().replace('-', '_')}"
                    _LOGGER.warning(
                        "Missing entity_id in entity_data, generated from prop: %s",
                        entity_id,
                    )
                else:
                    raise ValueError(
                        f"No entity_id found in entity_data and no prop to generate from. Data keys: {list(entity_data.keys())}"
                    )

            # Create entity description
            description = self._create_entity_description(coordinator, entity_data)

            # Initialize parent class (XCCEntity handles the coordinator and entity setup)
            super().__init__(coordinator, entity_id, description)

            # Explicitly set entity_id to avoid HA's fallback of
            # slugify(device_name + friendly_name), which bakes the controller
            # IP address (part of the device name) into the entity_id.
            base_entity_id = entity_id.replace('-', '_')
            if not base_entity_id.startswith('xcc_'):
                base_entity_id = f"xcc_{base_entity_id}"
            self.entity_id = f"binary_sensor.{base_entity_id}"

        except Exception as err:
            _LOGGER.error(
                "Error in XCCBinarySensor.__init__ for %s: %s",
                entity_data.get("entity_id", "unknown"),
                err,
            )
            raise

    def _create_entity_description(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_data: dict[str, Any],
    ) -> BinarySensorEntityDescription:
        """Create entity description for the binary sensor."""
        entity_id = entity_data.get("entity_id", "")
        field_name = entity_data.get("attributes", {}).get("field_name", entity_id)

        # Determine device class from field name patterns
        device_class = self._determine_device_class(field_name)

        return BinarySensorEntityDescription(
            key=entity_id,
            device_class=device_class,
        )

    def _determine_device_class(self, field_name: str) -> BinarySensorDeviceClass | None:
        """Determine device class from field name and attributes."""
        field_name_lower = field_name.lower()

        # Map common field patterns to device classes
        if any(
            pattern in field_name_lower
            for pattern in ["alarm", "error", "chyba", "porucha"]
        ):
            return BinarySensorDeviceClass.PROBLEM
        if any(
            pattern in field_name_lower
            for pattern in ["running", "bezi", "chod", "provoz"]
        ):
            return BinarySensorDeviceClass.RUNNING
        if any(pattern in field_name_lower for pattern in ["heat", "teplo", "ohrev"]):
            return BinarySensorDeviceClass.HEAT
        if any(pattern in field_name_lower for pattern in ["cool", "chlad"]):
            return BinarySensorDeviceClass.COLD
        if any(
            pattern in field_name_lower for pattern in ["power", "napajeni", "vykon"]
        ):
            return BinarySensorDeviceClass.POWER
        if any(
            pattern in field_name_lower for pattern in ["connect", "pripoj", "online"]
        ):
            return BinarySensorDeviceClass.CONNECTIVITY
        if any(
            pattern in field_name_lower
            for pattern in ["door", "dvere", "cover", "kryt"]
        ):
            return BinarySensorDeviceClass.DOOR
        if any(pattern in field_name_lower for pattern in ["window", "okno"]):
            return BinarySensorDeviceClass.WINDOW
        if any(pattern in field_name_lower for pattern in ["motion", "pohyb"]):
            return BinarySensorDeviceClass.MOTION
        if any(pattern in field_name_lower for pattern in ["occupancy", "pritomnost"]):
            return BinarySensorDeviceClass.OCCUPANCY
        if any(pattern in field_name_lower for pattern in ["safety", "bezpecnost"]):
            return BinarySensorDeviceClass.SAFETY

        # Default to None (generic binary sensor)
        return None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        raw_value = self._get_current_value()
        return self._convert_value_for_ha(raw_value)

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the device class."""
        if hasattr(self.entity_description, "device_class"):
            return self.entity_description.device_class
        return self._get_device_class()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        # Add raw value for debugging
        raw_value = self._get_current_value()
        if raw_value is not None:
            attrs["raw_value"] = raw_value

        return attrs


class XCCDataIncompleteBinarySensor(
    CoordinatorEntity[XCCDataUpdateCoordinator], BinarySensorEntity
):
    """Diagnostic alarm: the integration is not gathering all XCC data pages.

    Computed from the coordinator's consecutive incomplete/failed poll counters,
    NOT from a data page — so it stays available and keeps reporting even while
    the controller is dropping data (the very condition it warns about). Turns on
    after ``coordinator.missing_page_alert_polls`` consecutive incomplete or
    failed polls and clears automatically on recovery. Alert on it directly, e.g.
    notify when ``binary_sensor.xcc_data_incomplete`` is ``on``.
    """

    _attr_has_entity_name = True
    _attr_name = "Data incomplete"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: XCCDataUpdateCoordinator) -> None:
        """Initialize the data-incomplete diagnostic sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.ip_address}_xcc_data_incomplete"
        self.entity_id = "binary_sensor.xcc_data_incomplete"
        self._attr_device_info = {"identifiers": {(DOMAIN, coordinator.ip_address)}}

    @property
    def available(self) -> bool:
        """Always available — the alarm must persist through the outage it reports."""
        return True

    @property
    def is_on(self) -> bool:
        """True once data gathering has been degraded for the alert threshold."""
        return self.coordinator.data_gathering_degraded

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the streak counters and which pages are missing."""
        c = self.coordinator
        return {
            "consecutive_incomplete_polls": c.consecutive_incomplete_polls,
            "consecutive_failed_polls": c.consecutive_failed_polls,
            "alert_after_polls": c.missing_page_alert_polls,
            "missing_pages": c.last_missing_pages,
            "pages_gathered": c.gathered_page_count,
            "pages_expected": c.expected_page_count,
            "last_poll_failed": c.last_poll_failed,
        }
