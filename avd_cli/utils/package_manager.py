#!/usr/bin/env python
# coding: utf-8 -*-

"""Package manager utilities for installing Python packages."""

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class PackageManagerType(str, Enum):
    """Supported package manager types."""

    PIP = "pip"
    UV = "uv"
    AUTO = "auto"


def is_uv_managed_project() -> bool:
    """Check if the current directory is a uv-managed project.

    A project is considered uv-managed if it has a uv.lock file,
    indicating that uv manages the dependencies.

    Returns
    -------
    bool
        True if the project is uv-managed, False otherwise.
    """
    return Path("uv.lock").exists()


@dataclass
class InstallResult:
    """Result of a package installation operation."""

    success: bool
    package: str
    version: str
    manager: str
    command: List[str]
    error_message: Optional[str] = None


class PackageManager:
    """Manages Python package installation using pip or uv."""

    def __init__(self, manager: PackageManagerType = PackageManagerType.AUTO) -> None:
        """Initialize PackageManager.

        Parameters
        ----------
        manager : PackageManagerType
            The package manager to use. If AUTO, will detect available manager.
        """
        self._manager = manager
        self._resolved_manager: Optional[str] = None

    @staticmethod
    def detect_manager() -> str:
        """Detect available package manager.

        Prefers uv over pip if both are available.

        Returns
        -------
        str
            The detected package manager name ("uv" or "pip").

        Raises
        ------
        RuntimeError
            If no package manager is available.
        """
        if shutil.which("uv"):
            return "uv"
        if shutil.which("pip"):
            return "pip"
        raise RuntimeError(
            "No package manager found. Please install 'uv' or 'pip' and ensure it is in your PATH."
        )

    @property
    def manager(self) -> str:
        """Get the resolved package manager name.

        Returns
        -------
        str
            The package manager name ("uv" or "pip").
        """
        if self._resolved_manager is None:
            if self._manager == PackageManagerType.AUTO:
                self._resolved_manager = self.detect_manager()
            else:
                self._resolved_manager = self._manager.value
        return self._resolved_manager

    def build_install_command(self, package: str, version: str) -> List[str]:
        """Build the installation command for a package.

        For uv-managed projects (with uv.lock), uses 'uv add' to properly
        update pyproject.toml and uv.lock. Otherwise uses 'uv pip install'
        or 'pip install'.

        Parameters
        ----------
        package : str
            The package name to install.
        version : str
            The version to install.

        Returns
        -------
        List[str]
            The command arguments as a list.
        """
        package_spec = f"{package}=={version}"

        if self.manager == "uv":
            if is_uv_managed_project():
                return ["uv", "add", package_spec]
            return ["uv", "pip", "install", package_spec]
        return ["pip", "install", package_spec]

    def install_package(
        self,
        package: str,
        version: str,
        dry_run: bool = False,
    ) -> InstallResult:
        """Install a Python package at a specific version.

        Parameters
        ----------
        package : str
            The package name to install.
        version : str
            The version to install.
        dry_run : bool, optional
            If True, only return the command without executing, by default False.

        Returns
        -------
        InstallResult
            The result of the installation operation.

        Raises
        ------
        subprocess.CalledProcessError
            If the installation command fails and dry_run is False.
        """
        command = self.build_install_command(package, version)

        if dry_run:
            return InstallResult(
                success=True,
                package=package,
                version=version,
                manager=self.manager,
                command=command,
            )

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            return InstallResult(
                success=True,
                package=package,
                version=version,
                manager=self.manager,
                command=command,
            )
        except subprocess.CalledProcessError as exc:
            return InstallResult(
                success=False,
                package=package,
                version=version,
                manager=self.manager,
                command=command,
                error_message=exc.stderr or str(exc),
            )
