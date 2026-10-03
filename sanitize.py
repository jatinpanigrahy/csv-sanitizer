"""CLI entry point for the CSV Sanitizer pipeline.

Provides a command-line interface to normalize, deduplicate, and audit
tabular CSV files.
"""

import argparse
from pathlib import Path
import sys

from cleaner import config as config_loader
from cleaner import pipeline


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser for the CSV Sanitizer.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Sanitize messy CSV data and generate an audit report."
    )
    parser.add_argument(
        "input",
        help="Path to raw source CSV file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Destination path for sanitized output CSV file (default: <input_stem>_clean.csv in input directory).",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Destination path for audit report markdown file (default: <input_stem>_report.md in input directory).",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml in current working directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run the CSV sanitization pipeline.

    Args:
        argv: Optional list of argument strings. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' does not exist.", file=sys.stderr)
        return 1

    if args.output is None:
        args.output = str(input_path.parent / f"{input_path.stem}_clean.csv")

    if args.report is None:
        args.report = str(input_path.parent / f"{input_path.stem}_report.md")

    config = config_loader.load(args.config)
    stats = pipeline.run(args.input, args.output, args.report, config)

    print("Sanitization completed successfully.")
    print(f"  Input file: {args.input} ({stats.rows_input} rows)")
    print(f"  Output CSV: {args.output} ({stats.rows_output} rows)")
    print(f"  Audit report: {args.report}")
    print(f"  Names normalized: {stats.names_normalized}")
    print(f"  Phones standardized: {stats.phones_normalized}")
    print(f"  Dates standardized: {stats.dates_normalized}")
    print(f"  Emails missing: {stats.emails_missing}")
    print(f"  Duplicates merged: {stats.duplicates_merged}")
    print(f"  Duplicates flagged: {stats.duplicates_flagged}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
