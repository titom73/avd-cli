#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for deep_merge utility."""
import pytest
from avd_cli.utils.merge import deep_merge


class TestDeepMerge:
    """Test cases for deep_merge function."""

    def test_deep_merge_flat_dicts(self) -> None:
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested_dicts(self) -> None:
        """Test merging nested dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"d": 4, "e": 5}, "f": 6}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}

    def test_deep_merge_list_replacement(self) -> None:
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = deep_merge(base, override)
        assert result == {"items": [4, 5]}

    def test_deep_merge_does_not_mutate_inputs(self) -> None:
        """Test that original dicts are not modified."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert base == {"a": {"b": 1}}
        assert override == {"a": {"c": 2}}

    def test_deep_merge_empty_base(self) -> None:
        """Test merging into empty base."""
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_deep_merge_empty_override(self) -> None:
        """Test merging empty override."""
        result = deep_merge({"a": 1}, {})
        assert result == {"a": 1}
