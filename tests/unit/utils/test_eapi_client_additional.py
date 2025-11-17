import json

import aiohttp
import pytest

from avd_cli.exceptions import AuthenticationError, ConfigurationError, ConnectionError
from avd_cli.utils.eapi_client import EapiClient, EapiConfig


class DummyResponse:
    """Mock response object for aiohttp testing."""

    def __init__(self, payload, *, raise_exc=None):
        self.payload = payload
        self.raise_exc = raise_exc

    def raise_for_status(self):
        if self.raise_exc:
            raise self.raise_exc

    async def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class DummyDevice:
    """Mock device object for testing HTTP POST calls."""

    def __init__(self, responses):
        self.responses = responses
        self.post_calls = []

    def post(self, url, json):
        self.post_calls.append({"url": url, "json": json})
        if not self.responses:
            raise RuntimeError("No responses configured")
        return self.responses.pop(0)


def _build_client() -> EapiClient:
    return EapiClient(EapiConfig(host="example", username="user", password="pass"))


@pytest.mark.asyncio
async def test_execute_commands_authentication_error() -> None:
    client = _build_client()
    exc = aiohttp.ClientResponseError(request_info=None, history=(), status=401, message="auth")
    client._device = DummyDevice([])
    client._device.post = lambda url, json: (_ for _ in ()).throw(exc)

    with pytest.raises(AuthenticationError):
        await client._execute_commands(["show version"])


@pytest.mark.asyncio
async def test_execute_commands_invalid_json() -> None:
    client = _build_client()
    client._device = DummyDevice([
        DummyResponse(json.JSONDecodeError("msg", "doc", 0)),
    ])

    with pytest.raises(ConnectionError):
        await client._execute_commands(["show version"])


@pytest.mark.asyncio
async def test_get_running_config_fallback(monkeypatch) -> None:
    client = _build_client()
    calls = []

    async def fake_execute(commands):
        calls.append(commands)
        if len(calls) == 1:
            raise ConfigurationError("fail")
        return [{"output": "running"}]

    monkeypatch.setattr(client, "_execute_commands", fake_execute)

    assert await client.get_running_config() == "running"


@pytest.mark.asyncio
async def test_apply_config_wraps_session_errors(monkeypatch) -> None:
    client = _build_client()

    async def fake_session(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(client, "_apply_config_session", fake_session)

    with pytest.raises(ConfigurationError) as exc_info:
        await client.apply_config("hostname test")

    assert "Configuration validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_apply_config_session_show_diff_and_dry_run(monkeypatch) -> None:
    client = _build_client()
    client._device = DummyDevice([
        DummyResponse({"result": [{}, {}, {}]}),
        DummyResponse({"result": [{}, {}, {"output": "diff"}]}),
        DummyResponse({"result": [{}, {}, {}]}),
    ])
    monkeypatch.setattr("time.time", lambda: 1)

    diff = await client._apply_config_session(
        "\nhostname\nhostname test\ninterface Ethernet0\n",
        dry_run=True,
        show_diff=True,
    )

    assert diff == "diff"
    assert client._device.post_calls[-1]["json"]["params"]["cmds"][2] == "abort"


@pytest.mark.asyncio
async def test_apply_config_session_handles_http_error(monkeypatch) -> None:
    client = _build_client()
    exc = aiohttp.ClientResponseError(request_info=None, history=(), status=401, message="auth")
    client._device = DummyDevice([])
    client._device.post = lambda url, json: (_ for _ in ()).throw(exc)

    with pytest.raises(AuthenticationError):
        await client._apply_config_session("hostname test")
