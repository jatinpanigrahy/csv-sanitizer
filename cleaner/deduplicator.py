"""Deduplication and duplicate resolution module for the CSV Sanitizer pipeline.

This module provides fuzzy-matching capabilities to identify potential duplicate
records across tabular datasets using RapidFuzz. It automatically merges records
meeting a high-confidence similarity threshold based on data richness and flags
borderline matches for human auditing.
"""

from typing import Any

import pandas as pd
from rapidfuzz import fuzz


def _count_non_empty(row: pd.Series) -> int:
    """Count non-null, non-blank values in a row, excluding pipeline metadata columns.

    Args:
        row: A pandas Series representing a single dataset row.

    Returns:
        The total count of valid, non-empty data attributes.
    """
    count = 0
    for col, val in row.items():
        if col == "flag_reason":
            continue
        if pd.notna(val) and val is not None:
            if isinstance(val, str):
                if val.strip():
                    count += 1
            else:
                count += 1
    return count


def _apply_flag(df: pd.DataFrame, row_idx: int, col_idx: int) -> None:
    """Set or append SUSPECTED_DUPLICATE to the flag_reason column at row_idx.

    Args:
        df: The pandas DataFrame being modified.
        row_idx: Positional integer index of the target row.
        col_idx: Positional integer index of the flag_reason column.
    """
    curr = str(df.iat[row_idx, col_idx]) if pd.notna(df.iat[row_idx, col_idx]) else ""
    if not curr:
        df.iat[row_idx, col_idx] = "SUSPECTED_DUPLICATE"
    elif "SUSPECTED_DUPLICATE" not in curr:
        df.iat[row_idx, col_idx] = f"{curr}; SUSPECTED_DUPLICATE"


def find_and_handle_duplicates(
    df: pd.DataFrame,
    name_column: str,
    auto_merge_threshold: float = 90.0,
    flag_threshold: float = 70.0,
) -> tuple[pd.DataFrame, int, int]:
    """Identify and handle duplicate records using fuzzy string matching.

    Compares name field pairs across records using RapidFuzz token sort ratio.
    Records with similarity at or above auto_merge_threshold are automatically
    merged by retaining the record with the most complete data (or the earlier
    record in case of a tie) and dropping the redundant row. Records with similarity
    between flag_threshold and auto_merge_threshold are retained and flagged with
    'SUSPECTED_DUPLICATE' in the flag_reason column.

    Args:
        df: Input pandas DataFrame to evaluate.
        name_column: Name of the column containing entity names for comparison.
        auto_merge_threshold: Minimum similarity score (0-100) to trigger automatic merging.
            Defaults to 90.0.
        flag_threshold: Minimum similarity score (0-100) to flag records as suspected
            duplicates. Defaults to 70.0.

    Returns:
        A tuple of:
            - cleaned_df: A new DataFrame with merged rows dropped and flag reasons added.
            - merged_count: Number of redundant rows dropped due to auto-merging.
            - flagged_count: Total count of unique rows in the output DataFrame flagged
              as suspected duplicates.

    Raises:
        KeyError: If name_column is not present in a non-empty DataFrame.
    """
    if df.empty:
        cleaned_df = df.copy()
        if "flag_reason" not in cleaned_df.columns:
            cleaned_df["flag_reason"] = pd.Series(dtype=str)
        else:
            cleaned_df["flag_reason"] = cleaned_df["flag_reason"].fillna("").astype(str)
        return cleaned_df, 0, 0

    if name_column not in df.columns:
        raise KeyError(f"Column '{name_column}' not found in DataFrame.")

    working_df = df.copy()
    if "flag_reason" not in working_df.columns:
        working_df["flag_reason"] = ""
    else:
        working_df["flag_reason"] = working_df["flag_reason"].fillna("").astype(str)

    flag_col_idx = int(working_df.columns.get_loc("flag_reason"))
    name_col_idx = int(working_df.columns.get_loc(name_column))

    n = len(working_df)
    to_drop: set[int] = set()
    merged_count = 0

    for i in range(n):
        if i in to_drop:
            continue

        name_i_raw = working_df.iat[i, name_col_idx]
        name_i = "" if pd.isna(name_i_raw) else str(name_i_raw).strip()
        if not name_i:
            continue

        for j in range(i + 1, n):
            if j in to_drop:
                continue

            name_j_raw = working_df.iat[j, name_col_idx]
            name_j = "" if pd.isna(name_j_raw) else str(name_j_raw).strip()
            if not name_j:
                continue

            score = float(fuzz.token_sort_ratio(name_i, name_j))

            if score >= auto_merge_threshold:
                count_i = _count_non_empty(working_df.iloc[i])
                count_j = _count_non_empty(working_df.iloc[j])

                if count_j > count_i:
                    to_drop.add(i)
                    merged_count += 1
                    break
                else:
                    to_drop.add(j)
                    merged_count += 1
            elif score >= flag_threshold:
                _apply_flag(working_df, i, flag_col_idx)
                _apply_flag(working_df, j, flag_col_idx)

    surviving_indices = [idx for idx in range(n) if idx not in to_drop]
    cleaned_df = working_df.iloc[surviving_indices].copy()

    flagged_count = int(
        cleaned_df["flag_reason"].astype(str).str.contains("SUSPECTED_DUPLICATE", regex=False).sum()
    )

    return cleaned_df, merged_count, flagged_count
