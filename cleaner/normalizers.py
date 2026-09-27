"""Data normalization and sanitization utilities for CSV columns.

This module provides focused, pure functions designed to standardize heterogeneous,
real-world input data into clean, uniform representations for tabular columns.
"""

import pandas as pd


def normalize_names(series: pd.Series) -> tuple[pd.Series, int]:
    """Standardize personal names into Title Case and count modifications.

    Strips leading and trailing whitespace, converts names to Title Case, and
    accurately tracks how many non-empty values were modified from their
    original format.

    Args:
        series: Pandas Series representing the raw name column.

    Returns:
        A tuple of:
            - cleaned: Pandas Series with title-cased names.
            - changes_count: The total count of values modified.
    """
    raw_strings = series.fillna("").astype(str).str.strip()
    cleaned = raw_strings.str.title()

    # Track modifications only on non-blank entries
    changed_mask = (raw_strings != cleaned) & (raw_strings != "")
    changes_count = int(changed_mask.sum())

    return cleaned, changes_count


def normalize_emails(series: pd.Series) -> tuple[pd.Series, int]:
    """Standardize email addresses to lowercase and identify missing entries.

    Strips extraneous whitespace, converts characters to lowercase conforming to
    standard email case-insensitivity, and tallies missing or blank entries.

    Args:
        series: Pandas Series representing the raw email column.

    Returns:
        A tuple of:
            - cleaned: Pandas Series with lowercased, stripped emails.
            - missing_count: Number of rows lacking an email address.
    """
    raw_strings = series.fillna("").astype(str).str.strip()
    cleaned = raw_strings.str.lower()

    # Tally blank or previously null email fields
    missing_count = int((cleaned == "").sum())

    return cleaned, missing_count
