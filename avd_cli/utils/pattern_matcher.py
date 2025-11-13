"""Pattern matching utilities for filtering devices.

This module provides Ansible-compatible pattern matching for device filtering,
supporting wildcards, ranges, and exclusions.
"""

from __future__ import annotations

import fnmatch
import re
from typing import List, Set


class PatternMatcher:
    """Ansible-compatible pattern matcher for device filtering.

    Supports:
    - Wildcards: `spine*`, `*leaf*`, `?`
    - Ranges: `leaf[01:05]`, `spine[a:c]`
    - Exclusions: `!spine01`, `!dc1_*`

    Examples
    --------
    >>> matcher = PatternMatcher(["spine*", "!spine01"])
    >>> matcher.matches("spine02")
    True
    >>> matcher.matches("spine01")
    False
    >>> matcher.matches("leaf01")
    False
    """

    def __init__(self, patterns: List[str]) -> None:
        """Initialize pattern matcher with list of patterns.

        Parameters
        ----------
        patterns : List[str]
            List of patterns to match against. Patterns starting with '!'
            are treated as exclusions.

        Raises
        ------
        ValueError
            If a pattern is invalid (e.g., malformed range).
        """
        self.inclusion_patterns: List[str] = []
        self.exclusion_patterns: List[str] = []

        for pattern in patterns:
            if pattern.startswith("!"):
                # Exclusion pattern
                exclusion = pattern[1:]  # Remove the '!' prefix
                if not exclusion:
                    raise ValueError("Exclusion pattern cannot be empty")
                self.exclusion_patterns.append(exclusion)
            else:
                # Inclusion pattern
                self.inclusion_patterns.append(pattern)

        # Expand all range patterns into concrete patterns
        self.expanded_inclusions = self._expand_patterns(self.inclusion_patterns)
        self.expanded_exclusions = self._expand_patterns(self.exclusion_patterns)

    def matches(self, value: str) -> bool:
        """Check if value matches the pattern set.

        A value matches if:
        1. It matches at least one inclusion pattern (OR logic)
        2. It does not match any exclusion pattern

        Parameters
        ----------
        value : str
            The value to check against patterns.

        Returns
        -------
        bool
            True if value matches, False otherwise.
        """
        # If no inclusion patterns, match everything
        if not self.expanded_inclusions:
            matches_inclusion = True
        else:
            # Check if value matches any inclusion pattern
            matches_inclusion = any(
                fnmatch.fnmatch(value, pattern) for pattern in self.expanded_inclusions
            )

        if not matches_inclusion:
            return False

        # Check if value matches any exclusion pattern
        matches_exclusion = any(
            fnmatch.fnmatch(value, pattern) for pattern in self.expanded_exclusions
        )

        return not matches_exclusion

    def filter_values(self, values: List[str]) -> List[str]:
        """Filter a list of values based on patterns.

        Parameters
        ----------
        values : List[str]
            List of values to filter.

        Returns
        -------
        List[str]
            Filtered list containing only matching values.
        """
        return [value for value in values if self.matches(value)]

    def get_matched_values(self, values: List[str]) -> Set[str]:
        """Get set of values that match any pattern.

        Parameters
        ----------
        values : List[str]
            List of values to check.

        Returns
        -------
        Set[str]
            Set of values that matched at least one pattern.
        """
        return set(self.filter_values(values))

    @staticmethod
    def _expand_patterns(patterns: List[str]) -> List[str]:
        """Expand range patterns into individual patterns.

        Converts patterns like 'leaf[01:05]' into:
        ['leaf01', 'leaf02', 'leaf03', 'leaf04', 'leaf05']

        Parameters
        ----------
        patterns : List[str]
            List of patterns, possibly containing range notation.

        Returns
        -------
        List[str]
            List of expanded patterns.

        Raises
        ------
        ValueError
            If a range pattern is malformed.
        """
        expanded = []

        for pattern in patterns:
            # Check if pattern contains a range [start:end]
            range_match = re.search(r'\[([^:\]]+):([^:\]]+)\]', pattern)

            if range_match:
                # Extract prefix, start, end, and suffix
                prefix = pattern[:range_match.start()]
                suffix = pattern[range_match.end():]
                start_str = range_match.group(1)
                end_str = range_match.group(2)

                # Determine if it's numeric or alphabetic range
                if start_str.isdigit() and end_str.isdigit():
                    # Numeric range
                    start = int(start_str)
                    end = int(end_str)

                    if start > end:
                        raise ValueError(
                            f"Invalid range in pattern '{pattern}': "
                            f"start ({start}) is greater than end ({end})"
                        )

                    # Determine padding (e.g., '01' has padding of 2)
                    padding = len(start_str)

                    for i in range(start, end + 1):
                        expanded_pattern = f"{prefix}{str(i).zfill(padding)}{suffix}"
                        expanded.append(expanded_pattern)

                elif start_str.isalpha() and end_str.isalpha() and len(start_str) == 1 and len(end_str) == 1:
                    # Alphabetic range (single character)
                    start_ord = ord(start_str.lower())
                    end_ord = ord(end_str.lower())

                    if start_ord > end_ord:
                        raise ValueError(
                            f"Invalid range in pattern '{pattern}': "
                            f"start ('{start_str}') is greater than end ('{end_str}')"
                        )

                    # Preserve case from the original
                    is_upper = start_str.isupper()

                    for i in range(start_ord, end_ord + 1):
                        char = chr(i).upper() if is_upper else chr(i)
                        expanded_pattern = f"{prefix}{char}{suffix}"
                        expanded.append(expanded_pattern)
                else:
                    raise ValueError(
                        f"Invalid range in pattern '{pattern}': "
                        f"range values must be both numeric or both single alphabetic characters"
                    )
            else:
                # No range in pattern, use as-is
                expanded.append(pattern)

        return expanded

    def __repr__(self) -> str:
        """Return string representation of PatternMatcher."""
        return (
            f"PatternMatcher(inclusions={self.inclusion_patterns}, "
            f"exclusions={self.exclusion_patterns})"
        )
