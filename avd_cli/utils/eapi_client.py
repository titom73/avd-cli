#!/usr/bin/env python
# coding: utf-8 -*-

"""eAPI client implementation for EOS device communication.

This module provides async eAPI client for communicating with Arista EOS devices.
"""

import difflib
import json
import logging
import ssl
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import aiohttp

from avd_cli.exceptions import AuthenticationError, ConfigurationError, ConnectionError

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment mode enumeration."""

    REPLACE = "replace"
    MERGE = "merge"


@dataclass
class EapiConfig:
    """eAPI connection configuration."""

    host: str
    username: str
    password: str
    protocol: str = "https"
    port: int = 443
    timeout: int = 30
    verify_ssl: bool = False  # SSL verification disabled by default (lab/dev friendly)


class EapiClient:
    """Async eAPI client for Arista EOS devices.

    This client uses aioeapi library for async communication with EOS devices.

    Examples
    --------
    >>> config = EapiConfig(host="192.168.0.10", username="admin", password="admin")
    >>> async with EapiClient(config) as client:
    ...     running_config = await client.get_running_config()
    """

    def __init__(self, config: EapiConfig) -> None:
        """Initialize eAPI client.

        Parameters
        ----------
        config : EapiConfig
            eAPI connection configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._device: Any = None

    async def __aenter__(self) -> "EapiClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to device.

        Raises
        ------
        ConnectionError
            If connection cannot be established
        AuthenticationError
            If authentication fails
        """
        try:
            # Create SSL context
            ssl_context: Any
            if self.config.verify_ssl:
                ssl_context = ssl.create_default_context()
            else:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            # Create aiohttp session
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            self._device = aiohttp.ClientSession(
                auth=auth,
                timeout=timeout,
                connector=aiohttp.TCPConnector(ssl=ssl_context),
            )

            # Test connection with show version
            await self._execute_commands(["show version"])
            self.logger.debug("Connected to %s", self.config.host)

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError(
                    f"Authentication failed for {self.config.host}"
                ) from e
            raise ConnectionError(
                f"Failed to connect to {self.config.host}:{self.config.port}: HTTP {e.status}"
            ) from e
        except Exception as e:
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise ConnectionError(
                    f"Connection timeout to {self.config.host}:{self.config.port} after "
                    f"{self.config.timeout}s"
                ) from e
            raise ConnectionError(
                f"Failed to connect to {self.config.host}:{self.config.port}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Close connection to device."""
        if self._device:
            await self._device.close()
            self._device = None
            self.logger.debug("Disconnected from %s", self.config.host)

    async def _execute_commands(self, commands: list[str]) -> list[Dict[str, Any]]:
        """Execute commands via eAPI.

        Parameters
        ----------
        commands : list[str]
            List of CLI commands to execute

        Returns
        -------
        list[Dict[str, Any]]
            List of command results

        Raises
        ------
        ConnectionError
            If device is not connected
        ConfigurationError
            If command execution fails
        """
        if not self._device:
            raise ConnectionError("Not connected to device")

        url = f"{self.config.protocol}://{self.config.host}:{self.config.port}/command-api"

        payload = {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {"version": 1, "cmds": commands, "format": "text"},
            "id": "1",
        }

        try:
            async with self._device.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()

                if "error" in data:
                    error = data["error"]
                    raise ConfigurationError(
                        f"Command execution failed: {error.get('message', str(error))}"
                    )

                result: list[Dict[str, Any]] = data.get("result", [])
                return result

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError(
                    f"Authentication failed for {self.config.host}"
                ) from e
            raise ConnectionError(f"HTTP error: {e.status}") from e
        except json.JSONDecodeError as e:
            raise ConnectionError("Invalid JSON response from device") from e

    async def get_running_config(self) -> str:
        """Retrieve running configuration.

        Returns
        -------
        str
            Current running configuration as text

        Raises
        ------
        ConnectionError
            If device is not connected
        """
        # Try with enable mode first (some devices require privileged mode)
        try:
            results = await self._execute_commands(["enable", "show running-config"])
            if results and len(results) > 1:
                # Second result is the show running-config output
                output: str = results[1].get("output", "")
                return output
        except ConfigurationError:
            # If enable fails, try without it
            results = await self._execute_commands(["show running-config"])
            if results and len(results) > 0:
                output = results[0].get("output", "")
                return output
        return ""

    async def get_config_diff(
        self, intended_config: str, mode: DeploymentMode = DeploymentMode.REPLACE
    ) -> str:
        """Generate configuration diff.

        Parameters
        ----------
        intended_config : str
            Target configuration content
        mode : DeploymentMode
            Deployment mode (replace or merge)

        Returns
        -------
        str
            Unified diff between running and intended config
        """
        running_config = await self.get_running_config()

        # Generate unified diff
        running_lines = running_config.splitlines(keepends=True)
        intended_lines = intended_config.splitlines(keepends=True)

        diff = difflib.unified_diff(
            running_lines,
            intended_lines,
            fromfile="running-config",
            tofile="intended-config",
            lineterm="",
        )

        return "\n".join(diff)

    async def apply_config(
        self,
        intended_config: str,
        mode: DeploymentMode = DeploymentMode.REPLACE,
        dry_run: bool = False,
        show_diff: bool = False,
    ) -> Dict[str, Any]:
        """Apply configuration to device via eAPI using config sessions.

        This method uses EOS config sessions to provide atomic commit/rollback
        capability and validates configuration syntax before applying changes.

        Note: Config sessions perform MERGE operations (new config is added/updated,
        nothing is removed). True "replace" mode (removing old config) requires
        file-based workflows which are not supported via eAPI.

        Parameters
        ----------
        intended_config : str
            Configuration content to apply (will be merged with existing config)
        mode : DeploymentMode
            Deployment mode (currently only REPLACE with config sessions is supported)
        dry_run : bool
            If True, validate only without applying changes
        show_diff : bool
            If True, return the configuration diff from the session

        Returns
        -------
        Dict[str, Any]
            Result dict with keys: success (bool), diff (str | None), error (Optional[str])

        Raises
        ------
        ConfigurationError
            If configuration is invalid or application fails
        ConnectionError
            If device is not connected
        """
        try:
            # Always use config session for atomic commit with validation
            # Get diff from session if requested (works in both dry_run and normal mode)
            diff = await self._apply_config_session(
                intended_config,
                dry_run=dry_run,
                show_diff=show_diff
            )

            return {
                "success": True,
                "diff": diff,
                "error": None,
                "changes_applied": not dry_run,
            }

        except Exception as e:
            error_msg = str(e)
            raise ConfigurationError(
                f"Configuration validation failed: {error_msg}"
            ) from e

    async def _apply_config_session(  # noqa: C901
        self, config: str, dry_run: bool = False, show_diff: bool = False
    ) -> Optional[str]:
        """Apply configuration using config session with validation and full replacement.

        This method uses EOS config sessions with 'rollback clean-config' to perform
        a TRUE REPLACE operation that removes all existing configuration before
        applying the new configuration.

        **CRITICAL**: The provided configuration must be COMPLETE, including:
        - Management API configuration (management api http-commands)
        - User accounts with credentials
        - AAA configuration
        - Any other essential configuration for device access

        Failure to include management configuration will result in loss of device access!

        Parameters
        ----------
        config : str
            **COMPLETE** configuration text to apply (replaces all existing config)
        dry_run : bool, optional
            If True, validate config but don't commit (abort session)
        show_diff : bool, optional
            If True, return the configuration diff from the session

        Returns
        -------
        str | None
            Configuration diff if show_diff=True, None otherwise

        Raises
        ------
        ConnectionError
            If device is not connected
        ConfigurationError
            If configuration validation or application fails
        """
        if not self._device:
            raise ConnectionError("Not connected to device")

        try:
            # Generate unique session name
            import time
            session_name = f"avd_cli_{int(time.time())}"

            url = f"{self.config.protocol}://{self.config.host}:{self.config.port}/command-api"

            # Use config session for atomic, validated commit with rollback capability
            # Critical: EOS sessions require TWO separate eAPI requests:
            # 1. Enter session, apply 'rollback clean-config' (REPLACE), then apply config lines
            # 2. Re-enter session and commit
            # This is because after sending many config lines, the session context
            # is lost, and "commit" as the last command in the same request fails.

            # REPLACE mode: 'rollback clean-config' removes ALL existing configuration
            # before applying the new config. This ensures deletions are properly
            # reflected. The provided configuration MUST be complete including
            # management sections (users, api, aaa) to maintain device access.

            # Step 1: Enter session, apply rollback clean-config for TRUE REPLACE, then apply all config lines
            cmds_config = ["enable", f"configure session {session_name}", "rollback clean-config"]

            # Add each config line, filtering out empty lines and standalone keywords
            # that require arguments (common AVD generation issues)
            if config:
                for line in config.strip().split('\n'):
                    # Skip empty lines
                    if not line.strip():
                        continue

                    # Skip lines that are just "hostname", "description", etc without values
                    # These are invalid and will cause session failures
                    stripped = line.strip()
                    if stripped in ['hostname', 'description', 'name']:
                        continue

                    cmds_config.append(line)

            # Apply config to session
            payload_config = {
                "jsonrpc": "2.0",
                "method": "runCmds",
                "params": {
                    "version": 1,
                    "cmds": cmds_config,
                    "format": "text"
                },
                "id": "1",
            }

            async with self._device.post(url, json=payload_config) as response:
                response.raise_for_status()
                data = await response.json()

                if "error" in data:
                    error = data["error"]
                    # Try to abort the session
                    try:
                        abort_payload = {
                            "jsonrpc": "2.0",
                            "method": "runCmds",
                            "params": {
                                "version": 1,
                                "cmds": [
                                    "enable",
                                    f"configure session {session_name}",
                                    "abort"
                                ],
                                "format": "text"
                            },
                            "id": "1",
                        }
                        async with self._device.post(url, json=abort_payload):
                            pass  # Best effort abort
                    except Exception:
                        pass  # Ignore abort failures

                    raise ConfigurationError(
                        f"Configuration validation failed: {error.get('message', str(error))}"
                    )

            # Step 1.5: Get diff if requested (before commit/abort)
            diff_text = None
            if show_diff:
                cmds_diff = ["enable", f"configure session {session_name}", "show session-config diffs"]
                payload_diff = {
                    "jsonrpc": "2.0",
                    "method": "runCmds",
                    "params": {
                        "version": 1,
                        "cmds": cmds_diff,
                        "format": "text"
                    },
                    "id": "1",
                }

                async with self._device.post(url, json=payload_diff) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if "result" in data and len(data["result"]) > 2:
                        diff_text = data["result"][2].get("output", "")

            # Step 2: Re-enter session and commit (or abort if dry_run)
            final_action = "abort" if dry_run else "commit"
            cmds_commit = ["enable", f"configure session {session_name}", final_action]

            payload_commit = {
                "jsonrpc": "2.0",
                "method": "runCmds",
                "params": {
                    "version": 1,
                    "cmds": cmds_commit,
                    "format": "text"
                },
                "id": "1",
            }

            async with self._device.post(url, json=payload_commit) as response:
                response.raise_for_status()
                data = await response.json()

                if "error" in data:
                    error = data["error"]
                    # Try to abort the session
                    try:
                        abort_payload = {
                            "jsonrpc": "2.0",
                            "method": "runCmds",
                            "params": {
                                "version": 1,
                                "cmds": [
                                    "enable",
                                    f"configure session {session_name}",
                                    "abort"
                                ],
                                "format": "text"
                            },
                            "id": "1",
                        }
                        async with self._device.post(url, json=abort_payload):
                            pass  # Best effort abort
                    except Exception:
                        pass  # Ignore abort failures

                    raise ConfigurationError(
                        f"Commit failed: {error.get('message', str(error))}"
                    )

            return diff_text

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError(
                    f"Authentication failed for {self.config.host}"
                ) from e
            raise ConnectionError(f"HTTP error: {e.status}") from e
        except json.JSONDecodeError as e:
            raise ConnectionError("Invalid JSON response from device") from e

    async def test_connection(self) -> bool:
        """Test connection to device.

        Returns
        -------
        bool
            True if connection successful
        """
        try:
            await self.connect()
            await self.disconnect()
            return True
        except (ConnectionError, AuthenticationError):
            return False
