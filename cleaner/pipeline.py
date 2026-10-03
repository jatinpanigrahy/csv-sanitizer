"""Pipeline orchestration module for the CSV Sanitizer.

This module coordinates data loading, sequential column sanitization,
fuzzy duplicate detection and resolution, telemetry collection, and report generation.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from cleaner.config import DEFAULTS, _deep_merge
from cleaner.deduplicator import find_and_handle_duplicates
from cleaner.models import CleaningStats
from cleaner.normalizers import (
    normalize_dates,
    normalize_emails,
    normalize_names,
    normalize_phones,
)
from cleaner.reporter import build_report, write_report


def run(
    input_path: str,
    output_path: str,
    report_path: str,
    config: dict,
) -> CleaningStats:
    """Execute the end-to-end CSV sanitization pipeline.

    Reads raw tabular data from disk, sequentially applies normalization across
    configured columns (names, phone numbers, email addresses, dates), executes
    fuzzy duplicate detection and tiered resolution, writes the cleaned dataset to CSV,
    and outputs an audit report in Markdown format.

    Args:
        input_path: Path to the raw source CSV file.
        output_path: Destination path for the sanitized output CSV file.
        report_path: Destination path for the Markdown execution audit report.
        config: Configuration dictionary specifying column mappings,
            normalization parameters, and deduplication thresholds.

    Returns:
        A CleaningStats instance containing complete telemetry and audit counts
        for the sanitization run.
    """
    resolved_config = _deep_merge(DEFAULTS, config) if config else DEFAULTS

    input_file_path = Path(input_path)
    df = pd.read_csv(input_file_path)

    stats = CleaningStats(
        input_file=input_file_path.name,
        rows_input=len(df),
    )

    # 1. Normalize Names
    name_col = resolved_config["columns"]["name"]
    if name_col in df.columns:
        df[name_col], stats.names_normalized = normalize_names(df[name_col])

    # 2. Normalize Phone Numbers
    phone_col = resolved_config["columns"]["phone"]
    default_country = resolved_config["phone"]["default_country"]
    if phone_col in df.columns:
        df[phone_col], stats.phones_normalized, stats.phones_unparseable = normalize_phones(
            df[phone_col], default_country=default_country
        )

    # 3. Normalize Email Addresses
    email_col = resolved_config["columns"]["email"]
    if email_col in df.columns:
        df[email_col], stats.emails_missing = normalize_emails(df[email_col])

    # 4. Normalize Dates
    date_col = resolved_config["columns"]["date"]
    date_format = resolved_config["output"]["date_format"]
    if date_col in df.columns:
        df[date_col], stats.dates_normalized, stats.dates_unparseable = normalize_dates(
            df[date_col], target_format=date_format
        )

    # 5. Fuzzy Deduplication & Conflict Resolution
    auto_merge_threshold = float(resolved_config["deduplication"]["auto_merge_threshold"])
    flag_threshold = float(resolved_config["deduplication"]["flag_threshold"])
    df, stats.duplicates_merged, stats.duplicates_flagged = find_and_handle_duplicates(
        df,
        name_column=name_col,
        auto_merge_threshold=auto_merge_threshold,
        flag_threshold=flag_threshold,
    )

    # 6. Final Row Counts
    stats.rows_output = len(df)

    # 7. Write Cleaned Output CSV
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # 8 & 9. Generate and Write Markdown Report
    report_content = build_report(stats)
    write_report(report_content, report_path)

    # 10. Return Telemetry Ledger
    return stats
