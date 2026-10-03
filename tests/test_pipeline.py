"""Integration tests for the CSV Sanitizer pipeline.

Validates end-to-end execution of data ingestion, multi-field normalization,
fuzzy deduplication, output file generation, and CLI entry point functionality.
"""

from pathlib import Path
import shutil

import pandas as pd
import pytest

from cleaner import config, pipeline
import sanitize

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DIRTY_CSV_PATH = FIXTURES_DIR / "dirty.csv"
EXPECTED_CLEAN_CSV_PATH = FIXTURES_DIR / "expected_clean.csv"


def test_pipeline_integration_end_to_end(tmp_path: Path) -> None:
    """Execute the end-to-end pipeline on dirty.csv and assert output matches expected_clean.csv."""
    # 1. Copy dirty.csv to a temporary directory
    input_csv = tmp_path / "dirty.csv"
    shutil.copy(DIRTY_CSV_PATH, input_csv)

    output_csv = tmp_path / "cleaned.csv"
    report_md = tmp_path / "report.md"

    # 2. Run pipeline.run on it using default config
    cfg = config.load()
    stats = pipeline.run(
        input_path=str(input_csv),
        output_path=str(output_csv),
        report_path=str(report_md),
        config=cfg,
    )

    # Verify execution metrics
    assert stats.rows_input == 5
    assert stats.rows_output == 4
    assert stats.names_normalized == 5
    assert stats.phones_normalized == 5
    assert stats.dates_normalized == 5
    assert stats.emails_missing == 2
    assert stats.duplicates_merged == 1
    assert stats.duplicates_flagged == 0

    # Verify output files exist and are populated
    assert output_csv.exists()
    assert report_md.exists()
    assert report_md.stat().st_size > 0

    # 3. Load output CSV and expected_clean.csv
    actual_df = pd.read_csv(output_csv)
    expected_df = pd.read_csv(EXPECTED_CLEAN_CSV_PATH)

    # 4. Assert DataFrames are equal
    pd.testing.assert_frame_equal(actual_df, expected_df)


def test_cli_execution_with_default_paths(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI entry point operates correctly with default output and report paths."""
    input_csv = tmp_path / "test_data.csv"
    shutil.copy(DIRTY_CSV_PATH, input_csv)

    expected_output = tmp_path / "test_data_clean.csv"
    expected_report = tmp_path / "test_data_report.md"

    exit_code = sanitize.main([str(input_csv)])

    assert exit_code == 0
    assert expected_output.exists()
    assert expected_report.exists()

    actual_df = pd.read_csv(expected_output)
    expected_df = pd.read_csv(EXPECTED_CLEAN_CSV_PATH)
    pd.testing.assert_frame_equal(actual_df, expected_df)

    captured = capsys.readouterr()
    assert "Sanitization completed successfully" in captured.out
    assert "Rows processed: 5" in captured.out or "5 rows" in captured.out


def test_cli_execution_with_custom_flags(tmp_path: Path) -> None:
    """Verify CLI flags for explicit output and report destinations."""
    input_csv = tmp_path / "sample.csv"
    shutil.copy(DIRTY_CSV_PATH, input_csv)

    custom_output = tmp_path / "custom" / "result.csv"
    custom_report = tmp_path / "custom" / "summary.md"

    exit_code = sanitize.main([
        str(input_csv),
        "--output",
        str(custom_output),
        "--report",
        str(custom_report),
    ])

    assert exit_code == 0
    assert custom_output.exists()
    assert custom_report.exists()

    actual_df = pd.read_csv(custom_output)
    expected_df = pd.read_csv(EXPECTED_CLEAN_CSV_PATH)
    pd.testing.assert_frame_equal(actual_df, expected_df)


def test_cli_missing_input_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI gracefully handles missing input file with error exit code."""
    missing_file = tmp_path / "non_existent.csv"

    exit_code = sanitize.main([str(missing_file)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
