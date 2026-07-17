"""Regression tests for two integration-setup bugs.

Bug 1 — redundant first refresh inside a forwarded platform.
    ``__init__.async_setup_entry`` performs ``async_config_entry_first_refresh``
    ONCE, before forwarding platforms. sensor/select/switch each called it AGAIN
    in their own ``async_setup_entry``; that second call re-fetches every page and,
    if it races the per-page timeout (e.g. the slow FVESOC1.XML added in v1.15.12),
    raises ``ConfigEntryNotReady`` from within the forwarded platform. The other
    platforms had already set up, so the entry ends up partially loaded and the
    losing platform's entities are never (re)registered — they show "unavailable"
    (a restored registry entry with no live entity). Observed: cooling stuck on
    because ``switch.xcc_to_config_chlazeni`` could not be written.

Bug 2 — datetime fields inheriting the numeric ``h`` unit.
    The ``CAS``->``h`` unit heuristic matched the substring ``TIME`` inside
    ``DATETIME``/``TIMESTAMP``, so datetime props (e.g. ``FLASH-HEADER*-DATETIME``,
    value ``01.01.1970 00:00``) got unit ``h``. HA then coerces the state to float
    and raises ``ValueError`` on every read. Genuine hours-durations must keep ``h``.
"""

import importlib.util
import logging
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
XCC = REPO / "custom_components" / "xcc"


def _load_descriptor_parser():
    spec = importlib.util.spec_from_file_location(
        "descriptor_parser", XCC / "descriptor_parser.py"
    )
    mod = importlib.util.module_from_spec(spec)
    mod._LOGGER = logging.getLogger("test")
    spec.loader.exec_module(mod)
    return mod


def _code_without_comments(path: Path) -> str:
    """Source with full-line ``#`` comments dropped, so a comment that merely
    *names* the forbidden call doesn't count as calling it."""
    return "\n".join(
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("#")
    )


# --------------------------------------------------------------------------- #
# Bug 1: forwarded platforms must not call the blocking first refresh
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "platform", ["sensor", "select", "switch", "number", "binary_sensor", "button"]
)
def test_platform_setup_has_no_blocking_first_refresh(platform):
    code = _code_without_comments(XCC / f"{platform}.py")
    assert "async_config_entry_first_refresh" not in code, (
        f"{platform}.py must not call async_config_entry_first_refresh(); __init__ "
        "already performs the first refresh once, before forwarding platforms. A "
        "second call re-fetches all pages and can raise ConfigEntryNotReady mid-"
        "forward, leaving this platform's entities stuck 'unavailable'."
    )


def test_init_performs_single_first_refresh_before_forwarding():
    code = (XCC / "__init__.py").read_text(encoding="utf-8")
    assert code.count("async_config_entry_first_refresh") == 1, (
        "__init__ should own exactly one first refresh"
    )
    assert code.index("async_config_entry_first_refresh") < code.index(
        "async_forward_entry_setups"
    ), "the first refresh must run before platforms are forwarded"


# --------------------------------------------------------------------------- #
# Bug 2: datetime props must not infer the numeric 'h' unit
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "prop",
    [
        "FLASH-HEADER0-DATETIME",
        "FLASH-HEADER1-DATETIME",
        "FLASH-HEADER2-DATETIME",
        "SPOTOVECENYSTATS-DATA0-TIMESTAMP",
    ],
)
def test_datetime_prop_gets_no_hours_unit(prop):
    parser = _load_descriptor_parser().XCCDescriptorParser()
    assert parser._infer_unit_from_context(prop, None, None) != "h", (
        f"{prop} is a datetime string and must not infer the numeric 'h' unit"
    )


@pytest.mark.parametrize("prop", ["PROVOZHODIN", "PROVOZCAS", "BIVALENCECASSPUSTENI"])
def test_real_duration_props_keep_hours_unit(prop):
    """The datetime carve-out must not regress genuine hours-duration fields."""
    parser = _load_descriptor_parser().XCCDescriptorParser()
    assert parser._infer_unit_from_context(prop, None, None) == "h"


def test_flash_header_datetime_label_resolves_without_numeric_unit():
    """End-to-end via the real NAST descriptor: the FLASH-HEADER0-DATETIME <label>
    must resolve to a string sensor with no numeric unit (and thus no duration
    device_class), which is what previously caused the per-read ValueError."""
    nast = REPO / "tests" / "sample_data" / "nast.xml"
    if not nast.exists():
        pytest.skip("nast.xml sample not found")
    parser = _load_descriptor_parser().XCCDescriptorParser()
    cfgs = parser._parse_single_descriptor(nast.read_text(encoding="utf-8"), "nast")
    cfg = cfgs.get("FLASH-HEADER0-DATETIME")
    assert cfg is not None, "FLASH-HEADER0-DATETIME should be parsed from nast.xml"
    assert cfg.get("unit") in (None, ""), f"unexpected unit: {cfg.get('unit')!r}"
    assert cfg.get("device_class") != "duration"
