"""Unit tests for the markdown report generator module.

Validates the structure, metrics summary table, conditional warning notes,
and file output capabilities of the cleaner.reporter module.
"""

from datetime import datetime
from pathlib import Path

from cleaner.models import CleaningStats
from cleaner.reporter import build_report, write_report


def test_build_report_exact_structure() -> None:
    """Verify that build_report outputs the exact specified markdown structure."""
    stats = CleaningStats(
        input_file="contacts_dirty.csv",
        rows_input=500,
        rows_output=441,
        names_normalized=87,
        phones_normalized=134,
        phones_unparseable=3,
        dates_normalized=201,
        dates_unparseable=2,
        emails_missing=12,
        duplicates_merged=47,
        duplicates_flagged=12,
    )
    fixed_time = datetime(2026, 9, 27, 19, 45, 3)
    report = build_report(stats, run_datetime=fixed_time)

    expected = (
        "# CSV Cleaning Report\n"
        "\n"
        "**Input file:** contacts_dirty.csv\n"
        "**Run date:** 2026-09-27\n"
        "**Run time:** 19:45:03\n"
        "\n"
        "## Summary\n"
        "\n"
        "| Metric | Count |\n"
        "|---|---|\n"
        "| Rows processed | 500 |\n"
        "| Names normalized | 87 |\n"
        "| Phone numbers standardized | 134 |\n"
        "| Phone numbers unparseable (left as-is) | 3 |\n"
        "| Dates standardized | 201 |\n"
        "| Dates unparseable (left as-is) | 2 |\n"
        "| Emails missing | 12 |\n"
        "| Duplicate rows auto-merged | 47 |\n"
        "| Rows flagged for review | 12 |\n"
        "| **Rows in output** | **441** |\n"
        "\n"
        "## Notes\n"
        "\n"
        "- 12 rows contain `flag_reason = SUSPECTED_DUPLICATE`. Review these manually in the output file.\n"
        "- 3 phone numbers could not be parsed and were left unchanged.\n"
        "- 2 date values could not be parsed and were left unchanged.\n"
    )
    assert report == expected


def test_build_report_no_warnings_note() -> None:
    """Verify that zero anomalies yield the fallback 'No warnings or flagged rows.' note."""
    stats = CleaningStats(
        input_file="clean.csv",
        rows_input=10,
        rows_output=10,
        duplicates_flagged=0,
        phones_unparseable=0,
        dates_unparseable=0,
    )
    fixed_time = datetime(2026, 10, 1, 12, 0, 0)
    report = build_report(stats, run_datetime=fixed_time)

    assert "## Notes\n\n- No warnings or flagged rows.\n" in report
    assert "SUSPECTED_DUPLICATE" not in report


def test_build_report_individual_warning_notes() -> None:
    """Verify notes section includes only applicable warnings when some counts are zero."""
    # Only duplicates flagged
    stats_dup = CleaningStats(input_file="test.csv", duplicates_flagged=5)
    report_dup = build_report(stats_dup, run_datetime=datetime(2026, 1, 1, 0, 0, 0))
    assert "- 5 rows contain `flag_reason = SUSPECTED_DUPLICATE`. Review these manually in the output file." in report_dup
    assert "phone numbers could not be parsed" not in report_dup
    assert "date values could not be parsed" not in report_dup

    # Only phones unparseable
    stats_phone = CleaningStats(input_file="test.csv", phones_unparseable=4)
    report_phone = build_report(stats_phone, run_datetime=datetime(2026, 1, 1, 0, 0, 0))
    assert "- 4 phone numbers could not be parsed and were left unchanged." in report_phone
    assert "SUSPECTED_DUPLICATE" not in report_phone
    assert "date values could not be parsed" not in report_phone

    # Only dates unparseable
    stats_date = CleaningStats(input_file="test.csv", dates_unparseable=7)
    report_date = build_report(stats_date, run_datetime=datetime(2026, 1, 1, 0, 0, 0))
    assert "- 7 date values could not be parsed and were left unchanged." in report_date
    assert "SUSPECTED_DUPLICATE" not in report_date
    assert "phone numbers could not be parsed" not in report_date


def test_build_report_default_datetime() -> None:
    """Verify build_report generates valid timestamps when run_datetime is omitted."""
    stats = CleaningStats(input_file="test.csv")
    report = build_report(stats)

    assert "**Run date:** " in report
    assert "**Run time:** " in report


def test_write_report(tmp_path: Path) -> None:
    """Verify that write_report saves content with UTF-8 encoding to disk."""
    dest = tmp_path / "subdir" / "report.md"
    write_report("# Test Report", dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "# Test Report"
