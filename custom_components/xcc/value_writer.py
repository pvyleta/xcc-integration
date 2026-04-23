"""Pure helpers for resolving an HA entity_id back to an XCC property write.

The coordinator's ``async_set_entity_value`` method needs to translate an HA
entity_id (e.g. ``number.xcc_to_pozadovana_teplota``) back into the original
XCC ``prop`` (e.g. ``TO-POZADOVANA-TEPLOTA``) plus the optional ``internal_name``
that SYSCONFIG entities carry for the controller's internal addressing.

Resolution is tried in four steps, from most-trustworthy (the live ``data``
dict produced by the most recent poll) to weakest (uppercasing the suffix of
the entity_id). The first step that succeeds wins.

This module is import-safe without Home Assistant — it operates on plain dicts
and strings only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Per-platform entity_id prefixes that ``resolve_property`` strips when falling
# back to deriving the prop from the entity_id. Order doesn't matter; each is
# applied with ``str.replace`` so a missing prefix is a no-op.
_PLATFORM_PREFIXES: tuple[str, ...] = (
    "number.xcc_",
    "switch.xcc_",
    "select.xcc_",
    "number.",
    "switch.",
    "select.",
)


@dataclass
class PropResolution:
    """Result of resolving an entity_id back to an XCC property.

    ``prop`` is empty if no resolution method produced anything (caller should
    treat that as failure). ``method`` describes the winning step for logging.
    """

    prop: str = ""
    internal_name: str | None = None
    method: str = ""
    attempted: list[str] = field(default_factory=list)


def resolve_property(
    entity_id: str,
    data: dict[str, Any] | None,
    entity_configs: dict[str, Any] | None,
) -> PropResolution:
    """Resolve an HA entity_id to an XCC ``prop`` (and ``internal_name``).

    Parameters
    ----------
    entity_id:
        The HA entity_id whose value the caller wants to write to the XCC
        controller.
    data:
        The coordinator's most recent ``processed_data`` dict (the value
        ``DataUpdateCoordinator.data`` exposes after a successful update).
        May be ``None`` before the first poll completes.
    entity_configs:
        The ``self.entity_configs`` dict produced from descriptor parsing plus
        ``DESCRIPTOR_OVERRIDES``. May be ``None``/empty before descriptors are
        loaded.

    Returns
    -------
    A :class:`PropResolution` whose ``prop`` is empty when no method matched.
    """
    result = PropResolution()
    data = data or {}
    entity_configs = entity_configs or {}

    # Method 1 — exact lookup in the live per-type buckets. Most reliable
    # because it captures both ``prop`` and ``internal_name`` from the same
    # poll cycle that produced the entity HA is now writing to.
    for bucket in ("numbers", "switches", "selects"):
        bucket_data = data.get(bucket, {})
        if entity_id in bucket_data:
            entity_data = bucket_data[entity_id]
            attrs = entity_data.get("attributes", {}) or {}
            prop = attrs.get("prop")
            if prop:
                result.prop = prop
                result.internal_name = attrs.get("internal_name")
                result.method = f"found in {bucket} data"
                result.attempted.append(result.method)
                return result

    # Method 2 — flat ``entities`` list (older code path; some entities only
    # exist there, never in the per-type buckets).
    for entity in data.get("entities", []) or []:
        if entity.get("entity_id") == entity_id:
            prop = (entity.get("prop") or "").upper()
            if prop:
                result.prop = prop
                result.internal_name = (entity.get("attributes") or {}).get("internal_name")
                result.method = "found in general entities list"
                result.attempted.append(result.method)
                return result

    # Method 3 — descriptor configs keyed by canonical XCC prop.
    suffix = entity_id
    for prefix in _PLATFORM_PREFIXES:
        suffix = suffix.replace(prefix, "")
    suffix_upper = suffix.upper()
    for config_prop in entity_configs:
        if config_prop.lower() == suffix_upper.lower():
            result.prop = config_prop
            result.method = "found in entity configs"
            result.attempted.append(result.method)
            return result

    # Method 4 — last-resort uppercase derivation from the entity_id itself.
    # We always succeed here (just maybe with a wrong prop) so the caller can
    # log a single clear failure when the controller rejects the write.
    derived = entity_id
    for prefix in _PLATFORM_PREFIXES:
        derived = derived.replace(prefix, "")
    derived = derived.upper()
    if derived:
        result.prop = derived
        result.method = "derived from entity_id"
        result.attempted.append(result.method)
    return result
