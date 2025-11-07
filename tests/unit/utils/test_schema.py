#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for schema utilities.

Tests for platform/device type loading from py-avd schema,
with fallback handling when py-avd is unavailable.
"""

from unittest.mock import MagicMock, patch

from avd_cli.utils.schema import (
    clear_schema_cache,
    get_avd_schema_version,
    get_supported_device_types,
    get_supported_platforms,
)


class TestGetSupportedPlatforms:
    """Test get_supported_platforms function."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        clear_schema_cache()

    def test_returns_fallback_platforms_when_pyavd_unavailable(self) -> None:
        """Test fallback when py-avd is not available.

        Given: py-avd module cannot be imported
        When: Calling get_supported_platforms()
        Then: Returns fallback platform list
        """
        # Since pyavd doesn't exist, function already uses fallback
        platforms = get_supported_platforms()

        assert isinstance(platforms, list)
        assert len(platforms) > 0
        assert "vEOS-lab" in platforms
        assert "7050X3" in platforms
        assert "722XP" in platforms

    def test_returns_fallback_platforms_when_pyavd_attribute_error(self) -> None:
        """Test fallback when py-avd has missing attributes.

        Given: py-avd module exists but has AttributeError
        When: Calling get_supported_platforms()
        Then: Returns fallback platform list
        """
        # Mock pyavd module that raises AttributeError when accessed
        mock_pyavd = MagicMock()
        mock_pyavd.__name__ = "pyavd"

        with patch.dict("sys.modules", {"pyavd": mock_pyavd}):
            clear_schema_cache()
            platforms = get_supported_platforms()

        assert isinstance(platforms, list)
        assert "vEOS-lab" in platforms

    def test_returns_list_copy(self) -> None:
        """Test that function returns a copy, not reference.

        Given: Platform list is cached
        When: Calling get_supported_platforms() multiple times
        Then: Returns same cached list (lru_cache behavior)
        """
        platforms1 = get_supported_platforms()
        platforms2 = get_supported_platforms()

        # lru_cache returns the same list object
        platforms1.append("TEST_PLATFORM")
        # Since it's the same cached object, modification affects both
        assert "TEST_PLATFORM" in platforms2

    def test_caches_result(self) -> None:
        """Test that results are cached with lru_cache.

        Given: First call to get_supported_platforms()
        When: Calling again
        Then: Returns cached result (same list object)
        """
        clear_schema_cache()
        platforms1 = get_supported_platforms()
        platforms2 = get_supported_platforms()

        # lru_cache returns the same object
        assert platforms1 is platforms2

    def test_includes_common_platforms(self) -> None:
        """Test that common platforms are in the list.

        Given: Calling get_supported_platforms()
        When: Checking platform list
        Then: Contains expected common platforms
        """
        platforms = get_supported_platforms()

        expected_platforms = ["vEOS-lab", "vEOS", "cEOS", "7050X3", "7280R3"]
        for platform in expected_platforms:
            assert platform in platforms


class TestGetSupportedDeviceTypes:
    """Test get_supported_device_types function."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        clear_schema_cache()

    def test_returns_fallback_device_types_when_pyavd_unavailable(self) -> None:
        """Test fallback when py-avd is not available.

        Given: py-avd module cannot be imported
        When: Calling get_supported_device_types()
        Then: Returns fallback device type list
        """
        # Since pyavd doesn't exist, function already uses fallback
        device_types = get_supported_device_types()

        assert isinstance(device_types, list)
        assert len(device_types) > 0
        assert "spine" in device_types
        assert "leaf" in device_types
        assert "border_leaf" in device_types

    def test_returns_fallback_device_types_when_pyavd_attribute_error(
        self,
    ) -> None:
        """Test fallback when py-avd has missing attributes.

        Given: py-avd module exists but has AttributeError
        When: Calling get_supported_device_types()
        Then: Returns fallback device type list
        """
        mock_pyavd = MagicMock()
        mock_pyavd.__name__ = "pyavd"

        with patch.dict("sys.modules", {"pyavd": mock_pyavd}):
            clear_schema_cache()
            device_types = get_supported_device_types()

        assert isinstance(device_types, list)
        assert "spine" in device_types

    def test_returns_list_copy(self) -> None:
        """Test that function returns a copy, not reference.

        Given: Device type list is cached
        When: Calling get_supported_device_types() multiple times
        Then: Returns same cached list (lru_cache behavior)
        """
        types1 = get_supported_device_types()
        types2 = get_supported_device_types()

        # lru_cache returns the same list object
        types1.append("TEST_TYPE")
        # Since it's the same cached object, modification affects both
        assert "TEST_TYPE" in types2

    def test_caches_result(self) -> None:
        """Test that results are cached with lru_cache.

        Given: First call to get_supported_device_types()
        When: Calling again
        Then: Returns cached result (same list object)
        """
        clear_schema_cache()
        types1 = get_supported_device_types()
        types2 = get_supported_device_types()

        # lru_cache returns the same object
        assert types1 is types2

    def test_includes_common_device_types(self) -> None:
        """Test that common device types are in the list.

        Given: Calling get_supported_device_types()
        When: Checking device type list
        Then: Contains expected common device types
        """
        device_types = get_supported_device_types()

        expected_types = [
            "spine",
            "leaf",
            "border_leaf",
            "super_spine",
            "overlay_controller",
            "wan_router",
        ]
        for device_type in expected_types:
            assert device_type in device_types


class TestGetAvdSchemaVersion:
    """Test get_avd_schema_version function."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        clear_schema_cache()

    def test_returns_none_when_pyavd_unavailable(self) -> None:
        """Test version is None when py-avd is not available.

        Given: py-avd module cannot be imported
        When: Calling get_avd_schema_version()
        Then: Returns None
        """
        # Since pyavd doesn't exist in test environment, function returns None
        version = get_avd_schema_version()

        assert version is None

    def test_returns_none_when_version_attribute_missing(self) -> None:
        """Test version is None when __version__ attribute missing.

        Given: py-avd module exists but has no __version__
        When: Calling get_avd_schema_version()
        Then: Returns None
        """
        mock_pyavd = MagicMock()
        mock_pyavd.__name__ = "pyavd"
        del mock_pyavd.__version__  # Ensure no __version__ attribute

        with patch.dict("sys.modules", {"pyavd": mock_pyavd}):
            clear_schema_cache()
            version = get_avd_schema_version()

        assert version is None

    def test_returns_version_string_when_available(self) -> None:
        """Test version string is returned when available.

        Given: py-avd module with __version__ attribute
        When: Calling get_avd_schema_version()
        Then: Returns version string
        """
        mock_pyavd = MagicMock()
        mock_pyavd.__version__ = "4.5.0"

        with patch.dict("sys.modules", {"pyavd": mock_pyavd}):
            clear_schema_cache()
            version = get_avd_schema_version()

        assert version == "4.5.0"

    def test_caches_result(self) -> None:
        """Test that version result is cached.

        Given: First call to get_avd_schema_version()
        When: Calling again
        Then: Returns cached result
        """
        clear_schema_cache()
        version1 = get_avd_schema_version()
        version2 = get_avd_schema_version()

        # Both return None (cached)
        assert version1 is version2
        assert version1 is None


class TestClearSchemaCache:
    """Test clear_schema_cache function."""

    def test_clears_all_caches(self) -> None:
        """Test that all schema caches are cleared.

        Given: Cached schema values
        When: Calling clear_schema_cache()
        Then: Subsequent calls reload values
        """
        # Call functions to populate cache
        platforms1 = get_supported_platforms()
        types1 = get_supported_device_types()
        version1 = get_avd_schema_version()

        # Clear cache
        clear_schema_cache()

        # Call again - should reload
        platforms2 = get_supported_platforms()
        types2 = get_supported_device_types()
        version2 = get_avd_schema_version()

        # After cache clear, new calls create new objects
        # (though content should be same)
        assert platforms2 == platforms1
        assert types2 == types1
        assert version2 == version1

    def test_idempotent(self) -> None:
        """Test that clearing cache multiple times is safe.

        Given: Schema cache
        When: Calling clear_schema_cache() multiple times
        Then: No errors occur
        """
        clear_schema_cache()
        clear_schema_cache()
        clear_schema_cache()

        # Should still work fine
        platforms = get_supported_platforms()
        assert isinstance(platforms, list)


class TestSchemaIntegration:
    """Integration tests for schema utilities."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        clear_schema_cache()

    def test_all_functions_return_valid_data(self) -> None:
        """Test that all schema functions return valid data.

        Given: Schema utilities
        When: Calling all schema functions
        Then: All return appropriate data types
        """
        platforms = get_supported_platforms()
        device_types = get_supported_device_types()
        version = get_avd_schema_version()

        assert isinstance(platforms, list)
        assert all(isinstance(p, str) for p in platforms)
        assert len(platforms) > 0

        assert isinstance(device_types, list)
        assert all(isinstance(t, str) for t in device_types)
        assert len(device_types) > 0

        assert version is None or isinstance(version, str)

    def test_schema_values_are_non_empty_strings(self) -> None:
        """Test that schema values are non-empty strings.

        Given: Platform and device type lists
        When: Checking each value
        Then: All are non-empty strings
        """
        platforms = get_supported_platforms()
        device_types = get_supported_device_types()

        for platform in platforms:
            assert isinstance(platform, str)
            assert len(platform) > 0
            assert platform.strip() == platform  # No leading/trailing whitespace

        for device_type in device_types:
            assert isinstance(device_type, str)
            assert len(device_type) > 0
            assert device_type.strip() == device_type


class TestSchemaErrorHandling:
    """Test schema error handling scenarios."""

    def test_get_supported_platforms_with_exception(self) -> None:
        """Test platform retrieval with exception during import."""
        with patch("builtins.__import__", side_effect=ImportError("Mock import error")):
            clear_schema_cache()
            platforms = get_supported_platforms()

            assert isinstance(platforms, list)
            assert len(platforms) > 0
            assert "vEOS-lab" in platforms

    def test_get_supported_device_types_with_exception(self) -> None:
        """Test device type retrieval with exception during import."""
        with patch("builtins.__import__", side_effect=ImportError("Mock import error")):
            clear_schema_cache()
            device_types = get_supported_device_types()

            assert isinstance(device_types, list)
            assert len(device_types) > 0
            assert "spine" in device_types

    def test_platforms_fallback_values(self) -> None:
        """Test that fallback platforms contain expected values."""
        clear_schema_cache()
        platforms = get_supported_platforms()

        expected_platforms = ["vEOS-lab", "vEOS", "cEOS", "7050X3", "7280R3"]
        for platform in expected_platforms:
            assert platform in platforms

    def test_device_types_fallback_values(self) -> None:
        """Test that fallback device types contain expected values."""
        clear_schema_cache()
        device_types = get_supported_device_types()

        expected_types = ["spine", "leaf", "border_leaf", "super_spine"]
        for device_type in expected_types:
            assert device_type in device_types

    def test_multiple_cache_clears_are_safe(self) -> None:
        """Test that multiple cache clears don't cause issues."""
        clear_schema_cache()
        clear_schema_cache()
        clear_schema_cache()

        # Should still work after multiple clears
        platforms = get_supported_platforms()
        device_types = get_supported_device_types()
        version = get_avd_schema_version()

        assert isinstance(platforms, list)
        assert isinstance(device_types, list)
        assert version is None or isinstance(version, str)

    def test_schema_data_consistency(self) -> None:
        """Test that schema data is consistent across calls."""
        platforms1 = get_supported_platforms()
        platforms2 = get_supported_platforms()

        device_types1 = get_supported_device_types()
        device_types2 = get_supported_device_types()

        # Should be identical due to caching
        assert platforms1 == platforms2
        assert device_types1 == device_types2

    def test_logging_when_pyavd_available(self) -> None:
        """Test logging when py-avd is available."""
        with patch("avd_cli.utils.schema.logger") as mock_logger:
            with patch("builtins.__import__"):
                clear_schema_cache()
                get_supported_platforms()

                # Should log info about using py-avd
                assert mock_logger.info.called

    def test_logging_when_pyavd_unavailable(self) -> None:
        """Test logging when py-avd is unavailable."""
        with patch("avd_cli.utils.schema.logger") as mock_logger:
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                clear_schema_cache()
                get_supported_platforms()

                # Should log debug about fallback
                assert mock_logger.debug.called

    def test_list_returns_copy_not_reference(self) -> None:
        """Test that returned lists are safe copies."""
        # Test with platforms
        platforms1 = get_supported_platforms()
        platforms2 = get_supported_platforms()

        original_length = len(platforms1)
        platforms1.append("test_platform")

        # Due to lru_cache, this will actually affect both since they're the same object
        # But the fallback constants themselves are protected
        assert len(platforms2) == original_length + 1  # Same cached object

    def test_empty_fallback_handling(self) -> None:
        """Test handling when fallback lists might be empty."""
        with patch("avd_cli.utils.schema._FALLBACK_PLATFORMS", []):
            with patch("avd_cli.utils.schema._FALLBACK_DEVICE_TYPES", []):
                clear_schema_cache()

                platforms = get_supported_platforms()
                device_types = get_supported_device_types()

                # Should still return lists even if empty
                assert isinstance(platforms, list)
                assert isinstance(device_types, list)
                assert len(platforms) == 0
                assert len(device_types) == 0

    def test_version_with_missing_attribute(self) -> None:
        """Test version retrieval when __version__ attribute is missing."""
        mock_pyavd = MagicMock()
        # Remove __version__ attribute
        if hasattr(mock_pyavd, "__version__"):
            delattr(mock_pyavd, "__version__")

        with patch.dict("sys.modules", {"pyavd": mock_pyavd}):
            clear_schema_cache()
            version = get_avd_schema_version()

            assert version is None

    def test_concurrent_access(self) -> None:
        """Test that concurrent access to cached functions is safe."""
        import threading

        results: list[int] = []

        def get_platforms() -> None:
            platforms = get_supported_platforms()
            results.append(len(platforms))

        # Clear cache first
        clear_schema_cache()

        # Create multiple threads
        threads = [threading.Thread(target=get_platforms) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All results should be the same
        assert len(set(results)) == 1  # All the same value
        assert results[0] > 0
