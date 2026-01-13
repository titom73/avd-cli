#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for avd_cli.utils.package_manager module."""

import subprocess

import pytest
from pytest_mock import MockerFixture

from avd_cli.utils.package_manager import (
    InstallResult,
    PackageManager,
    PackageManagerType,
    is_uv_managed_project,
)


@pytest.mark.unit
class TestIsUvManagedProject:
    """Tests for is_uv_managed_project function."""

    def test_returns_true_when_uv_lock_exists(self, mocker: MockerFixture) -> None:
        """Verify returns True when uv.lock file exists."""
        mocker.patch("avd_cli.utils.package_manager.Path.exists", return_value=True)

        assert is_uv_managed_project() is True

    def test_returns_false_when_uv_lock_missing(self, mocker: MockerFixture) -> None:
        """Verify returns False when uv.lock file does not exist."""
        mocker.patch("avd_cli.utils.package_manager.Path.exists", return_value=False)

        assert is_uv_managed_project() is False


@pytest.mark.unit
class TestPackageManagerDetection:
    """Tests for package manager detection."""

    def test_detect_manager_returns_uv_when_available(self, mocker: MockerFixture) -> None:
        """Verify detect_manager returns 'uv' when uv is available."""
        mocker.patch("shutil.which", side_effect=lambda cmd: "/usr/bin/uv" if cmd == "uv" else None)

        result = PackageManager.detect_manager()

        assert result == "uv"

    def test_detect_manager_returns_pip_when_uv_unavailable(self, mocker: MockerFixture) -> None:
        """Verify detect_manager returns 'pip' when only pip is available."""
        mocker.patch(
            "shutil.which",
            side_effect=lambda cmd: "/usr/bin/pip" if cmd == "pip" else None,
        )

        result = PackageManager.detect_manager()

        assert result == "pip"

    def test_detect_manager_raises_when_none_available(self, mocker: MockerFixture) -> None:
        """Verify detect_manager raises RuntimeError when no manager is available."""
        mocker.patch("shutil.which", return_value=None)

        with pytest.raises(RuntimeError, match="No package manager found"):
            PackageManager.detect_manager()


@pytest.mark.unit
class TestPackageManagerInit:
    """Tests for PackageManager initialization."""

    def test_init_with_auto_detection(self, mocker: MockerFixture) -> None:
        """Verify PackageManager auto-detects manager on first access."""
        mocker.patch("shutil.which", side_effect=lambda cmd: "/usr/bin/uv" if cmd == "uv" else None)

        pm = PackageManager(manager=PackageManagerType.AUTO)

        assert pm.manager == "uv"

    def test_init_with_explicit_pip(self) -> None:
        """Verify PackageManager uses pip when explicitly specified."""
        pm = PackageManager(manager=PackageManagerType.PIP)

        assert pm.manager == "pip"

    def test_init_with_explicit_uv(self) -> None:
        """Verify PackageManager uses uv when explicitly specified."""
        pm = PackageManager(manager=PackageManagerType.UV)

        assert pm.manager == "uv"


@pytest.mark.unit
class TestBuildInstallCommand:
    """Tests for build_install_command method."""

    def test_build_install_command_pip(self) -> None:
        """Verify pip install command construction."""
        pm = PackageManager(manager=PackageManagerType.PIP)

        command = pm.build_install_command("pyavd", "5.7.0")

        assert command == ["pip", "install", "pyavd==5.7.0"]

    def test_build_install_command_uv_not_managed(self, mocker: MockerFixture) -> None:
        """Verify uv pip install command when not in uv-managed project."""
        mocker.patch("avd_cli.utils.package_manager.is_uv_managed_project", return_value=False)
        pm = PackageManager(manager=PackageManagerType.UV)

        command = pm.build_install_command("pyavd", "5.7.0")

        assert command == ["uv", "pip", "install", "pyavd==5.7.0"]

    def test_build_install_command_uv_managed_project(self, mocker: MockerFixture) -> None:
        """Verify uv add command when in uv-managed project."""
        mocker.patch("avd_cli.utils.package_manager.is_uv_managed_project", return_value=True)
        pm = PackageManager(manager=PackageManagerType.UV)

        command = pm.build_install_command("pyavd", "5.7.0")

        assert command == ["uv", "add", "pyavd==5.7.0"]

    def test_build_install_command_with_different_versions(self) -> None:
        """Verify command handles various version formats."""
        pm = PackageManager(manager=PackageManagerType.PIP)

        for version in ["5.7.0", "5.6.0", "4.10.2", "6.0.0.dev1"]:
            command = pm.build_install_command("pyavd", version)
            assert command == ["pip", "install", f"pyavd=={version}"]


@pytest.mark.unit
class TestInstallPackage:
    """Tests for install_package method."""

    def test_install_package_dry_run_does_not_execute(self, mocker: MockerFixture) -> None:
        """Verify dry_run=True returns command without executing."""
        mock_run = mocker.patch("subprocess.run")
        pm = PackageManager(manager=PackageManagerType.PIP)

        result = pm.install_package("pyavd", "5.7.0", dry_run=True)

        mock_run.assert_not_called()
        assert result.success is True
        assert result.command == ["pip", "install", "pyavd==5.7.0"]
        assert result.package == "pyavd"
        assert result.version == "5.7.0"
        assert result.manager == "pip"

    def test_install_package_executes_subprocess(self, mocker: MockerFixture) -> None:
        """Verify install_package calls subprocess.run with correct arguments."""
        mock_run = mocker.patch("subprocess.run")
        pm = PackageManager(manager=PackageManagerType.PIP)

        result = pm.install_package("pyavd", "5.7.0")

        mock_run.assert_called_once_with(
            ["pip", "install", "pyavd==5.7.0"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.success is True

    def test_install_package_returns_success_on_success(self, mocker: MockerFixture) -> None:
        """Verify successful installation returns success result."""
        mocker.patch("subprocess.run")
        pm = PackageManager(manager=PackageManagerType.UV)

        result = pm.install_package("pyavd", "5.7.0")

        assert isinstance(result, InstallResult)
        assert result.success is True
        assert result.error_message is None

    def test_install_package_returns_failure_on_error(self, mocker: MockerFixture) -> None:
        """Verify failed installation returns failure result with error message."""
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                returncode=1,
                cmd=["pip", "install", "pyavd==99.99.99"],
                stderr="ERROR: No matching distribution found for pyavd==99.99.99",
            ),
        )
        pm = PackageManager(manager=PackageManagerType.PIP)

        result = pm.install_package("pyavd", "99.99.99")

        assert result.success is False
        assert result.error_message is not None
        assert "No matching distribution" in result.error_message


@pytest.mark.unit
class TestInstallResult:
    """Tests for InstallResult dataclass."""

    def test_install_result_success(self) -> None:
        """Verify InstallResult for successful installation."""
        result = InstallResult(
            success=True,
            package="pyavd",
            version="5.7.0",
            manager="pip",
            command=["pip", "install", "pyavd==5.7.0"],
        )

        assert result.success is True
        assert result.package == "pyavd"
        assert result.version == "5.7.0"
        assert result.manager == "pip"
        assert result.error_message is None

    def test_install_result_failure(self) -> None:
        """Verify InstallResult for failed installation."""
        result = InstallResult(
            success=False,
            package="pyavd",
            version="99.99.99",
            manager="pip",
            command=["pip", "install", "pyavd==99.99.99"],
            error_message="Version not found",
        )

        assert result.success is False
        assert result.error_message == "Version not found"
