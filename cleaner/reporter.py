"""Markdown report generation module for the CSV Sanitizer pipeline.

This module consumes execution statistics captured in a CleaningStats ledger
and formats them into an audit-ready Markdown report detailing row processing counts,
normalization metrics, anomaly records, and human-in-the-loop review notes.
"""

from datetime import datetime
from pathlib import Path

from cleaner.models import CleaningStats


def build_report(
    stats: CleaningStats,
    run_datetime: datetime | None = None,
) -> str:
    """Generate a formatted markdown cleaning summary report from execution statistics.

    Args:
        stats: Telemetry and audit metrics captured during the sanitization run.
        run_datetime: Optional explicit datetime for report generation timestamps.
            Defaults to the current local datetime if not provided.

    Returns:
        A Markdown-formatted report string detailing file metadata, transformation
        metrics, deduplication counts, and audit notes.
    """
    current_time = run_datetime if run_datetime is not None else datetime.now()
    run_date = current_time.strftime("%Y-%m-%d")
    run_time = current_time.strftime("%H:%M:%S")

    notes: list[str] = []
    if stats.duplicates_flagged > 0:
        notes.append(
            f"- {stats.duplicates_flagged} rows contain `flag_reason = SUSPECTED_DUPLICATE`. "
            "Review these manually in the output file."
        )
    if stats.phones_unparseable > 0:
        notes.append(
            f"- {stats.phones_unparseable} phone numbers could not be parsed and were left unchanged."
        )
    if stats.dates_unparseable > 0:
        notes.append(
            f"- {stats.dates_unparseable} date values could not be parsed and were left unchanged."
        )

    if not notes:
        notes.append("- No warnings or flagged rows.")

    report_lines = [
        "# CSV Cleaning Report",
        "",
        f"**Input file:** {stats.input_file}",
        f"**Run date:** {run_date}",
        f"**Run time:** {run_time}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Rows processed | {stats.rows_input} |",
        f"| Names normalized | {stats.names_normalized} |",
        f"| Phone numbers standardized | {stats.phones_normalized} |",
        f"| Phone numbers unparseable (left as-is) | {stats.phones_unparseable} |",
        f"| Dates standardized | {stats.dates_normalized} |",
        f"| Dates unparseable (left as-is) | {stats.dates_unparseable} |",
        f"| Emails missing | {stats.emails_missing} |",
        f"| Duplicate rows auto-merged | {stats.duplicates_merged} |",
        f"| Rows flagged for review | {stats.duplicates_flagged} |",
        f"| **Rows in output** | **{stats.rows_output}** |",
        "",
        "## Notes",
        "",
        *notes,
    ]

    return "\n".join(report_lines) + "\n"


def write_report(report_content: str, output_path: str | Path) -> None:
    """Write generated markdown report to disk.

    Args:
        report_content: The formatted markdown report text.
        output_path: File system destination path for the report.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_content, encoding="utf-8")
