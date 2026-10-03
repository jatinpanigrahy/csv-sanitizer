"""Data normalization and sanitization utilities for CSV columns.

This module provides focused, pure functions designed to standardize heterogeneous,
real-world input data into clean, uniform representations for tabular columns.
"""

from typing import Any

import pandas as pd
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat


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


def normalize_phones(
    series: pd.Series, default_country: str
) -> tuple[pd.Series, int, int]:
    """Standardize phone numbers into E.164 format and track parseability.

    Parses telephone numbers using Google's libphonenumber metadata with a fallback
    default country code. Valid numbers are formatted to standard E.164. Unparseable
    or invalid numbers are preserved in their original form.

    Args:
        series: Pandas Series representing the raw phone number column.
        default_country: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB') to use
            when country dial prefixes are missing.

    Returns:
        A tuple of:
            - cleaned: Pandas Series with formatted E.164 numbers or original values.
            - normalized_count: Total count of successfully standardized numbers.
            - unparseable_count: Total count of numbers that failed parsing or validation.
    """
    cleaned_values: list[Any] = []
    normalized_count = 0
    unparseable_count = 0

    for val in series:
        if pd.isna(val) or val is None or val == "":
            cleaned_values.append(val)
            unparseable_count += 1
            continue

        try:
            parsed = phonenumbers.parse(str(val), default_country)
            if phonenumbers.is_valid_number(parsed):
                cleaned_values.append(
                    phonenumbers.format_number(
                        parsed, PhoneNumberFormat.E164
                    )
                )
                normalized_count += 1
            else:
                cleaned_values.append(val)
                unparseable_count += 1
        except NumberParseException:
            cleaned_values.append(val)
            unparseable_count += 1

    cleaned_series = pd.Series(cleaned_values, index=series.index)
    return cleaned_series, normalized_count, unparseable_count


def normalize_dates(
    series: pd.Series, target_format: str
) -> tuple[pd.Series, int, int]:
    """Standardize date representations into a uniform string format.

    Parses heterogeneous date strings using pandas mixed-format parser and formats
    valid timestamps according to target_format. Preserves original strings for rows
    that cannot be parsed.

    Args:
        series: Pandas Series representing the raw date column.
        target_format: strftime format string (e.g., '%Y-%m-%d') for the cleaned dates.

    Returns:
        A tuple of:
            - cleaned: Pandas Series with standardized date strings or original values.
            - normalized_count: Total count of successfully parsed dates.
            - unparseable_count: Total count of values that failed parsing.
    """
    dt_series = pd.to_datetime(series, format="mixed", errors="coerce")
    formatted = dt_series.dt.strftime(target_format)
    cleaned = formatted.where(dt_series.notna(), series)
    normalized_count = int(dt_series.notna().sum())
    unparseable_count = int(dt_series.isna().sum())

    return cleaned, normalized_count, unparseable_count
