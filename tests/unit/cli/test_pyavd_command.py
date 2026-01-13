#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for avd_cli.cli.commands.pyavd module."""

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from avd_cli.cli.main import cli


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide Click CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.mark.unit
class TestPyavdCommandGroup:
    """Tests for pyavd command group."""

    def test_pyavd_command_exists(self, cli_runner: CliRunner) -> None:
        """Verify pyavd command group is available."""
        result = cli_runner.invoke(cli, ["pyavd", "--help"])

        assert result.exit_code == 0
        assert "Manage pyavd package version" in result.output

    def test_pyavd_version_subcommand_exists(self, cli_runner: CliRunner) -> None:
        """Verify pyavd version subcommand is available."""
        result = cli_runner.invoke(cli, ["pyavd", "version"])

        assert result.exit_code == 0
        assert "pyavd version:" in result.output

    def test_pyavd_install_subcommand_exists(self, cli_runner: CliRunner) -> None:
        """Verify pyavd install subcommand is available."""
        result = cli_runner.invoke(cli, ["pyavd", "install", "--help"])

        assert result.exit_code == 0
        assert "Install a specific version of pyavd" in result.output


@pytest.mark.unit
class TestPyavdVersionCommand:
    """Tests for pyavd version command."""

    def test_version_displays_current_version(self, cli_runner: CliRunner) -> None:
        """Verify version command displays installed pyavd version."""
        result = cli_runner.invoke(cli, ["pyavd", "version"])

        assert result.exit_code == 0
        assert "pyavd version:" in result.output


@pytest.mark.unit
class TestPyavdInstallCommand:
    """Tests for pyavd install command."""

    def test_install_requires_version_argument(self, cli_runner: CliRunner) -> None:
        """Verify install command requires version argument."""
        result = cli_runner.invoke(cli, ["pyavd", "install"])

        assert result.exit_code == 2
        assert "Missing argument" in result.output

    def test_install_dry_run_does_not_execute(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify --dry-run shows command without executing."""
        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(cli, ["pyavd", "install", "5.7.0", "--dry-run"])

        mock_run.assert_not_called()
        assert result.exit_code == 0
        assert "Dry run mode" in result.output
        assert "pyavd==5.7.0" in result.output

    def test_install_dry_run_shows_pip_command(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify --dry-run with --package-manager pip shows pip command."""
        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(
            cli, ["pyavd", "install", "5.7.0", "--dry-run", "--package-manager", "pip"]
        )

        mock_run.assert_not_called()
        assert "pip install pyavd==5.7.0" in result.output

    def test_install_dry_run_shows_uv_command(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify --dry-run with --package-manager uv shows uv add for uv-managed project."""
        mock_run = mocker.patch("subprocess.run")
        mocker.patch("avd_cli.utils.package_manager.is_uv_managed_project", return_value=True)

        result = cli_runner.invoke(
            cli, ["pyavd", "install", "5.7.0", "--dry-run", "--package-manager", "uv"]
        )

        mock_run.assert_not_called()
        assert "uv add pyavd==5.7.0" in result.output

    def test_install_dry_run_shows_uv_pip_install_when_not_managed(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify --dry-run with --package-manager uv shows uv pip install when not uv-managed."""
        mock_run = mocker.patch("subprocess.run")
        mocker.patch("avd_cli.utils.package_manager.is_uv_managed_project", return_value=False)

        result = cli_runner.invoke(
            cli, ["pyavd", "install", "5.7.0", "--dry-run", "--package-manager", "uv"]
        )

        mock_run.assert_not_called()
        assert "uv pip install pyavd==5.7.0" in result.output

    def test_install_executes_with_valid_version(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify install executes subprocess for valid version."""
        mock_run = mocker.patch("subprocess.run")
        mocker.patch("shutil.which", return_value="/usr/bin/pip")

        result = cli_runner.invoke(
            cli, ["pyavd", "install", "5.7.0", "--package-manager", "pip"]
        )

        mock_run.assert_called_once()
        assert result.exit_code == 0
        assert "Successfully installed" in result.output

    def test_install_displays_error_on_failure(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Verify install displays error message on failure."""
        import subprocess

        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                returncode=1,
                cmd=["pip", "install", "pyavd==99.99.99"],
                stderr="ERROR: No matching distribution found",
            ),
        )

        result = cli_runner.invoke(
            cli, ["pyavd", "install", "99.99.99", "--package-manager", "pip"]
        )

        assert result.exit_code == 1
        assert "Failed to install" in result.output

    def test_install_package_manager_choice_validation(self, cli_runner: CliRunner) -> None:
        """Verify --package-manager only accepts valid choices."""
        result = cli_runner.invoke(
            cli, ["pyavd", "install", "5.7.0", "--package-manager", "invalid"]
        )

        assert result.exit_code == 2
        assert "Invalid value" in result.output


@pytest.mark.unit
class TestCliVersionOption:
    """Tests for --version option on main CLI."""

    def test_version_output_contains_avd_cli_version(self, cli_runner: CliRunner) -> None:
        """Verify --version shows avd-cli version."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "avd-cli" in result.output
        assert "version" in result.output

    def test_version_output_contains_pyavd_version(self, cli_runner: CliRunner) -> None:
        """Verify --version shows pyavd version."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "pyavd" in result.output

    def test_version_output_format(self, cli_runner: CliRunner) -> None:
        """Verify --version output has expected format."""
        result = cli_runner.invoke(cli, ["--version"])

        lines = result.output.strip().split("\n")
        assert len(lines) == 2
        assert "avd-cli, version" in lines[0]
        assert "pyavd, version" in lines[1]
