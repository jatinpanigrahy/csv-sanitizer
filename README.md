# CSV Sanitizer

CSV Sanitizer is a configurable Python tool designed to clean messy data in CSV files. It standardizes different formats across common business fields, detects duplicate rows using fuzzy matching, and generates a clear Markdown report summarizing every change made.

---

## Features

- **Name Normalization**: Converts names to Title Case, removes extra whitespace, and tracks how many rows were updated.
- **Email Sanitization**: Converts email addresses to lowercase, trims whitespace, and counts missing values.
- **Date Standardization**: Converts different date formats (ISO, US, European, timestamps) into a single format (default: `YYYY-MM-DD`), while safely keeping unparseable entries unchanged.
- **International Phone Formatting**: Validates and formats phone numbers into the standard international E.164 format (e.g., `+14155552671`) using Google's `phonenumbers` library (`libphonenumber`). It also supports local numbers that are missing a country code.
- **Tiered Fuzzy Deduplication**: Finds similar rows using string matching (`RapidFuzz`):
  - **Auto-Merge (Score &ge; 90)**: Merges high-confidence duplicate records automatically, keeping the row with the most complete information.
  - **Flagging for Review (70 &le; Score < 90)**: Marks borderline duplicates with `flag_reason = SUSPECTED_DUPLICATE` in the output CSV for manual verification.
- **Audit Reporting**: Automatically creates a companion Markdown report with summary stats, change counts, and notes on flagged rows.

---

## Installation & Setup

CSV Sanitizer uses [`uv`](https://github.com/astral-sh/uv) to manage Python packages quickly and reliably.

### Prerequisites

- Python 3.10+
- `uv` installed (`pip install uv` or via standalone installer)

### Setup

```bash
# Clone the repository
git clone https://github.com/jatinpanigrahy/csv-sanitizer.git
cd csv-sanitizer

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

---

## Usage

Run the sanitizer from the command line:

```bash
python sanitize.py <input.csv>
```

By default, the tool saves the cleaned data to `<input_stem>_clean.csv` and the report to `<input_stem>_report.md` in the same folder as the input file.

### CLI Options

| Flag | Argument | Description | Default |
|---|---|---|---|
| `input` | Path | Path to the raw source CSV file. | *(Required)* |
| `--output` | Path | Custom path for saving the cleaned CSV. | `<input_stem>_clean.csv` |
| `--report` | Path | Custom path for saving the Markdown report. | `<input_stem>_report.md` |
| `--config` | Path | Path to a custom YAML configuration file. | `config.yaml` |

#### Example

```bash
python sanitize.py sample/sample_input.csv --output sample/cleaned.csv --report sample/report.md --config config.yaml
```

---

## Configuration

You can customize column names, default settings, and deduplication cutoffs in `config.yaml` without changing any code.

```yaml
columns:
  # Map CSV column headers to sanitizer fields
  name: "name"
  phone: "phone"
  email: "email"
  date: "date"

phone:
  # Fallback two-letter ISO country code when '+' prefix is omitted
  default_country: "US"
  output_format: "E164"

deduplication:
  # RapidFuzz similarity score (0-100) for automatic merging
  auto_merge_threshold: 90
  # RapidFuzz similarity score (0-100) for manual review flagging
  flag_threshold: 70

output:
  # Standard strftime format string for output dates
  date_format: "%Y-%m-%d"
```

If `config.yaml` is missing or some settings are omitted, the tool automatically applies default settings.

---

## Architecture & Design Decisions

The project is organized into four layers so that each part has a single job and is easy to test:

1. **Configuration Layer (`cleaner/config.py`)**: Loads the user's YAML file and applies default settings for anything missing, ensuring the program runs smoothly even with partial settings.
2. **Normalizers Layer (`cleaner/normalizers.py`)**: Contains independent functions for individual data types (names, emails, phones, dates). Each function accepts a pandas Series and returns transformed values along with change counts, keeping cleaning rules separate from file operations.
3. **Pipeline Layer (`cleaner/pipeline.py` & `cleaner/deduplicator.py`)**: Manages the cleaning process from start to finish—reading raw data, applying normalizers, finding duplicates, creating the Markdown report with `cleaner/reporter.py`, and saving output files.
4. **CLI Layer (`sanitize.py`)**: Handles command-line arguments, checks file paths, runs the pipeline, and prints summary results to the terminal.

This structure makes it easy to test each cleaning rule and deduplication step on its own without needing dummy files or fake command-line setups.

---

## Limitations & Scalability

### Deduplication Complexity

The fuzzy deduplicator compares every record against every other record ($O(n^2)$ time complexity) to detect approximate matches:

- **Optimal Scope**: Datasets up to **~10,000 rows**, where comparisons finish quickly and memory use remains low.
- **Scale Considerations**: For larger datasets (tens of thousands to millions of rows), comparing every row against all other rows becomes too slow.
- **Scaling Path**: Production setups handling large volumes should add **blocking strategies** (such as grouping records by first letter, postal code, or phonetic sound) or hashing techniques to limit comparisons to smaller groups.
