"""Legacy/current login detection and bounded HTTP-200 session recovery."""

import asyncio
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/xcc"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, COMPONENT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("descriptor_parser", "descriptor_parser.py")
client_module = _load("_xcc_login_test_client", "xcc_client.py")
MODERN = (ROOT / "tests/sample_data/login-modern.html").read_text(encoding="utf-8")
LEGACY = '<LOGIN><USER VALUE=""/><PASS VALUE=""/></LOGIN>'
DATA = '<page><INPUT P="SAKTTEP" NAME="__R1_REAL_r1" VALUE="32.1"/></page>'


class Response:
    status = 200

    def __init__(self, content):
        self.content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def read(self):
        return self.content.encode("utf-8")

    async def text(self):
        return self.content

    def get_encoding(self):
        return "utf-8"


class Session:
    def __init__(self, responses, post_response=DATA):
        self.responses = iter(responses)
        self.requests = []
        self.post_response = post_response
        self.cookie_jar = [SimpleNamespace(key="SoftPLC", value="test-session")]

    def get(self, url):
        self.requests.append(url)
        return Response(next(self.responses))

    def post(self, url, data):
        return Response(self.post_response)


@pytest.fixture
def client():
    client_module._auth_locks.clear()
    return client_module.XCCClient("192.0.2.1", "test", "test")


@pytest.mark.parametrize("page", [LEGACY, "<LOGIN/>", MODERN,
    MODERN.replace('id="loginForm"', "id='LOGINFORM'"),
    MODERN.replace('id="loginForm"', 'id="other"')])
def test_login_formats_detected(client, page):
    assert client._is_login_page(page)
    assert not client._is_session_valid(200, page)


@pytest.mark.parametrize("page", [DATA, "", "Login settings",
    '<html><title>Login settings</title><form id="settings">'
    '<input type="password"></form></html>',
    '<html><script>const target="LOGIN.XML";</script></html>'])
def test_non_login_pages_are_not_false_positives(client, page):
    assert not client._is_login_page(page)


@pytest.mark.asyncio
async def test_cached_html_login_session_is_invalid(client):
    client.session = Session([MODERN])
    assert not await client._test_session()


@pytest.mark.asyncio
@pytest.mark.parametrize("login_page", [LEGACY, MODERN])
async def test_expired_session_reauthenticates_and_retries_same_page(client, login_page):
    client.session = Session([login_page, DATA])
    client._test_session = AsyncMock(return_value=False)
    client._authenticate = AsyncMock()
    assert await client.fetch_page("STATUS.XML") == DATA
    client._authenticate.assert_awaited_once()
    assert client.session.requests == ["http://192.0.2.1/STATUS.XML"] * 2


@pytest.mark.asyncio
async def test_session_fixed_by_other_request_skips_duplicate_auth(client):
    client.session = Session([MODERN, DATA])
    client._test_session = AsyncMock(return_value=True)
    client._authenticate = AsyncMock()
    assert await client.fetch_page("STATUS.XML") == DATA
    client._authenticate.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RuntimeError("Authentication failed"),
                                 LookupError("Authentication failed")])
async def test_authentication_failure_is_not_returned_as_data(client, error):
    client.session = Session([MODERN])
    client._test_session = AsyncMock(return_value=False)
    client._authenticate = AsyncMock(side_effect=error)
    result = await client.fetch_pages(["STATUS.XML"])
    assert result["STATUS.XML"].startswith("Error:")
    assert "Authentication failed" in result["STATUS.XML"]


@pytest.mark.asyncio
async def test_failed_retry_is_not_returned_as_data(client):
    client.session = Session([MODERN, MODERN])
    client._test_session = AsyncMock(return_value=False)
    client._authenticate = AsyncMock()
    with pytest.raises(Exception, match="Session re-authentication failed"):
        await client.fetch_page("STATUS.XML")
    assert len(client.session.requests) == 2


@pytest.mark.asyncio
async def test_cancelled_authentication_propagates(client):
    client.session = Session([MODERN])
    client._test_session = AsyncMock(return_value=False)
    client._authenticate = AsyncMock(side_effect=asyncio.CancelledError)
    with pytest.raises(asyncio.CancelledError):
        await client.fetch_page("STATUS.XML")


@pytest.mark.asyncio
@pytest.mark.parametrize("login_page", [LEGACY, MODERN])
async def test_unsuccessful_login_post_is_rejected(client, login_page):
    client.session = Session([MODERN], post_response=login_page)
    with pytest.raises(Exception, match="Authentication failed"):
        await client._authenticate()


@pytest.mark.asyncio
async def test_valid_data_is_unchanged(client):
    client.session = Session([DATA])
    client._authenticate = AsyncMock()
    assert await client.fetch_page("STATUS.XML") == DATA
    client._authenticate.assert_not_awaited()


@pytest.mark.asyncio
async def test_encoding_fallback_is_preserved(client):
    page = '<?xml version="1.0" encoding="unknown-codec"?>' + DATA
    client.session = Session([page])
    assert await client.fetch_page("STATUS.XML") == page
