"""Unit tests for PatternMatcher class."""

import pytest

from avd_cli.utils.pattern_matcher import PatternMatcher


class TestPatternMatcher:
    """Test cases for PatternMatcher class."""

    def test_exact_match(self) -> None:
        """Test exact string matching.

        Given: Pattern matcher with exact string patterns
        When: Matching exact strings
        Then: Matches are correctly identified
        """
        matcher = PatternMatcher(["spine01", "leaf01"])

        assert matcher.matches("spine01") is True
        assert matcher.matches("leaf01") is True
        assert matcher.matches("spine02") is False
        assert matcher.matches("leaf02") is False

    def test_wildcard_match(self) -> None:
        """Test wildcard pattern matching.

        Given: Pattern matcher with wildcard patterns
        When: Matching strings against wildcards
        Then: Wildcards match correctly
        """
        matcher = PatternMatcher(["spine*", "leaf*"])

        assert matcher.matches("spine01") is True
        assert matcher.matches("spine02") is True
        assert matcher.matches("leaf01") is True
        assert matcher.matches("leaf-1a") is True
        assert matcher.matches("border01") is False

    def test_wildcard_in_middle(self) -> None:
        """Test wildcard patterns in middle of string.

        Given: Pattern with wildcard in middle
        When: Matching strings
        Then: Middle wildcards work correctly
        """
        matcher = PatternMatcher(["dc1_*_leaf"])

        assert matcher.matches("dc1_pod1_leaf") is True
        assert matcher.matches("dc1_pod2_leaf") is True
        assert matcher.matches("dc2_pod1_leaf") is False
        assert matcher.matches("dc1_spine") is False

    def test_question_mark_wildcard(self) -> None:
        """Test single character wildcard.

        Given: Pattern with ? wildcard
        When: Matching strings
        Then: Single character matches work
        """
        matcher = PatternMatcher(["spine0?"])

        assert matcher.matches("spine01") is True
        assert matcher.matches("spine02") is True
        assert matcher.matches("spine10") is False
        assert matcher.matches("spine0") is False

    def test_numeric_range(self) -> None:
        """Test numeric range expansion.

        Given: Pattern with numeric range
        When: Matching strings
        Then: Range is expanded correctly
        """
        matcher = PatternMatcher(["leaf[01:05]"])

        assert matcher.matches("leaf01") is True
        assert matcher.matches("leaf02") is True
        assert matcher.matches("leaf05") is True
        assert matcher.matches("leaf06") is False
        assert matcher.matches("leaf00") is False

    def test_numeric_range_with_padding(self) -> None:
        """Test numeric range with zero padding.

        Given: Pattern with zero-padded numeric range
        When: Matching strings
        Then: Padding is preserved
        """
        matcher = PatternMatcher(["spine[001:005]"])

        assert matcher.matches("spine001") is True
        assert matcher.matches("spine003") is True
        assert matcher.matches("spine005") is True
        assert matcher.matches("spine01") is False  # Different padding
        assert matcher.matches("spine1") is False

    def test_alphabetic_range(self) -> None:
        """Test alphabetic range expansion.

        Given: Pattern with alphabetic range
        When: Matching strings
        Then: Alphabetic range works correctly
        """
        matcher = PatternMatcher(["pod[a:c]"])

        assert matcher.matches("poda") is True
        assert matcher.matches("podb") is True
        assert matcher.matches("podc") is True
        assert matcher.matches("podd") is False

    def test_alphabetic_range_uppercase(self) -> None:
        """Test alphabetic range with uppercase letters.

        Given: Pattern with uppercase alphabetic range
        When: Matching strings
        Then: Case is preserved
        """
        matcher = PatternMatcher(["POD[A:C]"])

        assert matcher.matches("PODA") is True
        assert matcher.matches("PODB") is True
        assert matcher.matches("PODC") is True
        assert matcher.matches("poda") is False  # Different case

    def test_exclusion_pattern(self) -> None:
        """Test exclusion patterns.

        Given: Pattern with exclusions
        When: Matching strings
        Then: Exclusions work correctly
        """
        matcher = PatternMatcher(["spine*", "!spine01"])

        assert matcher.matches("spine02") is True
        assert matcher.matches("spine03") is True
        assert matcher.matches("spine01") is False  # Excluded

    def test_multiple_exclusions(self) -> None:
        """Test multiple exclusion patterns.

        Given: Pattern with multiple exclusions
        When: Matching strings
        Then: All exclusions are applied
        """
        matcher = PatternMatcher(["leaf*", "!leaf01", "!leaf02"])

        assert matcher.matches("leaf03") is True
        assert matcher.matches("leaf04") is True
        assert matcher.matches("leaf01") is False
        assert matcher.matches("leaf02") is False

    def test_exclusion_with_wildcard(self) -> None:
        """Test exclusion with wildcard pattern.

        Given: Exclusion pattern with wildcard
        When: Matching strings
        Then: Wildcard exclusions work
        """
        matcher = PatternMatcher(["leaf*", "!leaf0*"])

        assert matcher.matches("leaf10") is True
        assert matcher.matches("leaf20") is True
        assert matcher.matches("leaf01") is False
        assert matcher.matches("leaf02") is False

    def test_no_inclusion_patterns(self) -> None:
        """Test matcher with only exclusions.

        Given: Pattern matcher with only exclusions
        When: Matching strings
        Then: Everything matches except exclusions
        """
        matcher = PatternMatcher(["!spine01"])

        assert matcher.matches("spine02") is True
        assert matcher.matches("leaf01") is True
        assert matcher.matches("spine01") is False

    def test_filter_values(self) -> None:
        """Test filtering a list of values.

        Given: Pattern matcher and list of values
        When: Filtering values
        Then: Only matching values are returned
        """
        matcher = PatternMatcher(["spine*", "!spine01"])
        values = ["spine01", "spine02", "spine03", "leaf01"]

        result = matcher.filter_values(values)

        assert result == ["spine02", "spine03"]

    def test_get_matched_values(self) -> None:
        """Test getting set of matched values.

        Given: Pattern matcher and list of values
        When: Getting matched values
        Then: Returns set of matched values
        """
        matcher = PatternMatcher(["spine*"])
        values = ["spine01", "spine02", "leaf01", "spine03"]

        result = matcher.get_matched_values(values)

        assert result == {"spine01", "spine02", "spine03"}

    def test_invalid_range_start_greater_than_end(self) -> None:
        """Test invalid range where start > end.

        Given: Pattern with invalid range
        When: Creating pattern matcher
        Then: ValueError is raised
        """
        with pytest.raises(ValueError, match="start.*greater than end"):
            PatternMatcher(["leaf[05:01]"])

    def test_invalid_mixed_range_types(self) -> None:
        """Test invalid range with mixed types.

        Given: Pattern with mixed numeric/alphabetic range
        When: Creating pattern matcher
        Then: ValueError is raised
        """
        with pytest.raises(ValueError, match="must be both numeric or both single alphabetic"):
            PatternMatcher(["device[1:z]"])

    def test_empty_exclusion_pattern(self) -> None:
        """Test empty exclusion pattern.

        Given: Pattern with empty exclusion (just '!')
        When: Creating pattern matcher
        Then: ValueError is raised
        """
        with pytest.raises(ValueError, match="Exclusion pattern cannot be empty"):
            PatternMatcher(["!"])

    def test_complex_pattern_combination(self) -> None:
        """Test complex combination of patterns.

        Given: Complex pattern with ranges, wildcards, and exclusions
        When: Matching various strings
        Then: All pattern types work together
        """
        matcher = PatternMatcher([
            "spine[01:03]",
            "leaf*",
            "!leaf-mgmt*",
            "border*"
        ])

        # Spine range matches
        assert matcher.matches("spine01") is True
        assert matcher.matches("spine02") is True
        assert matcher.matches("spine03") is True
        assert matcher.matches("spine04") is False

        # Leaf wildcard matches (except excluded)
        assert matcher.matches("leaf-1a") is True
        assert matcher.matches("leaf-mgmt01") is False

        # Border wildcard matches
        assert matcher.matches("border01") is True
        assert matcher.matches("border-leaf") is True

    def test_pattern_with_range_and_suffix(self) -> None:
        """Test pattern with range and suffix.

        Given: Pattern with range followed by suffix
        When: Matching strings
        Then: Range and suffix are both matched
        """
        matcher = PatternMatcher(["spine[01:02]-dc1"])

        assert matcher.matches("spine01-dc1") is True
        assert matcher.matches("spine02-dc1") is True
        assert matcher.matches("spine03-dc1") is False
        assert matcher.matches("spine01") is False

    def test_repr(self) -> None:
        """Test string representation of PatternMatcher.

        Given: PatternMatcher instance
        When: Getting string representation
        Then: Returns formatted string with patterns
        """
        matcher = PatternMatcher(["spine*", "!spine01"])

        repr_str = repr(matcher)

        assert "PatternMatcher" in repr_str
        assert "spine*" in repr_str
        assert "spine01" in repr_str
