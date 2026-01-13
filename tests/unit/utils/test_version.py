#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for avd_cli.utils.version module."""

import pytest
from pytest_mock import MockerFixture


@pytest.mark.unit
class TestGetPyavdVersion:
    """Tests for get_pyavd_version function."""

    def test_get_pyavd_version_returns_valid_string(self) -> None:
        """Verify get_pyavd_version returns a valid version string."""
        from avd_cli.utils.version import get_pyavd_version

        version = get_pyavd_version()

        assert isinstance(version, str)
        assert version not in ("not installed",)
        # pyavd is installed, should return actual version like "5.7.2"
        assert len(version) > 0

    def test_get_pyavd_version_handles_import_error(self, mocker: MockerFixture) -> None:
        """Verify returns 'not installed' when pyavd cannot be imported."""
        # Mock the import to fail
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "pyavd":
                raise ImportError("No module named 'pyavd'")
            return original_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=mock_import)

        # Need to reimport the function to test with the mock
        import importlib
        import avd_cli.utils.version as version_module
        importlib.reload(version_module)

        version = version_module.get_pyavd_version()
        assert version == "not installed"

        # Restore the module
        importlib.reload(version_module)

    def test_get_pyavd_version_handles_missing_attribute(self, mocker: MockerFixture) -> None:
        """Verify returns 'unknown' when pyavd has no __version__ attribute."""
        # Create a mock module without __version__
        mock_pyavd = type("MockPyavd", (), {})()

        mocker.patch.dict("sys.modules", {"pyavd": mock_pyavd})

        import importlib
        import avd_cli.utils.version as version_module
        importlib.reload(version_module)

        version = version_module.get_pyavd_version()
        assert version == "unknown"

        # Restore by removing from sys.modules and reloading
        import sys
        if "pyavd" in sys.modules:
            del sys.modules["pyavd"]
        importlib.reload(version_module)


@pytest.mark.unit
class TestGetAvdCliVersion:
    """Tests for get_avd_cli_version function."""

    def test_get_avd_cli_version_returns_string(self) -> None:
        """Verify get_avd_cli_version returns a version string."""
        from avd_cli.utils.version import get_avd_cli_version

        version = get_avd_cli_version()

        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_avd_cli_version_matches_package_version(self) -> None:
        """Verify get_avd_cli_version matches avd_cli.__version__."""
        from avd_cli import __version__
        from avd_cli.utils.version import get_avd_cli_version

        version = get_avd_cli_version()

        assert version == __version__
