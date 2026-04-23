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
