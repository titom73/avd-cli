#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for constants module."""
import pytest
from pathlib import Path

from avd_cli.constants import (
    APP_NAME,
    APP_DESCRIPTION,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_CONFIGS_DIR,
    DEFAULT_DOCS_DIR,
    DEFAULT_TESTS_DIR,
    WORKFLOW_MODE_EOS_DESIGN,
    WORKFLOW_MODE_CLI_CONFIG,
    WORKFLOW_MODE_FULL,
    WORKFLOW_MODE_CONFIG_ONLY,
    EXIT_SUCCESS,
    EXIT_VALIDATION_ERROR,
    EXIT_GENERATION_ERROR,
    normalize_workflow,
)


class TestApplicationMetadata:
    """Test cases for application metadata constants."""

    def test_app_name_is_string(self) -> None:
        """Test APP_NAME is a non-empty string."""
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0

    def test_app_description_is_string(self) -> None:
        """Test APP_DESCRIPTION is a non-empty string."""
        assert isinstance(APP_DESCRIPTION, str)
        assert len(APP_DESCRIPTION) > 0


class TestDefaultPaths:
    """Test cases for default path constants."""

    def test_default_output_dir_is_path(self) -> None:
        """Test DEFAULT_OUTPUT_DIR is a Path object."""
        assert isinstance(DEFAULT_OUTPUT_DIR, Path)

    def test_default_subdirs_are_strings(self) -> None:
        """Test subdirectory constants are non-empty strings."""
        assert isinstance(DEFAULT_CONFIGS_DIR, str) and len(DEFAULT_CONFIGS_DIR) > 0
        assert isinstance(DEFAULT_DOCS_DIR, str) and len(DEFAULT_DOCS_DIR) > 0
        assert isinstance(DEFAULT_TESTS_DIR, str) and len(DEFAULT_TESTS_DIR) > 0


class TestWorkflowModes:
    """Test cases for workflow mode constants."""

    def test_workflow_modes_are_strings(self) -> None:
        """Test workflow mode constants are non-empty strings."""
        assert isinstance(WORKFLOW_MODE_EOS_DESIGN, str)
        assert isinstance(WORKFLOW_MODE_CLI_CONFIG, str)
        assert isinstance(WORKFLOW_MODE_FULL, str)
        assert isinstance(WORKFLOW_MODE_CONFIG_ONLY, str)

    def test_workflow_modes_are_distinct(self) -> None:
        """Test workflow modes have unique values."""
        modes = [
            WORKFLOW_MODE_EOS_DESIGN,
            WORKFLOW_MODE_CLI_CONFIG,
            WORKFLOW_MODE_FULL,
            WORKFLOW_MODE_CONFIG_ONLY,
        ]
        assert len(modes) == len(set(modes)), "Workflow modes should be unique"


class TestExitCodes:
    """Test cases for exit code constants."""

    def test_exit_success_is_zero(self) -> None:
        """Test EXIT_SUCCESS is 0."""
        assert EXIT_SUCCESS == 0

    def test_error_codes_are_nonzero(self) -> None:
        """Test error exit codes are non-zero."""
        assert EXIT_VALIDATION_ERROR != 0
        assert EXIT_GENERATION_ERROR != 0

    def test_exit_codes_are_distinct(self) -> None:
        """Test exit codes have unique values."""
        codes = [EXIT_SUCCESS, EXIT_VALIDATION_ERROR, EXIT_GENERATION_ERROR]
        assert len(codes) == len(set(codes)), "Exit codes should be unique"


class TestNormalizeWorkflow:
    """Test cases for workflow normalization function."""

    @pytest.mark.parametrize(
        "input_workflow,expected",
        [
            # Deprecated values should be normalized
            ("full", "eos-design"),
            ("config-only", "cli-config"),
            # Current values should pass through unchanged
            ("eos-design", "eos-design"),
            ("cli-config", "cli-config"),
            # Unknown values should pass through unchanged
            ("custom-workflow", "custom-workflow"),
            ("unknown", "unknown"),
        ],
    )
    def test_normalize_known_workflows(self, input_workflow: str, expected: str) -> None:
        """Test normalization of workflow values."""
        assert normalize_workflow(input_workflow) == expected

    def test_normalize_preserves_case(self) -> None:
        """Test that normalization is case-sensitive."""
        # "Full" (capital F) should not match "full"
        assert normalize_workflow("Full") == "Full"
        assert normalize_workflow("FULL") == "FULL"

    def test_normalize_unknown_workflow_returns_input(self) -> None:
        """Test that unknown workflows are returned unchanged."""
        unknown = "my-custom-workflow"
        assert normalize_workflow(unknown) == unknown

    def test_normalize_empty_string(self) -> None:
        """Test normalization of empty string."""
        assert normalize_workflow("") == ""

    def test_normalize_with_hyphens_and_underscores(self) -> None:
        """Test workflows with various separators."""
        # Only exact matches should be normalized
        assert normalize_workflow("eos_design") == "eos_design"  # Not normalized
        assert normalize_workflow("eos-design") == "eos-design"  # Pass through


class TestWorkflowMapping:
    """Test cases for workflow backward compatibility mapping."""

    def test_deprecated_full_maps_to_eos_design(self) -> None:
        """Test deprecated 'full' maps to current 'eos-design'."""
        result = normalize_workflow(WORKFLOW_MODE_FULL)
        assert result == WORKFLOW_MODE_EOS_DESIGN

    def test_deprecated_config_only_maps_to_cli_config(self) -> None:
        """Test deprecated 'config-only' maps to current 'cli-config'."""
        result = normalize_workflow(WORKFLOW_MODE_CONFIG_ONLY)
        assert result == WORKFLOW_MODE_CLI_CONFIG

    def test_current_modes_unchanged(self) -> None:
        """Test current workflow modes are not modified."""
        assert normalize_workflow(WORKFLOW_MODE_EOS_DESIGN) == WORKFLOW_MODE_EOS_DESIGN
        assert normalize_workflow(WORKFLOW_MODE_CLI_CONFIG) == WORKFLOW_MODE_CLI_CONFIG
