# CSV Sanitizer

A robust, configurable Python CLI tool that takes messy, real-world CSV files and transforms them into standardized datasets with automated deduplication and audit reporting.

## Key Features

- **Field Normalization:** Title-cases names, normalizes international phone numbers (E.164), standardizes dates (ISO 8601), and standardizes emails.
- **Intelligent Deduplication:** Uses fuzzy string matching to auto-merge high-confidence duplicate records and flag ambiguous entries for manual inspection.
- **Audit Reporting:** Generates a comprehensive Markdown report summarizing all modifications and flagged rows.
- **Custom Mapping:** Configurable via `config.yaml` to handle custom column names without code modifications.

## Quickstart

### Prerequisites

- Python 3.12+
- `uv` (recommended) or `pip`

### Setup

```bash
# Clone the repository
git clone https://github.com/jatinpanigrahy/csv-sanitizer.git
cd csv-sanitizer

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Basic Usage

```bash
python sanitize.py input.csv
```