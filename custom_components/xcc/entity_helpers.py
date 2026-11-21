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

# Heating-circuit namespacing. Mirrors xcc_client.qualify_circuit_prop, kept
# local so this module stays dependency-free (see module docstring).
_OKRUH_DATA_PAGE_RE = re.compile(r"^OKRUH1(\d+)\.XML$")
_OKRUH_PROP_RE = re.compile(r"^OKRUH(\d+)-(.+)$")


def _circuit_base_props(prop: str) -> tuple[str, ...]:
    """Return the bare names a circuit-namespaced prop may stand for.

    ``OKRUH<n>-X`` was either ``TO-X`` or ``X`` on its page; ``TO-X`` first.
    Empty when ``prop`` is not namespaced.
    """
    match = _OKRUH_PROP_RE.match((prop or "").upper())
    if not match:
        return ()
    return f"TO-{match.group(2)}", match.group(2)


def _in_table(prop: str, table: dict[str, Any]) -> bool:
    """Exact key match, counting a namespaced prop's bare counterpart.

    okruh.xml is shared across circuits, so ``OKRUH<n>-X`` is described (and
    pinned) wherever its circuit-0 twin is.
    """
    return prop in table or any(base in table for base in _circuit_base_props(prop))


def circuit_of_prop(prop: str) -> int | None:
    """Return the circuit index a namespaced prop belongs to, else None."""
    match = _OKRUH_PROP_RE.match((prop or "").upper())
    return int(match.group(1)) if match else None


def own_or_twin_config(prop: str, table: dict[str, Any]) -> dict[str, Any]:
    """Exact descriptor entry for ``prop``, else its circuit-0 twin's, else ``{}``."""
    for key in (prop, *_circuit_base_props(prop)):
        if key in table:
            return table[key]
    return {}


def circuit_label(circuit: int, page_name: str | None = None) -> str:
    """The controller's name for a circuit: its ``PAGENAME``, else the default.

    main.xml numbers ``okruh.xml?page=n`` as ``n + 1`` and names unrenamed
    circuits ``Okruh <n + 1>``, so the page index alone would be off by one.
    """
    return (page_name or "").strip() or f"Okruh {circuit + 1}"


def circuit_page_name(entities: dict[str, dict[str, Any]], prop: str) -> str | None:
    """Live ``PAGENAME`` of the circuit ``prop`` belongs to, from entity metadata."""
    circuit = circuit_of_prop(prop)
    if circuit is None:
        return None
    meta = entities.get(f"xcc_okruh{circuit}_pagename") or {}
    return (meta.get("data") or {}).get("state")


def qualify_circuit_name(name: str, prop: str, page_name: str | None = None) -> str:
    """Prefix a secondary circuit's entity name with its circuit's label.

    Secondary circuits inherit circuit 0's descriptor, so without this every
    circuit renders under the same name. Circuit 0 and non-circuit props are
    returned unchanged. A name that is just the namespaced prop falls back to
    the bare prop, matching how circuit 0's undescribed twin is named.
    """
    circuit = circuit_of_prop(prop)
    if circuit is None:
        return name
    if not name or name.upper() == prop.upper():
        name = prop.split("-", 1)[1]
    return f"{circuit_label(circuit, page_name)} {name}"


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

    # Circuit-namespaced props (OKRUH<n>-KONSTANTA) have no descriptor of their
    # own — okruh.xml is byte-identical for every ?page=N and describes them
    # under the bare name. Fall back to that so secondary circuits inherit
    # circuit 0's entity type, unit, select options and read-only pins.
    missing = object()
    for base_prop in _circuit_base_props(prop):
        config = lookup_with_normalized_fallback(base_prop, table, missing)
        if config is not missing:
            return config

    return default


# Device priority order used by ``process_entities``. Highest priority first.
# Any entity whose page-derived device key (see ``_normalize_page_to_device``)
# is *not* listed here is silently dropped, so every sub-device whose data
# pages may carry descriptor-backed props must appear in this tuple.
# Keep in sync with ``XCCDataUpdateCoordinator._init_device_info``.
_DEVICE_PRIORITY: tuple[str, ...] = (
    "SYSCONFIG",
    "SPOT",
    "FVEINV",
    "FVE",
    "BIV",
    "BIVTUV",
    "OKRUH",
    "TUV1",
    "TUV2",
    "BAZEN1",
    "BAZEN2",
    "BAZMIST",
    "SOLAR",
    "AKU",
    "POCASI",
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
    config: dict[str, Any],
    prop: str,
    language: str,
    page_names: dict[int, str] | None = None,
) -> str:
    """Return the preferred friendly name for the given descriptor config.

    Mirrors ``XCCDataUpdateCoordinator._get_friendly_name`` but without a
    coordinator instance; ``language`` is matched against ``"english"`` so
    the helper doesn't have to import ``const``.
    """
    if language == "english":
        name = (
            config.get("friendly_name_en")
            or config.get("friendly_name")
            or prop
        )
    else:
        name = (
            config.get("friendly_name")
            or config.get("friendly_name_en")
            or prop
        )

    circuit = circuit_of_prop(prop)
    page_name = (page_names or {}).get(circuit) if circuit is not None else None
    return qualify_circuit_name(name, prop, page_name)


def _normalize_page_to_device(page: str, prop: str) -> str:
    """Map a raw XCC page name onto a logical device key."""
    page_upper = page.upper()
    if _OKRUH_DATA_PAGE_RE.match(page_upper):
        # Every circuit's data page (OKRUH10/OKRUH11/OKRUH12/...) folds into the
        # single OKRUH device. Without this the replace-chain below yields
        # "OKRUH1"/"OKRUH12", neither of which is in _DEVICE_PRIORITY, so those
        # circuits' entities were silently dropped. Circuit collisions are
        # prevented by prop namespacing (see xcc_client.qualify_circuit_prop),
        # not by the device key.
        return "OKRUH"
    if page_upper.startswith("NAST"):
        # nast.xml descriptor + the NAST1/2/3.XML data pages it spans (one per
        # <block data="NASTn">). All fold into the single NAST device; without
        # this NAST2.XML/NAST3.XML would normalize to "NAST2"/"NAST3" (absent
        # from _DEVICE_PRIORITY) and their entities would be silently dropped.
        return "NAST"
    if page_upper == "MAIN.XML" or prop.startswith("SYSCONFIG-"):
        return "SYSCONFIG"
    if page_upper == "STATUS.XML":
        # STATUS.XML has no descriptor; its fields belong to the same logical
        # device as STAVJED1.XML (heat-pump unit status).
        return "STAVJED"
    if page_upper.startswith("FVESOC"):
        # fvesoc.xml / FVESOC1.XML carry the monthly battery SOC-curve setpoints
        # (FVE-SOCCONFIG-SOCCURVE*). They belong to the Photovoltaics system, so
        # group them under the existing FVE device. A bare "FVESOC" key is not in
        # _DEVICE_PRIORITY and its entities would otherwise be silently dropped.
        return "FVE"
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
    page_names: dict[int, str] = {}

    for entity in raw_entities:
        prop = entity["attributes"]["field_name"]
        page = entity["attributes"].get("page", "unknown")
        has_descriptor = _in_table(prop, entity_configs)
        circuit = circuit_of_prop(prop)
        if circuit is not None and prop.upper() == f"OKRUH{circuit}-PAGENAME":
            page_names[circuit] = entity.get("state") or ""
        is_nast_entity = page.upper().startswith("NAST")
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
            if entity_type == "sensor" and not _in_table(prop, entity_configs):
                parsed_type = entity.get("entity_type")
                if parsed_type and parsed_type != "sensor":
                    entity_type = parsed_type

            descriptor_config = own_or_twin_config(prop, entity_configs)
            if (
                entity["attributes"].get("page", "").upper().startswith("NAST")
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
                descriptor_config, prop, language, page_names
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


# ---------------------------------------------------------------------------
# Data-gathering health
#
# A flaky controller can keep dropping some data pages while the overall poll
# still "succeeds": ``client.fetch_pages`` returns an ``"Error: ..."`` string for
# each page it could not fetch, and the coordinator simply skips those. Their
# entities then go stale/unavailable silently. These pure helpers let the
# coordinator fold each poll into two streak counters so a diagnostic
# binary_sensor + a Repairs issue can alert once the gap persists.
# ---------------------------------------------------------------------------

def missing_data_pages(
    expected_pages: "list[str] | set[str]", pages_data: dict[str, Any] | None
) -> list[str]:
    """Return the expected data pages NOT successfully gathered this poll.

    A page counts as gathered only when ``pages_data`` holds it with real content
    (not an ``"Error: ..."`` sentinel). A requested page absent from
    ``pages_data`` also counts as missing.
    """
    gathered = {
        page
        for page, content in (pages_data or {}).items()
        if isinstance(content, str) and not content.startswith("Error:")
    }
    return sorted(set(expected_pages) - gathered)


def next_gather_health(
    missing_pages: list[str],
    poll_failed: bool,
    prev_incomplete: int,
    prev_failed: int,
) -> tuple[int, int]:
    """Fold one poll's outcome into ``(incomplete_streak, failed_streak)``.

    - A *failed* poll (the whole update raised) bumps the failed streak and
      leaves the incomplete streak untouched — completeness can't be judged.
    - A *successful* poll clears the failed streak, then bumps the incomplete
      streak when any expected page is missing, else resets it to 0.
    """
    if poll_failed:
        return prev_incomplete, prev_failed + 1
    incomplete = prev_incomplete + 1 if missing_pages else 0
    return incomplete, 0
