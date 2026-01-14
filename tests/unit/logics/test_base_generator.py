#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for BaseGenerator abstract class."""
import pytest

from avd_cli.logics.base_generator import BaseGenerator


class TestBaseGenerator:
    """Test cases for BaseGenerator abstract class."""

    def test_base_generator_is_abstract(self) -> None:
        """Test that BaseGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseGenerator()  # type: ignore[abstract]

    def test_base_generator_requires_generate_method(self) -> None:
        """Test that subclasses must implement generate() method."""

        class IncompleteGenerator(BaseGenerator):
            """Incomplete generator missing generate method."""

            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteGenerator()  # type: ignore[abstract]

    def test_base_generator_can_be_subclassed(self) -> None:
        """Test that BaseGenerator can be properly subclassed."""
        from pathlib import Path
        from typing import List, Optional

        class CompleteGenerator(BaseGenerator):
            """Complete generator with all required methods."""

            def generate(
                self,
                inventory,
                output_path: Path,
                device_filter=None,
            ) -> List[Path]:
                """Implementation of generate method."""
                return []

        # Should not raise
        generator = CompleteGenerator()
        assert isinstance(generator, BaseGenerator)
