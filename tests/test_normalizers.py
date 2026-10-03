"""Unit tests for column normalization functions.

Validates the transformation correctness, edge-case resilience, and change-count
accuracy of name, email, phone, and date sanitization utilities.
"""

import pandas as pd

from cleaner.normalizers import (
    normalize_dates,
    normalize_emails,
    normalize_names,
    normalize_phones,
)


def test_normalize_names_casing_and_counts() -> None:
    """Verify title-casing transformations and accurate change counting."""
    raw = pd.Series(["john doe", "SARAH CONNOR", "Bob Smith"])
    cleaned, count = normalize_names(raw)

    assert list(cleaned) == ["John Doe", "Sarah Connor", "Bob Smith"]
    # Only "john doe" and "SARAH CONNOR" required case adjustment
    assert count == 2


def test_normalize_names_handles_blanks() -> None:
    """Verify whitespace-only entries and null values resolve to empty strings."""
    raw = pd.Series(["   ", None, "alice wonder"])
    cleaned, count = normalize_names(raw)

    assert list(cleaned) == ["", "", "Alice Wonder"]
    # Only "alice wonder" was a non-empty name modified into Title Case
    assert count == 1


def test_normalize_emails_standardization() -> None:
    """Verify email lowercasing and extraneous whitespace stripping."""
    raw = pd.Series(["user@EXAMPLE.COM", "ADMIN@DOMAIN.ORG", "test@test.com"])
    cleaned, missing_count = normalize_emails(raw)

    assert list(cleaned) == ["user@example.com", "admin@domain.org", "test@test.com"]
    assert missing_count == 0


def test_normalize_emails_missing_count() -> None:
    """Verify missing, blank, and null email detection."""
    raw = pd.Series(["valid@domain.com", "", "   ", None])
    cleaned, missing_count = normalize_emails(raw)

    # 3 entries lack a usable email address
    assert missing_count == 3


def test_normalize_phones_valid_formats() -> None:
    """Verify phone numbers in various formats standardize to E.164."""
    raw = pd.Series([
        "(202) 555-0173",
        "202-555-0123",
        "202.555.0199",
        "+12025550188",
        "+44 20 7946 0958",
    ])
    cleaned, normalized_count, unparseable_count = normalize_phones(raw, "US")

    assert list(cleaned) == [
        "+12025550173",
        "+12025550123",
        "+12025550199",
        "+12025550188",
        "+442079460958",
    ]
    assert normalized_count == 5
    assert unparseable_count == 0


def test_normalize_phones_alternative_country() -> None:
    """Verify default_country parameter applies to national phone formats."""
    raw = pd.Series(["020 7946 0958"])
    cleaned, normalized_count, unparseable_count = normalize_phones(raw, "GB")

    assert list(cleaned) == ["+442079460958"]
    assert normalized_count == 1
    assert unparseable_count == 0


def test_normalize_phones_preserves_unparseable() -> None:
    """Verify invalid, malformed, and missing phone numbers are preserved."""
    raw = pd.Series(["invalid-phone", "12345", "", "   ", None])
    cleaned, normalized_count, unparseable_count = normalize_phones(raw, "US")

    assert cleaned.iloc[0] == "invalid-phone"
    assert cleaned.iloc[1] == "12345"
    assert cleaned.iloc[2] == ""
    assert cleaned.iloc[3] == "   "
    assert pd.isna(cleaned.iloc[4])
    assert normalized_count == 0
    assert unparseable_count == 5


def test_normalize_dates_standardization() -> None:
    """Verify diverse date representations standardize to the target format."""
    raw = pd.Series([
        "2023-01-15",
        "05/12/2022",
        "2021/04/01",
        "December 25, 2020",
    ])
    cleaned, normalized_count, unparseable_count = normalize_dates(raw, "%Y-%m-%d")

    assert list(cleaned) == [
        "2023-01-15",
        "2022-05-12",
        "2021-04-01",
        "2020-12-25",
    ]
    assert normalized_count == 4
    assert unparseable_count == 0


def test_normalize_dates_custom_target_format() -> None:
    """Verify date formatting honors custom strftime format patterns."""
    raw = pd.Series(["2023-01-15"])
    cleaned, normalized_count, unparseable_count = normalize_dates(raw, "%d/%m/%Y")

    assert list(cleaned) == ["15/01/2023"]
    assert normalized_count == 1
    assert unparseable_count == 0


def test_normalize_dates_preserves_unparseable() -> None:
    """Verify unparseable and missing date values are retained without error."""
    raw = pd.Series(["not-a-date", "32/13/2020", "", None])
    cleaned, normalized_count, unparseable_count = normalize_dates(raw, "%Y-%m-%d")

    assert cleaned.iloc[0] == "not-a-date"
    assert cleaned.iloc[1] == "32/13/2020"
    assert cleaned.iloc[2] == ""
    assert pd.isna(cleaned.iloc[3])
    assert normalized_count == 0
    assert unparseable_count == 4
