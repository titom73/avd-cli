#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for Jinja2 template resolution module.

Tests cover template variable resolution, hostvars access, filters,
and error handling as specified in AC-036 to AC-045.
"""

import pytest

from avd_cli.exceptions import TemplateError
from avd_cli.logics.templating import TemplateResolver, build_template_context


class TestTemplateResolver:
    """Tests for TemplateResolver class."""

    def test_simple_variable_resolution(self):
        """AC-036: Simple variable should be replaced with value from context."""
        context = {"my_var": "hello"}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ my_var }}")
        assert result == "hello"

    def test_hostvars_dictionary_access(self):
        """AC-037: hostvars['hostname']['key'] should resolve from host_vars."""
        context = {"hostvars": {"spine01": {"platform": "7050X3", "mgmt_ip": "192.168.0.10"}}}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ hostvars['spine01']['platform'] }}")
        assert result == "7050X3"

    def test_hostvars_nested_access(self):
        """Test nested dictionary access in hostvars."""
        context = {"hostvars": {"leaf01": {"interfaces": {"Ethernet1": {"description": "uplink"}}}}}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ hostvars['leaf01']['interfaces']['Ethernet1']['description'] }}")
        assert result == "uplink"

    def test_default_filter_with_undefined_variable(self):
        """AC-038: Variable | default(value) should use default when var undefined."""
        context = {}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ undefined_var | default(123) }}")
        assert result == "123"

    def test_default_filter_with_defined_variable(self):
        """AC-039: Variable | default(value) should use var value when defined."""
        context = {"my_var": 456}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ my_var | default(123) }}")
        assert result == "456"

    def test_default_filter_with_string(self):
        """Test default filter with string default value."""
        context = {}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ missing | default('N/A') }}")
        assert result == "N/A"

    def test_undefined_variable_returns_empty_string(self):
        """AC-040: Undefined variable without default returns empty string (graceful)."""
        context = {}
        resolver = TemplateResolver(context)

        # With Undefined (not StrictUndefined), undefined vars return empty
        result = resolver.resolve("{{ undefined_var }}")
        assert result == ""

    def test_nested_template_resolution(self):
        """AC-041: Templates in nested structures should be resolved."""
        context = {"var1": "value1", "var2": "value2"}
        resolver = TemplateResolver(context)

        nested_data = {
            "level1": {"level2": "{{ var1 }}", "list": ["{{ var2 }}", "static"]},
            "simple": "{{ var1 }}",
        }

        result = resolver.resolve_recursive(nested_data)
        assert result["level1"]["level2"] == "value1"
        assert result["level1"]["list"][0] == "value2"
        assert result["simple"] == "value1"

    def test_preserve_non_string_types(self):
        """AC-042: Non-string values (int, bool, list) should be preserved."""
        context = {}
        resolver = TemplateResolver(context)

        data = {
            "integer": 123,
            "boolean": True,
            "float": 45.67,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"num": 789},
        }

        result = resolver.resolve_recursive(data)
        assert result["integer"] == 123
        assert result["boolean"] is True
        assert result["float"] == 45.67
        assert result["none"] is None
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["num"] == 789

    def test_template_syntax_error(self):
        """AC-043: Template syntax error should raise clear TemplateError."""
        context = {"var": "value"}
        resolver = TemplateResolver(context)

        # Invalid Jinja2 syntax
        with pytest.raises(TemplateError, match="Template error"):
            resolver.resolve("{{ var | }}")  # Incomplete filter

    def test_multiple_templates_in_string(self):
        """AC-045: Multiple templates in same string should all be resolved."""
        context = {"var1": "Hello", "var2": "World"}
        resolver = TemplateResolver(context)

        result = resolver.resolve("{{ var1 }} {{ var2 }}!")
        assert result == "Hello World!"

    def test_string_filters(self):
        """Test Jinja2 string filters (lower, upper)."""
        context = {"text": "MixedCase"}
        resolver = TemplateResolver(context)

        result_lower = resolver.resolve("{{ text | lower }}")
        assert result_lower == "mixedcase"

        result_upper = resolver.resolve("{{ text | upper }}")
        assert result_upper == "MIXEDCASE"

    def test_bool_filter(self):
        """Test custom bool filter."""
        context = {"val1": "yes", "val2": "false", "val3": 1, "val4": 0}
        resolver = TemplateResolver(context)

        # Note: Our bool filter converts strings to bool
        result1 = resolver.resolve("{{ val1 | bool }}")
        assert result1 == "True"

        result2 = resolver.resolve("{{ val2 | bool }}")
        assert result2 == "False"

    def test_has_template_detection(self):
        """Test template pattern detection."""
        resolver = TemplateResolver({})

        assert resolver.has_template("{{ variable }}") is True
        assert resolver.has_template("no template here") is False
        assert resolver.has_template("prefix {{ var }} suffix") is True
        assert resolver.has_template("multiple {{ var1 }} and {{ var2 }}") is True

    def test_resolve_value_with_string(self):
        """Test resolve_value with string containing template."""
        context = {"my_var": "test"}
        resolver = TemplateResolver(context)

        result = resolver.resolve_value("{{ my_var }}")
        assert result == "test"

    def test_resolve_value_with_non_string(self):
        """Test resolve_value preserves non-string types."""
        resolver = TemplateResolver({})

        assert resolver.resolve_value(123) == 123
        assert resolver.resolve_value(True) is True
        assert resolver.resolve_value(None) is None

    def test_resolve_dict(self):
        """Test resolve_dict resolves all string values."""
        context = {"var1": "value1", "var2": "value2"}
        resolver = TemplateResolver(context)

        data = {"key1": "{{ var1 }}", "key2": 123, "key3": "{{ var2 }}"}

        result = resolver.resolve_dict(data)
        assert result["key1"] == "value1"
        assert result["key2"] == 123
        assert result["key3"] == "value2"

    def test_resolve_list(self):
        """Test resolve_list resolves all string elements."""
        context = {"var1": "value1", "var2": "value2"}
        resolver = TemplateResolver(context)

        data = ["{{ var1 }}", 123, "{{ var2 }}", {"nested": "{{ var1 }}"}]

        result = resolver.resolve_list(data)
        assert result[0] == "value1"
        assert result[1] == 123
        assert result[2] == "value2"
        assert result[3]["nested"] == "value1"


class TestBuildTemplateContext:
    """Tests for build_template_context function."""

    def test_context_includes_global_vars(self):
        """Test global vars are included in context."""
        global_vars = {"global_mtu": 9214, "global_asn": 65000}
        group_vars = {}
        host_vars = {}

        context = build_template_context(global_vars, group_vars, host_vars)

        assert context["global_mtu"] == 9214
        assert context["global_asn"] == 65000

    def test_context_includes_group_vars(self):
        """Test group vars are merged into context."""
        global_vars = {}
        group_vars = {"SPINES": {"bgp_as": 65001}, "LEAVES": {"bgp_as": 65002}}
        host_vars = {}

        context = build_template_context(global_vars, group_vars, host_vars)

        # Group vars should be merged at top level
        # Note: If multiple groups define same key, later wins
        assert "bgp_as" in context

    def test_context_creates_hostvars(self):
        """Test hostvars dictionary is created."""
        global_vars = {"global_var": "global"}
        group_vars = {"GROUP1": {"group_var": "group"}}
        host_vars = {"host1": {"ansible_host": "192.168.0.10"}}

        context = build_template_context(global_vars, group_vars, host_vars)

        assert "hostvars" in context
        assert "host1" in context["hostvars"]
        assert context["hostvars"]["host1"]["ansible_host"] == "192.168.0.10"

    def test_hostvars_includes_global_and_host_vars(self):
        """Test hostvars for each host includes global and host vars."""
        global_vars = {"global_mtu": 9214}
        group_vars = {"SPINES": {"platform": "7050X3"}}
        host_vars = {"spine01": {"id": 1, "platform": "from_host"}}

        context = build_template_context(global_vars, group_vars, host_vars)

        # Each host should have global + host vars
        # Group vars are available at top level, not in hostvars
        assert context["hostvars"]["spine01"]["global_mtu"] == 9214
        assert context["hostvars"]["spine01"]["platform"] == "from_host"
        assert context["hostvars"]["spine01"]["id"] == 1

    def test_hostvars_includes_inventory_hostname(self):
        """Test inventory_hostname is added to each host."""
        global_vars = {}
        group_vars = {}
        host_vars = {"spine01": {}}

        context = build_template_context(global_vars, group_vars, host_vars)

        assert context["hostvars"]["spine01"]["inventory_hostname"] == "spine01"

    def test_empty_inventory(self):
        """Test build_template_context with empty inventory."""
        context = build_template_context({}, {}, {})

        assert context == {"hostvars": {}}

    def test_host_vars_override_group_vars(self):
        """Test host_vars override group_vars for same key."""
        global_vars = {}
        group_vars = {"GROUP": {"platform": "from_group"}}
        host_vars = {"host1": {"platform": "from_host"}}

        context = build_template_context(global_vars, group_vars, host_vars)

        # Host-specific value should win
        assert context["hostvars"]["host1"]["platform"] == "from_host"


class TestTemplateIntegration:
    """Integration tests combining multiple template features."""

    def test_realistic_inventory_scenario(self):
        """Test realistic AVD inventory scenario with templates."""
        global_vars = {"default_mtu": 9214}
        group_vars = {
            "SPINES": {"platform": "{{ hostvars['spine01']['poc_platform'] }}"},
            "LEAVES": {"platform": "722XP"},
        }
        host_vars = {
            "spine01": {"poc_platform": "7050X3", "ansible_host": "192.168.0.10"},
            "leaf01": {"ansible_host": "192.168.0.20"},
        }

        context = build_template_context(global_vars, group_vars, host_vars)
        resolver = TemplateResolver(context)

        # Resolve group_vars templates
        resolved_group_vars = {name: resolver.resolve_recursive(data) for name, data in group_vars.items()}

        # Platform template should resolve
        assert resolved_group_vars["SPINES"]["platform"] == "7050X3"

    def test_mgmt_ip_template_resolution(self):
        """Test management IP resolution from ansible_host."""
        global_vars = {}
        group_vars = {}
        host_vars = {
            "leaf01": {"ansible_host": "192.168.0.14"},
            "leaf02": {"ansible_host": "192.168.0.15"},
        }

        # Simulate AVD leaf.yml structure
        leaf_config = {
            "l2leaf": {
                "node_groups": [
                    {
                        "group": "IDF1",
                        "nodes": [
                            {
                                "name": "leaf01",
                                "mgmt_ip": "{{ hostvars['leaf01'].ansible_host }}/24",
                            }
                        ],
                    }
                ]
            }
        }

        context = build_template_context(global_vars, group_vars, host_vars)
        resolver = TemplateResolver(context)

        resolved = resolver.resolve_recursive(leaf_config)
        mgmt_ip = resolved["l2leaf"]["node_groups"][0]["nodes"][0]["mgmt_ip"]

        assert mgmt_ip == "192.168.0.14/24"
