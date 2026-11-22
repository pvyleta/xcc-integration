"""Per-page and whole-poll timeouts in ``XCCClient.fetch_pages``.

A slow page must cost only that page: the pages already fetched survive, and
pages not reached before the poll deadline are marked ``"Error: Timeout"``
(which ``missing_data_pages`` counts) instead of being attempted.
"""

import asyncio
import importlib.util
import os
import sys
from types import ModuleType

import pytest

_XCC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "custom_components", "xcc")
)


def _load_module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, os.path.join(_XCC_DIR, filename))
    assert spec and spec.loader, f"cannot load {filename}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# descriptor_parser first: xcc_client falls back to a top-level import of it.
_load_module("descriptor_parser", "descriptor_parser.py")
_xcc_client = _load_module("_xcc_client_timeouts", "xcc_client.py")
_entity_helpers = _load_module("_xcc_entity_helpers_timeouts", "entity_helpers.py")


def _client(delays: dict[str, float]):
    client = _xcc_client.XCCClient("192.168.1.100", "xcc", "xcc")
    fetched = []

    async def fake_fetch_page(page):
        fetched.append(page)
        await asyncio.sleep(delays.get(page, 0))
        return f"<PAGE>{page}</PAGE>"

    client.fetch_page = fake_fetch_page
    return client, fetched


@pytest.mark.asyncio
async def test_slow_page_times_out_alone():
    pages = ["A.XML", "SLOW.XML", "C.XML"]
    client, fetched = _client({"SLOW.XML": 5})

    results = await client.fetch_pages(pages, page_timeout=0.1)

    assert results["SLOW.XML"] == "Error: Timeout"
    assert results["A.XML"] == "<PAGE>A.XML</PAGE>"
    assert results["C.XML"] == "<PAGE>C.XML</PAGE>"
    assert fetched == pages
    assert _entity_helpers.missing_data_pages(pages, results) == ["SLOW.XML"]


@pytest.mark.asyncio
async def test_poll_deadline_skips_unreached_pages():
    pages = ["A.XML", "SLOW.XML", "C.XML", "D.XML"]
    client, fetched = _client({"SLOW.XML": 5})

    # A at t=0, SLOW from t=0.2 cut at the 0.5 s deadline, C and D never tried.
    results = await client.fetch_pages(pages, page_timeout=10, total_timeout=0.5)

    assert results["A.XML"] == "<PAGE>A.XML</PAGE>"
    assert results["SLOW.XML"] == "Error: Timeout"
    assert results["C.XML"] == results["D.XML"] == "Error: Timeout"
    assert fetched == ["A.XML", "SLOW.XML"]
    assert set(results) == set(pages)


@pytest.mark.asyncio
async def test_no_timeouts_fetches_everything():
    pages = ["A.XML", "B.XML"]
    client, _ = _client({})

    results = await client.fetch_pages(pages)

    assert results == {p: f"<PAGE>{p}</PAGE>" for p in pages}
