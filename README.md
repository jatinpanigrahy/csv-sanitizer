# CSV Sanitizer

CSV Sanitizer is a robust, configurable Python utility designed to clean messy, real-world tabular data. It standardizes heterogeneous formats across common business fields, applies intelligent fuzzy deduplication, and generates an audit-ready Markdown report summarizing every modification.

---

## Features

- **Name Normalization**: Standardizes personal and contact names into Title Case, strips extraneous whitespace, and tracks modified rows.
- **Email Sanitization**: Converts email addresses to lowercase conforming to RFC standards, trims whitespace, and tallies missing values.
- **Date Standardization**: Parses varied and mixed date formats (ISO, US, European, timestamps) into a uniform target format (default: `YYYY-MM-DD`), preserving unparseable entries safely.
- **International Phone Formatting**: Validates and standardizes telephone numbers into the international E.164 format (e.g., `+14155552671`) using Google's `phonenumbers` library (`libphonenumber`), with fallback support for regional numbers missing country codes.
- **Tiered Fuzzy Deduplication**: Evaluates records using token-sort string similarity (`RapidFuzz`):
  - **Auto-Merge (Score &ge; 90)**: Merges high-confidence duplicate records automatically, retaining the row with the most complete attributes.
  - **Human-in-the-Loop Flagging (70 &le; Score < 90)**: Flags borderline duplicates with a `flag_reason = SUSPECTED_DUPLICATE` annotation in the output CSV for manual verification.
- **Audit Reporting**: Automatically compiles a companion Markdown report with detailed telemetry, transformation counts, and flagged review notes.

---

## Installation & Setup

CSV Sanitizer uses [`uv`](https://github.com/astral-sh/uv) for fast and reliable Python package management.

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

Run the sanitizer directly via the command-line interface:

```bash
python sanitize.py <input.csv>
```

By default, the tool writes the sanitized dataset to `<input_stem>_clean.csv` and the audit report to `<input_stem>_report.md` within the same folder as the input file.

### CLI Options

| Flag | Argument | Description | Default |
|---|---|---|---|
| `input` | Path | Positional path to the raw source CSV file. | *(Required)* |
| `--output` | Path | Custom destination path for the sanitized CSV. | `<input_stem>_clean.csv` |
| `--report` | Path | Custom destination path for the Markdown audit report. | `<input_stem>_report.md` |
| `--config` | Path | Path to custom YAML configuration file. | `config.yaml` |

#### Example

```bash
python sanitize.py sample/sample_input.csv --output sample/cleaned.csv --report sample/report.md --config config.yaml
```

---

## Configuration

Custom column headers, parsing defaults, and deduplication thresholds can be adjusted without code changes using `config.yaml`.

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

If `config.yaml` is missing or keys are omitted, the application automatically applies built-in defaults via recursive deep merging.

---

## Architecture & Design Decisions

The application follows a four-layer architecture engineered for clean separation of concerns and high testability:

1. **Configuration Layer (`cleaner/config.py`)**: Loads user YAML definitions and performs recursive fallback merges against default settings, guaranteeing zero-failure operation when settings are partial.
2. **Normalizers Layer (`cleaner/normalizers.py`)**: Contains pure, stateless functions for individual data domains (names, emails, phones, dates). Each function accepts a pandas Series and returns transformed values along with modification counts, keeping domain logic isolated from I/O.
3. **Pipeline Layer (`cleaner/pipeline.py` & `cleaner/deduplicator.py`)**: Orchestrates the sequential execution—reading raw data, applying normalizers, executing tiered fuzzy deduplication, generating the Markdown audit report via `cleaner/reporter.py`, and writing outputs.
4. **CLI Layer (`sanitize.py`)**: Handles argument parsing, path validation, execution delegation, and terminal summary reporting.

This layered structure ensures each transformation step and deduplication rule can be unit-tested independently without mocking filesystem operations or CLI state.

---

## Limitations & Scalability

### Deduplication Complexity

The fuzzy deduplicator utilizes an pairwise comparison algorithm with $O(n^2)$ time complexity to detect approximate string matches across records:

- **Optimal Scope**: Datasets up to **~10,000 rows**, where pairwise comparison finishes quickly and memory overhead remains low.
- **Scale Considerations**: For larger datasets (tens of thousands to millions of rows), comparing every row against all subsequent rows becomes computationally prohibitive.
- **Scaling Path**: Production deployments handling massive volumes should introduce **blocking strategies** (such as partitioning records by first-letter index, postal code, or phonetic encodings like Soundex/Double Metaphone) or locality-sensitive hashing (LSH) to restrict fuzzy comparisons to candidate subsets.

---

## License

This project is licensed under the MIT License.