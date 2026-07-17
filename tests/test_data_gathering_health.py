"""Tests for the data-gathering health detector.

The detection logic lives in the pure ``entity_helpers`` module (no Home
Assistant), so the full missing-pages -> streak -> alert decision is unit-tested
here without HA. The ``binary_sensor.xcc_data_incomplete`` entity that surfaces
it (is_on / always-available / attributes) is covered by the HA-gated
``test_data_incomplete_binary_sensor.py``.

Loaded via importlib (not ``from custom_components.xcc...``) so the package
``__init__`` — which imports Home Assistant — is not executed.
"""

import importlib.util
from pathlib import Path

XCC = Path(__file__).parent.parent / "custom_components" / "xcc"


def _load_entity_helpers():
    spec = importlib.util.spec_from_file_location(
        "xcc_entity_helpers_probe", XCC / "entity_helpers.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EH = _load_entity_helpers()
DATA_PAGES = ["FVE4.XML", "TUV11.XML", "OKRUH10.XML", "FVESOC1.XML"]
THRESHOLD = 5


# ---- missing_data_pages -----------------------------------------------------

def test_all_pages_present_none_missing():
    pages = {p: "<page>ok</page>" for p in DATA_PAGES}
    assert EH.missing_data_pages(DATA_PAGES, pages) == []


def test_error_content_counts_as_missing():
    pages = {p: "<page>ok</page>" for p in DATA_PAGES}
    pages["FVESOC1.XML"] = "Error: timeout fetching page FVESOC1.XML"
    assert EH.missing_data_pages(DATA_PAGES, pages) == ["FVESOC1.XML"]


def test_absent_key_counts_as_missing():
    pages = {p: "<page>ok</page>" for p in DATA_PAGES if p != "TUV11.XML"}
    assert EH.missing_data_pages(DATA_PAGES, pages) == ["TUV11.XML"]


def test_none_or_empty_pages():
    assert EH.missing_data_pages(DATA_PAGES, None) == sorted(DATA_PAGES)
    assert EH.missing_data_pages([], {}) == []


# ---- next_gather_health -----------------------------------------------------

def test_incomplete_streak_increments_then_resets_on_recovery():
    inc, fail = 0, 0
    inc, fail = EH.next_gather_health(["FVESOC1.XML"], False, inc, fail)
    assert (inc, fail) == (1, 0)
    inc, fail = EH.next_gather_health(["FVESOC1.XML"], False, inc, fail)
    assert (inc, fail) == (2, 0)
    inc, fail = EH.next_gather_health([], False, inc, fail)  # full data again
    assert (inc, fail) == (0, 0)


def test_failed_poll_bumps_failed_and_preserves_incomplete():
    inc, fail = 3, 0
    inc, fail = EH.next_gather_health([], True, inc, fail)  # whole update raised
    assert (inc, fail) == (3, 1)
    inc, fail = EH.next_gather_health([], False, inc, fail)  # clean poll clears both
    assert (inc, fail) == (0, 0)


# ---- end-to-end alert decision ---------------------------------------------

def test_partial_gathering_trips_alert_after_threshold_and_clears():
    inc, fail = 0, 0
    degraded = []
    for _ in range(6):
        inc, fail = EH.next_gather_health(["FVESOC1.XML"], False, inc, fail)
        degraded.append(max(inc, fail) >= THRESHOLD)
    assert degraded == [False, False, False, False, True, True]
    inc, fail = EH.next_gather_health([], False, inc, fail)
    assert max(inc, fail) < THRESHOLD  # recovery clears the alarm


def test_total_failures_also_trip_alert():
    inc, fail = 0, 0
    for _ in range(THRESHOLD):
        inc, fail = EH.next_gather_health([], True, inc, fail)
    assert max(inc, fail) >= THRESHOLD
