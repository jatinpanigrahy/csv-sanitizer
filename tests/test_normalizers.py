"""Unit tests for column normalization functions.

Validates the transformation correctness, edge-case resilience, and change-count
accuracy of the name and email sanitization utilities.
"""

import pandas as pd

from cleaner.normalizers import normalize_emails, normalize_names


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
