#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for eAPI client."""

from typing import Any, Dict

import pytest
from aioresponses import aioresponses

from avd_cli.exceptions import ConfigurationError, ConnectionError
from avd_cli.utils.eapi_client import DeploymentMode, EapiClient, EapiConfig


class TestEapiConfig:
    """Test EapiConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = EapiConfig(
            host="192.168.0.10",
            username="admin",
            password="admin",
        )

        assert config.host == "192.168.0.10"
        assert config.username == "admin"
        assert config.password == "admin"
        assert config.protocol == "https"
        assert config.port == 443
        assert config.timeout == 30
        assert config.verify_ssl is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = EapiConfig(
            host="10.0.0.1",
            username="netadmin",
            password="secret",
            protocol="http",
            port=8080,
            timeout=60,
            verify_ssl=True,
        )

        assert config.host == "10.0.0.1"
        assert config.username == "netadmin"
        assert config.password == "secret"
        assert config.protocol == "http"
        assert config.port == 8080
        assert config.timeout == 60
        assert config.verify_ssl is True


class TestDeploymentMode:
    """Test DeploymentMode enum."""

    def test_mode_values(self) -> None:
        """Test deployment mode enumeration values."""
        assert DeploymentMode.REPLACE.value == "replace"
        assert DeploymentMode.MERGE.value == "merge"


@pytest.mark.asyncio
class TestEapiClient:
    """Test EapiClient class."""

    @pytest.fixture
    def config(self) -> EapiConfig:
        """Create test configuration."""
        return EapiConfig(
            host="192.168.0.10",
            username="admin",
            password="admin",
            timeout=10,
        )

    @pytest.fixture
    def mock_command_response(self) -> Dict[str, Any]:
        """Create mock command response."""
        return {
            "jsonrpc": "2.0",
            "result": [{"output": "show version output"}],
            "id": "1",
        }

    @pytest.fixture
    def mock_running_config_response(self) -> Dict[str, Any]:
        """Create mock running config response."""
        return {
            "jsonrpc": "2.0",
            "result": [
                {
                    "output": """! Command: show running-config
! device: test-device (vEOS, EOS-4.28.0F)
!
hostname test-device
!
interface Ethernet1
   description test interface
!
"""
                }
            ],
            "id": "1",
        }

    async def test_connect_success(self, config: EapiConfig) -> None:
        """Test successful connection."""
        with aioresponses() as m:
            # Mock show version command for connection test
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version info"}], "id": "1"},
                status=200,
            )

            async with EapiClient(config) as client:
                assert client._device is not None

    async def test_connect_auth_failure(self, config: EapiConfig) -> None:
        """Test connection with authentication failure."""
        with aioresponses() as m:
            # Mock 401 authentication error
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                status=401,
            )

            # Connection wraps AuthenticationError in ConnectionError
            with pytest.raises(ConnectionError, match="Authentication failed"):
                async with EapiClient(config):
                    pass

    async def test_connect_timeout(self, config: EapiConfig) -> None:
        """Test connection timeout."""
        config_short_timeout = EapiConfig(
            host="192.168.0.10",
            username="admin",
            password="admin",
            timeout=1,
        )

        with aioresponses() as m:
            # Mock timeout exception
            url = (
                f"{config_short_timeout.protocol}://{config_short_timeout.host}:"
                f"{config_short_timeout.port}/command-api"
            )
            m.post(url, exception=TimeoutError("Connection timeout"))

            with pytest.raises(ConnectionError, match="timeout"):
                async with EapiClient(config_short_timeout):
                    pass

    async def test_ssl_verification_disabled(self, config: EapiConfig) -> None:
        """Test SSL verification disabled by default."""
        assert config.verify_ssl is False

        with aioresponses() as m:
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )

            client = EapiClient(config)
            await client.connect()

            # Verify SSL context is created
            # Note: Full SSL context testing requires integration tests
            assert client._device is not None

            await client.disconnect()

    async def test_ssl_verification_enabled(self) -> None:
        """Test SSL verification enabled."""
        config = EapiConfig(
            host="192.168.0.10",
            username="admin",
            password="admin",
            verify_ssl=True,
        )

        assert config.verify_ssl is True

        with aioresponses() as m:
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )

            client = EapiClient(config)
            await client.connect()
            assert client._device is not None
            await client.disconnect()

    async def test_execute_commands_success(
        self, config: EapiConfig, mock_command_response: Dict[str, Any]
    ) -> None:
        """Test successful command execution."""
        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock command execution
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload=mock_command_response,
            )

            async with EapiClient(config) as client:
                results = await client._execute_commands(["show version"])
                assert len(results) == 1
                assert results[0]["output"] == "show version output"

    async def test_execute_commands_error(self, config: EapiConfig) -> None:
        """Test command execution with error response."""
        error_response = {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid command"},
            "id": "1",
        }

        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock command error
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload=error_response,
            )

            async with EapiClient(config) as client:
                with pytest.raises(ConfigurationError, match="Command execution failed"):
                    await client._execute_commands(["invalid command"])

    async def test_get_running_config(
        self, config: EapiConfig, mock_running_config_response: Dict[str, Any]
    ) -> None:
        """Test retrieving running configuration."""
        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock running config retrieval with enable command
            # First call returns enable response and show running-config
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable command result
                        mock_running_config_response["result"][0],  # show running-config result
                    ],
                    "id": "1",
                },
            )

            async with EapiClient(config) as client:
                running_config = await client.get_running_config()
                assert "hostname test-device" in running_config
                assert "interface Ethernet1" in running_config

    async def test_get_config_diff(self, config: EapiConfig) -> None:
        """Test configuration diff generation."""
        running_config = """hostname old-device
interface Ethernet1
   description old description
"""
        intended_config = """hostname new-device
interface Ethernet1
   description new description
"""

        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock running config with enable command
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable command result
                        {"output": running_config},  # show running-config result
                    ],
                    "id": "1",
                },
            )

            async with EapiClient(config) as client:
                diff = await client.get_config_diff(intended_config)
                assert "old-device" in diff
                assert "new-device" in diff
                assert "old description" in diff
                assert "new description" in diff

    async def test_apply_config_dry_run(self, config: EapiConfig) -> None:
        """Test apply configuration in dry-run mode."""
        intended_config = "hostname test-device\n"

        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock config session apply (step 1: enter session + rollback clean-config + apply config)
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable
                        {"output": ""},  # configure session
                        {"output": ""},  # rollback clean-config
                        {"output": ""},  # config lines
                    ],
                    "id": "1",
                },
            )
            # Mock diff retrieval (optional, for show_diff)
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable
                        {"output": ""},  # configure session
                        {
                            "output": "--- old\n+++ new\n@@ -1 +1 @@\n-hostname old-device\n+hostname test-device\n"
                        },  # show session-config diffs
                    ],
                    "id": "1",
                },
            )
            # Mock session commit/abort (step 2: re-enter session + abort for dry_run)
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable
                        {"output": ""},  # configure session
                        {"output": ""},  # abort (dry_run)
                    ],
                    "id": "1",
                },
            )

            async with EapiClient(config) as client:
                result = await client.apply_config(
                    intended_config, mode=DeploymentMode.REPLACE, dry_run=True, show_diff=True
                )

                assert result["success"] is True
                assert result["changes_applied"] is False
                assert result["diff"] is not None
                assert "hostname" in result["diff"]  # Check diff contains expected content
                assert result["error"] is None

    async def test_apply_config_replace_mode(self, config: EapiConfig) -> None:
        """Test apply configuration in replace mode."""
        intended_config = """hostname test-device
interface Ethernet1
   description test interface
"""

        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock running config for diff with enable command
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable command result
                        {"output": "hostname old-device\n"},  # show running-config result
                    ],
                    "id": "1",
                },
            )
            # Mock config application
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{}, {}, {}], "id": "1"},
            )

            async with EapiClient(config) as client:
                result = await client.apply_config(
                    intended_config, mode=DeploymentMode.REPLACE, dry_run=False
                )

                assert result["success"] is True
                assert result["changes_applied"] is True
                assert result["error"] is None

    async def test_apply_config_merge_mode(self, config: EapiConfig) -> None:
        """Test apply configuration in merge mode."""
        intended_config = """interface Ethernet2
   description new interface
"""

        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )
            # Mock running config for diff with enable command
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={
                    "jsonrpc": "2.0",
                    "result": [
                        {"output": ""},  # enable command result
                        {"output": "hostname test-device\n"},  # show running-config result
                    ],
                    "id": "1",
                },
            )
            # Mock config application
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{}, {}], "id": "1"},
            )

            async with EapiClient(config) as client:
                result = await client.apply_config(
                    intended_config, mode=DeploymentMode.MERGE, dry_run=False
                )

                assert result["success"] is True
                assert result["changes_applied"] is True

    async def test_test_connection_success(self, config: EapiConfig) -> None:
        """Test successful connection test."""
        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )

            client = EapiClient(config)
            result = await client.test_connection()
            assert result is True

    async def test_test_connection_failure(self, config: EapiConfig) -> None:
        """Test failed connection test."""
        with aioresponses() as m:
            # Mock connection failure
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                status=401,
            )

            client = EapiClient(config)
            result = await client.test_connection()
            assert result is False

    async def test_context_manager(self, config: EapiConfig) -> None:
        """Test async context manager behavior."""
        with aioresponses() as m:
            # Mock connection
            m.post(
                f"{config.protocol}://{config.host}:{config.port}/command-api",
                payload={"jsonrpc": "2.0", "result": [{"output": "version"}], "id": "1"},
            )

            async with EapiClient(config) as client:
                assert client._device is not None

            # After context exit, device should be None
            assert client._device is None
