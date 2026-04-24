"""Pure helper functions for XCC entity-name normalization and type inference.

These helpers were extracted from ``coordinator.py`` so they can be reused by
platform modules (``sensor.py``, etc.) without dragging in a coordinator
instance, and so they can be unit-tested in isolation without importing
Home Assistant.

Nothing in this module imports from ``homeassistant`` or from the integration's
runtime classes — keep it that way so the test suite can exercise it in any
environment.
"""

from __future__ import annotations

import re
from typing import Any

# Property-name prefixes that descriptor and data pages disagree on. Stripping
# them lets ``normalize_property_name`` match e.g. ``WEB-OKRUHYODKAZPOCASI``
# against ``OKRUHYODKAZPOCASI`` from a different page.
_NORMALIZE_PREFIX_STRIPS: tuple[str, ...] = ("WEB-", "MAIN-", "CONFIG-")

_INVALID_ENTITY_ID_CHARS = re.compile(r"[^a-z0-9_]")
_REPEATED_UNDERSCORES = re.compile(r"_+")


def format_entity_id_suffix(prop: str) -> str:
    """Format an XCC property name into a valid Home Assistant entity-ID suffix.

    The ``xcc_`` prefix is **not** added — callers prepend it themselves so the
    same helper can be used for entity_id lookups that already include it.

    Examples
    --------
    >>> format_entity_id_suffix("TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA")
    'topneokruhyin3_fvepretopeni_priorita'
    >>> format_entity_id_suffix("FVE.ENABLED")
    'fve_enabled'
    >>> format_entity_id_suffix("")
    'unknown'
    """
    entity_id = prop.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    entity_id = _INVALID_ENTITY_ID_CHARS.sub("_", entity_id)
    entity_id = _REPEATED_UNDERSCORES.sub("_", entity_id).strip("_")
    return entity_id or "unknown"


def normalize_property_name(prop: str) -> str:
    """Normalize an XCC property name for cross-page lookup.

    Different XCC pages occasionally refer to the same logical property using
    slightly different separators (``_`` vs ``-`` vs ``.``) or page-scoped
    prefixes (``WEB-``, ``MAIN-``, ``CONFIG-``). This helper produces a
    canonical form so the coordinator can match a data-page prop against a
    descriptor prop even when those cosmetics differ.
    """
    normalized = prop.upper().replace("_", "-").replace(".", "-")
    for prefix in _NORMALIZE_PREFIX_STRIPS:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    return normalized


def infer_entity_type_from_attributes(entity: dict[str, Any]) -> str:
    """Infer a Home Assistant entity type from raw XCC entity attributes.

    Used when no descriptor entry exists for a property; relies purely on the
    register suffix (``_BOOL_i`` → boolean, ``_REAL_`` → numeric, etc.) that
    ``parse_xml_entities`` records under ``data_type``/``element_type``/
    ``is_settable``.

    Returns a *plural* key matching the buckets in
    ``XCCDataUpdateCoordinator._process_entities``'s ``processed_data`` dict.
    """
    attributes = entity.get("attributes", {})
    data_type = attributes.get("data_type", "unknown")
    element_type = attributes.get("element_type", "unknown")
    is_settable = attributes.get("is_settable", False)

    if data_type == "boolean":
        return "switches" if is_settable else "binary_sensors"
    if data_type == "enum":
        return "selects" if is_settable else "sensors"
    if data_type == "numeric":
        return "numbers" if is_settable else "sensors"
    if element_type in ("INPUT", "SELECT"):
        return "numbers" if data_type == "numeric" else "selects"
    return "sensors"


def lookup_with_normalized_fallback(
    prop: str,
    table: dict[str, Any],
    default: Any = None,
) -> Any:
    """Look up ``prop`` in ``table``, falling back to a normalized match.

    First tries an exact key match (the common case), then falls back to
    matching ``normalize_property_name(prop)`` against normalized table keys.
    Returns ``default`` when nothing matches.

    This is the shared lookup logic that previously appeared inline in
    ``XCCDataUpdateCoordinator.get_entity_type``, ``is_writable``, and
    ``get_entity_config``.
    """
    config = table.get(prop)
    if config is not None:
        return config

    normalized_prop = normalize_property_name(prop)
    for key, value in table.items():
        if normalize_property_name(key) == normalized_prop:
            return value
    return default


# Device priority order used by ``process_entities``. Highest priority first.
# Copied out of XCCDataUpdateCoordinator so the pure pipeline remains
# self-contained; keep in sync with coordinator._process_entities if that
# method is ever extended.
_DEVICE_PRIORITY: tuple[str, ...] = (
    "SYSCONFIG",
    "SPOT",
    "FVEINV",
    "FVE",
    "BIV",
    "OKRUH",
    "TUV1",
    "STAVJED",
    "NAST",
    "XCC_HIDDEN_SETTINGS",
)

# Entity-type → processed_data bucket. Anything not in this map falls through
# to the ``sensors`` bucket.
_BUCKET_BY_TYPE: dict[str, str] = {
    "switch": "switches",
    "binary_sensor": "binary_sensors",
    "number": "numbers",
    "select": "selects",
    "button": "buttons",
}


def _resolve_friendly_name(
    config: dict[str, Any], prop: str, language: str
) -> str:
    """Return the preferred friendly name for the given descriptor config.

    Mirrors ``XCCDataUpdateCoordinator._get_friendly_name`` but without a
    coordinator instance; ``language`` is matched against ``"english"`` so
    the helper doesn't have to import ``const``.
    """
    if language == "english":
        return (
            config.get("friendly_name_en")
            or config.get("friendly_name")
            or prop
        )
    return (
        config.get("friendly_name")
        or config.get("friendly_name_en")
        or prop
    )


def _normalize_page_to_device(page: str, prop: str) -> str:
    """Map a raw XCC page name onto a logical device key."""
    page_upper = page.upper()
    if page_upper == "NAST.XML":
        return "NAST"
    if page_upper == "MAIN.XML" or prop.startswith("SYSCONFIG-"):
        return "SYSCONFIG"
    if page_upper == "STATUS.XML":
        # STATUS.XML has no descriptor; its fields belong to the same logical
        # device as STAVJED1.XML (heat-pump unit status).
        return "STAVJED"
    return (
        page_upper
        .replace("1.XML", "")
        .replace("10.XML", "")
        .replace("11.XML", "")
        .replace("4.XML", "")
        .replace(".XML", "")
    )


def process_entities(
    raw_entities: list[dict[str, Any]],
    entity_configs: dict[str, dict[str, Any]],
    language: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Transform raw XCC entities into Home Assistant platform buckets.

    Pure extraction of ``XCCDataUpdateCoordinator._process_entities`` so the
    pipeline can be exercised in unit tests without instantiating a
    coordinator (and therefore without a running Home Assistant).

    Parameters
    ----------
    raw_entities:
        List produced by ``xcc_client.parse_xml_entities`` (plus optional
        SYSCONFIG entities from ``XCCClient.parse_main_xml_config_entities``).
    entity_configs:
        Descriptor/override table keyed by XCC property name
        (``XCCDescriptorParser.parse_descriptor_files`` output, optionally
        merged with ``DESCRIPTOR_OVERRIDES``).
    language:
        Either ``"english"`` or ``"czech"`` — controls friendly-name
        preference.

    Returns
    -------
    (processed_data, entities_metadata)
        ``processed_data`` has the exact structure expected by the platform
        modules (``sensors``, ``binary_sensors``, ``switches``, ``numbers``,
        ``selects``, ``buttons``, ``climates``, ``entities``).
        ``entities_metadata`` is the dict that the coordinator stores on
        ``self.entities`` (keyed by ``xcc_<suffix>``).
    """
    processed_data: dict[str, Any] = {
        "sensors": {},
        "binary_sensors": {},
        "switches": {},
        "numbers": {},
        "selects": {},
        "buttons": {},
        "climates": {},
    }
    entities_list: list[dict[str, Any]] = []
    entities_metadata: dict[str, dict[str, Any]] = {}

    entities_with_descriptors: list[dict[str, Any]] = []
    entities_without_descriptors: list[dict[str, Any]] = []

    for entity in raw_entities:
        prop = entity["attributes"]["field_name"]
        page = entity["attributes"].get("page", "unknown")
        has_descriptor = prop in entity_configs
        is_nast_entity = page.upper() == "NAST.XML"
        is_sysconfig_entity = prop.startswith("SYSCONFIG-")
        if has_descriptor or is_nast_entity or is_sysconfig_entity:
            entities_with_descriptors.append(entity)
        else:
            entities_without_descriptors.append(entity)

    entities_by_page: dict[str, list[dict[str, Any]]] = {}
    for entity in entities_with_descriptors:
        prop = entity["attributes"]["field_name"]
        page = entity["attributes"].get("page", "unknown")
        device_key = _normalize_page_to_device(page, prop)
        entities_by_page.setdefault(device_key, []).append(entity)

    if entities_without_descriptors:
        entities_by_page["XCC_HIDDEN_SETTINGS"] = entities_without_descriptors

    assigned_entities: set[str] = set()
    for device_name in _DEVICE_PRIORITY:
        if device_name not in entities_by_page:
            continue
        for entity in entities_by_page[device_name]:
            prop = entity["attributes"]["field_name"]
            if prop in assigned_entities:
                continue
            assigned_entities.add(prop)

            config = lookup_with_normalized_fallback(prop, entity_configs)
            entity_type = (config or {}).get("entity_type", "sensor")
            if entity_type == "sensor" and prop not in entity_configs:
                parsed_type = entity.get("entity_type")
                if parsed_type and parsed_type != "sensor":
                    entity_type = parsed_type

            descriptor_config = entity_configs.get(prop, {})
            if (
                entity["attributes"].get("page", "").upper() == "NAST.XML"
                and not descriptor_config
            ):
                entity_attrs = entity.get("attributes", {})
                descriptor_config = {
                    "friendly_name": entity_attrs.get(
                        "friendly_name", prop.replace("-", " ").title()
                    ),
                    "friendly_name_en": entity_attrs.get(
                        "friendly_name", prop.replace("-", " ").title()
                    ),
                    "unit": entity_attrs.get("unit_of_measurement", ""),
                    "element_type": entity.get("entity_type", "sensor"),
                    "source": "NAST",
                }

            friendly_name = _resolve_friendly_name(
                descriptor_config, prop, language
            )
            unit = (
                descriptor_config.get("unit")
                or entity["attributes"].get("unit", "")
            )
            entity_id = f"xcc_{format_entity_id_suffix(prop)}"
            page = entity["attributes"].get("page", "unknown")

            entities_list.append({
                "entity_id": entity_id,
                "prop": prop,
                "name": friendly_name,
                "friendly_name": friendly_name,
                "state": entity["attributes"].get("value", ""),
                "unit": unit,
                "page": page,
                "device": device_name,
            })

            entities_metadata[entity_id] = {
                "type": entity_type,
                "entity_id": entity_id,
                "data": entity,
                "page": page,
                "prop": prop,
                "descriptor_config": descriptor_config,
                "device": device_name,
            }

            state_data = {
                "state": entity.get("state", ""),
                "attributes": entity["attributes"],
                "entity_id": entity_id,
                "prop": prop,
                "name": friendly_name,
                "unit": unit,
                "page": page,
                "device": device_name,
            }
            bucket = _BUCKET_BY_TYPE.get(entity_type, "sensors")
            processed_data[bucket][entity_id] = state_data

    processed_data["entities"] = entities_list
    return processed_data, entities_metadata
