#!/usr/bin/env python
# coding: utf-8 -*-

"""Deep merge utility for dictionary operations."""
from copy import deepcopy
from typing import Any, Dict


def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    *,
    copy: bool = True
) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Recursively merges nested dictionaries. Override values take precedence.
    Lists are replaced, not merged.

    Parameters
    ----------
    base : Dict[str, Any]
        Base dictionary
    override : Dict[str, Any]
        Dictionary to merge into base (takes precedence)
    copy : bool, optional
        If True, creates deep copies to avoid mutation, by default True

    Returns
    -------
    Dict[str, Any]
        Merged dictionary

    Examples
    --------
    >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
    >>> override = {"b": {"d": 4, "e": 5}, "f": 6}
    >>> deep_merge(base, override)
    {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
    """
    result = deepcopy(base) if copy else base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value, copy=copy)
        else:
            result[key] = deepcopy(value) if copy else value

    return result
