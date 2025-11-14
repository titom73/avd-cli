#!/usr/bin/env python
# coding: utf-8
# pylint: disable=line-too-long
"""Unit tests for eAPI client utility functions.

These tests cover basic eAPI client functionality to improve coverage
of eapi_client.py.
"""

from avd_cli.utils.eapi_client import DeploymentMode, EapiConfig


def test_deployment_mode_enum_values() -> None:
    """Test DeploymentMode enum has correct values.

    Coverage: Lines covering DeploymentMode enum
    """
    assert DeploymentMode.REPLACE.value == "replace"
    assert DeploymentMode.MERGE.value == "merge"


def test_eapi_config_default_values() -> None:
    """Test EapiConfig default values.

    Coverage: Lines covering EapiConfig dataclass
    """
    config = EapiConfig(host="192.168.1.1", username="admin", password="password")

    assert config.host == "192.168.1.1"
    assert config.username == "admin"
    assert config.password == "password"
    assert config.protocol == "https"
    assert config.port == 443
    assert config.timeout == 30
    assert config.verify_ssl is False


def test_eapi_config_custom_values() -> None:
    """Test EapiConfig with custom values.

    Coverage: Lines covering EapiConfig with custom parameters
    """
    config = EapiConfig(
        host="10.0.0.1",
        username="user",
        password="pass",
        protocol="http",
        port=80,
        timeout=60,
        verify_ssl=True,
    )

    assert config.host == "10.0.0.1"
    assert config.username == "user"
    assert config.password == "pass"
    assert config.protocol == "http"
    assert config.port == 80
    assert config.timeout == 60
    assert config.verify_ssl is True


def test_eapi_config_ssl_verification_disabled_by_default() -> None:
    """Test that SSL verification is disabled by default for lab/dev friendliness.

    Coverage: Lines covering EapiConfig SSL verification default
    """
    config = EapiConfig(host="192.168.1.1", username="admin", password="password")

    assert config.verify_ssl is False


def test_deployment_mode_enum_members() -> None:
    """Test DeploymentMode enum has all expected members.

    Coverage: Lines covering DeploymentMode enum members
    """
    assert hasattr(DeploymentMode, "REPLACE")
    assert hasattr(DeploymentMode, "MERGE")
    assert len(list(DeploymentMode)) == 2
