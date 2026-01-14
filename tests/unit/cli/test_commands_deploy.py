"""Unit tests for deploy command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch, AsyncMock

from avd_cli.cli.commands.deploy import deploy, deploy_eos


class TestDeployCommand:
    """Test cases for deploy command group."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_deploy_group_help(self, runner: CliRunner) -> None:
        """Test deploy group shows help."""
        result = runner.invoke(deploy, ["--help"])
        assert result.exit_code == 0
        assert "Deploy configurations" in result.output

    def test_deploy_eos_help(self, runner: CliRunner) -> None:
        """Test deploy eos shows help."""
        result = runner.invoke(deploy, ["eos", "--help"])
        assert result.exit_code == 0
        assert "--inventory-path" in result.output
        assert "--dry-run" in result.output

    @patch("avd_cli.logics.deployer.Deployer")
    @patch("avd_cli.cli.commands.deploy.asyncio.run")
    def test_deploy_eos_dry_run(
        self,
        mock_asyncio_run: MagicMock,
        mock_deployer_class: MagicMock,
        runner: CliRunner,
        tmp_path,
    ) -> None:
        """Test deploy eos with dry-run flag."""
        # Setup
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()
        configs_path = inventory_path / "intended" / "configs"
        configs_path.mkdir(parents=True)

        mock_deployer = MagicMock()
        mock_deployer_class.return_value = mock_deployer
        mock_asyncio_run.return_value = []

        result = runner.invoke(
            deploy,
            ["eos", "--inventory-path", str(inventory_path), "--dry-run"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0
        mock_deployer_class.assert_called_once()
        assert mock_deployer_class.call_args.kwargs["dry_run"] is True
