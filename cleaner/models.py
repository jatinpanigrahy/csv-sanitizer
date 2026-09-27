"""Data models and telemetry tracking for the CSV Sanitizer pipeline.

This module provides data structures utilized across processing stages to record
transformation metrics, audit anomalies, and capture execution results.
"""

from dataclasses import dataclass


@dataclass
class CleaningStats:
    """Execution metrics and audit ledger for CSV transformation jobs.

    Tracks initial row counts, individual field normalizations, unparseable
    data anomalies, duplicate resolution results, and final output counts.
    """

    # Source file metadata
    input_file: str = ""

    # Processing volume metrics
    rows_input: int = 0
    rows_output: int = 0

    # Normalization metrics
    names_normalized: int = 0
    phones_normalized: int = 0
    phones_unparseable: int = 0
    emails_missing: int = 0
    dates_normalized: int = 0
    dates_unparseable: int = 0

    # Deduplication metrics
    duplicates_merged: int = 0
    duplicates_flagged: int = 0
