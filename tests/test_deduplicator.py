"""Unit tests for the duplicate detection and resolution module.

Validates the accuracy of fuzzy matching, threshold-based auto-merging, data-completeness
selection, borderline candidate flagging, and edge-case resilience.
"""

import pandas as pd
import pytest

from cleaner.deduplicator import find_and_handle_duplicates


def test_auto_merge_keeps_row_with_more_data_earlier() -> None:
    """Verify earlier row is retained when it contains more non-null fields."""
    df = pd.DataFrame([
        {"name": "John Doe", "email": "john@example.com", "phone": "+12025550123"},
        {"name": "John Doe", "email": "john@example.com", "phone": None},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 1
    assert merged_count == 1
    assert flagged_count == 0
    assert cleaned.iloc[0]["phone"] == "+12025550123"
    assert cleaned.iloc[0]["flag_reason"] == ""


def test_auto_merge_keeps_row_with_more_data_later() -> None:
    """Verify later row is retained when it contains more non-null fields."""
    df = pd.DataFrame([
        {"name": "Jane Smith", "email": None, "phone": None},
        {"name": "Jane Smith", "email": "jane@example.com", "phone": "+12025550199"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 1
    assert merged_count == 1
    assert flagged_count == 0
    assert cleaned.iloc[0]["email"] == "jane@example.com"
    assert cleaned.iloc[0]["phone"] == "+12025550199"
    assert cleaned.iloc[0]["flag_reason"] == ""


def test_auto_merge_tie_breaker_keeps_earlier_row() -> None:
    """Verify on tie of data richness, the earlier row is kept."""
    df = pd.DataFrame([
        {"name": "Jonathan Doe", "email": "john_early@example.com"},
        {"name": "Jonathan Doe", "email": "john_late@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 1
    assert merged_count == 1
    assert flagged_count == 0
    assert cleaned.iloc[0]["email"] == "john_early@example.com"


def test_flagging_between_thresholds() -> None:
    """Verify records with similarity between flag and merge thresholds are flagged."""
    df = pd.DataFrame([
        {"name": "Alice Smith", "email": "alice1@example.com"},
        {"name": "Alicia Smith", "email": "alice2@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 2
    assert merged_count == 0
    assert flagged_count == 2
    assert cleaned.iloc[0]["flag_reason"] == "SUSPECTED_DUPLICATE"
    assert cleaned.iloc[1]["flag_reason"] == "SUSPECTED_DUPLICATE"


def test_no_action_for_distinct_names() -> None:
    """Verify unrelated names are neither merged nor flagged."""
    df = pd.DataFrame([
        {"name": "Alice Smith", "email": "alice@example.com"},
        {"name": "Bob Jones", "email": "bob@example.com"},
        {"name": "Charlie Brown", "email": "charlie@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 3
    assert merged_count == 0
    assert flagged_count == 0
    assert all(r == "" for r in cleaned["flag_reason"])


def test_exact_matches_multiple_duplicates() -> None:
    """Verify multiple exact duplicate records merge into a single row."""
    df = pd.DataFrame([
        {"name": "Robert Taylor", "email": "bob@example.com"},
        {"name": "Robert Taylor", "email": "bob@example.com"},
        {"name": "Robert Taylor", "email": "bob@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 1
    assert merged_count == 2
    assert flagged_count == 0
    assert cleaned.iloc[0]["name"] == "Robert Taylor"


def test_empty_dataframe_with_columns() -> None:
    """Verify empty DataFrame with columns returns empty result with flag_reason."""
    df = pd.DataFrame(columns=["name", "email", "phone"])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert cleaned.empty
    assert merged_count == 0
    assert flagged_count == 0
    assert "flag_reason" in cleaned.columns


def test_empty_dataframe_without_columns() -> None:
    """Verify completely empty DataFrame returns empty result with flag_reason."""
    df = pd.DataFrame()

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert cleaned.empty
    assert merged_count == 0
    assert flagged_count == 0
    assert "flag_reason" in cleaned.columns


def test_missing_name_column_raises_error() -> None:
    """Verify KeyError is raised when the specified name column is not present."""
    df = pd.DataFrame([{"user_name": "Alice", "email": "alice@example.com"}])

    with pytest.raises(KeyError, match="not found in DataFrame"):
        find_and_handle_duplicates(df, "nonexistent_column")


def test_custom_thresholds() -> None:
    """Verify custom similarity thresholds govern merge and flag decisions."""
    # "Jonathan Davis" vs "Johnathan Davis" ratio is ~96.55
    df = pd.DataFrame([
        {"name": "Jonathan Davis", "email": "jd1@example.com"},
        {"name": "Johnathan Davis", "email": "jd2@example.com"},
    ])

    # With higher auto_merge_threshold (98.0), this becomes a flag instead of merge
    cleaned, merged_count, flagged_count = find_and_handle_duplicates(
        df, "name", auto_merge_threshold=98.0, flag_threshold=90.0
    )

    assert len(cleaned) == 2
    assert merged_count == 0
    assert flagged_count == 2
    assert cleaned.iloc[0]["flag_reason"] == "SUSPECTED_DUPLICATE"
    assert cleaned.iloc[1]["flag_reason"] == "SUSPECTED_DUPLICATE"


def test_blank_and_null_names_ignored() -> None:
    """Verify blank, whitespace-only, and null names are never matched as duplicates."""
    df = pd.DataFrame([
        {"name": None, "email": "unknown1@example.com"},
        {"name": "", "email": "unknown2@example.com"},
        {"name": "   ", "email": "unknown3@example.com"},
        {"name": "Valid Name", "email": "valid@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 4
    assert merged_count == 0
    assert flagged_count == 0


def test_token_order_insensitivity() -> None:
    """Verify token sort ratio successfully detects reversed name ordering."""
    df = pd.DataFrame([
        {"name": "Smith John", "email": None},
        {"name": "John Smith", "email": "john.smith@example.com"},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 1
    assert merged_count == 1
    assert cleaned.iloc[0]["email"] == "john.smith@example.com"


def test_custom_index_preservation() -> None:
    """Verify original index labels are preserved for surviving rows."""
    df = pd.DataFrame(
        [
            {"name": "Alice Smith", "email": None},
            {"name": "Bob Jones", "email": "bob@example.com"},
            {"name": "Alice Smith", "email": "alice@example.com"},
        ],
        index=[101, 102, 103],
    )

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert merged_count == 1
    assert list(cleaned.index) == [102, 103]


def test_preexisting_flag_reason_retained() -> None:
    """Verify existing flag reason values are preserved when suspected duplicate is flagged."""
    df = pd.DataFrame([
        {"name": "Alice Smith", "flag_reason": "INVALID_PHONE"},
        {"name": "Alicia Smith", "flag_reason": ""},
    ])

    cleaned, merged_count, flagged_count = find_and_handle_duplicates(df, "name")

    assert len(cleaned) == 2
    assert merged_count == 0
    assert flagged_count == 2
    assert "INVALID_PHONE" in cleaned.iloc[0]["flag_reason"]
    assert "SUSPECTED_DUPLICATE" in cleaned.iloc[0]["flag_reason"]
    assert cleaned.iloc[1]["flag_reason"] == "SUSPECTED_DUPLICATE"
