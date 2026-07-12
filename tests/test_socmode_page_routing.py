"""Regression test: FVE-SOCCONFIG-SOCMODE must route to FVE4.XML, not FVESOC1.XML.

v1.15.12 routed every FVE-SOCCONFIG-* write to FVESOC1.XML (added for the
SOCCURVE0..11 monthly setpoints). SOCMODE and MANUALSOC are inputs on FVE4.XML,
so their NAME lookup against FVESOC1.XML failed on every attempt and the write
never reached the controller.

Unlike the older page-detection tests, this exercises the real set_value()
against the real sample data pages instead of duplicating the routing logic.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("homeassistant")

from custom_components.xcc.xcc_client import XCCClient

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def _read_sample(name: str) -> str:
    path = SAMPLE_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="windows-1250", errors="ignore")


def _client_with_mocked_io() -> tuple[XCCClient, AsyncMock, AsyncMock]:
    """Client whose fetch_page serves real sample pages and whose POST is captured."""
    client = XCCClient("192.168.1.100", "xcc", "xcc")

    async def fake_fetch_page(page: str) -> str:
        return _read_sample(page)

    fetch_mock = AsyncMock(side_effect=fake_fetch_page)
    client.fetch_page = fetch_mock

    post_response = MagicMock()
    post_response.status = 200
    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=post_response)
    post_cm.__aexit__ = AsyncMock(return_value=False)
    # aiohttp's post() returns the context manager synchronously
    session = MagicMock()
    session.post = MagicMock(return_value=post_cm)
    client.session = session

    return client, fetch_mock, session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prop", "expected_page", "expected_name"),
    [
        ("FVE-SOCCONFIG-SOCMODE", "FVE4.XML", "__R69665_USINT_u"),
        ("FVE-SOCCONFIG-MANUALSOC", "FVE4.XML", "__R69678_USINT_u"),
        ("FVE-SOCCONFIG-SOCCURVE0", "FVESOC1.XML", None),
        ("FVE-SOCCONFIG-SOCCURVE11", "FVESOC1.XML", None),
    ],
)
async def test_fve_socconfig_write_routing(prop, expected_page, expected_name):
    """set_value must fetch the page that actually carries the prop's NAME."""
    client, fetch_mock, session = _client_with_mocked_io()

    result = await client.set_value(prop, "0")

    assert result is True, f"set_value({prop}) failed — NAME not found on routed page"
    fetch_mock.assert_awaited_once_with(expected_page)

    (url,), kwargs = session.post.call_args
    assert url.endswith(expected_page), f"POST for {prop} went to {url}"
    posted = kwargs["data"]
    if expected_name is not None:
        assert posted == {expected_name: "0"}
    else:
        # SOCCURVE NAMEs vary per slot; the prop must resolve to exactly one NAME
        assert len(posted) == 1 and next(iter(posted)).startswith("__R")


@pytest.mark.asyncio
async def test_socmode_name_absent_from_fvesoc_page():
    """Guard the premise: FVESOC1.XML must not grow a SOCMODE input silently."""
    client, _, _ = _client_with_mocked_io()
    mapping = client._extract_name_mapping_from_xml(_read_sample("FVESOC1.XML"))
    assert "FVE-SOCCONFIG-SOCMODE" not in mapping
    assert all(f"FVE-SOCCONFIG-SOCCURVE{i}" in mapping for i in range(12))
