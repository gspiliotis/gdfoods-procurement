# Get Suppliers - myDATA Invoice Fetcher

This Python project fetches invoice data from the Greek AADE myDATA API and generates Excel or CSV reports with aggregated quantities by supplier and item.

## Features

- Fetches all invoice data from myDATA API for a given date range
- Optionally filters by supplier VAT numbers from a file
- Handles automatic pagination for large datasets
- Aggregates quantities by (issuer, item, date) tuples
- Supports per-supplier date adjustments
- Generates Excel or CSV output files
- Can export discovered VAT numbers to a file for later use

## Requirements

- Python 3.7 or higher
- Internet connection to access the myDATA API

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API credentials (see `.env.example`):

```
MYDATA_USER_ID=your_user_id_here
MYDATA_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

Fetch all invoices for a date range (no filtering):
```bash
python fetch_invoices.py <start_date> <end_date>
```

Fetch and filter by specific VAT numbers:
```bash
python fetch_invoices.py <start_date> <end_date> <vat_file>
```

### Arguments

- `start_date`: Start date in YYYY-MM-DD format (e.g., 2025-12-01)
- `end_date`: End date in YYYY-MM-DD format (e.g., 2025-12-31)
- `vat_file` (optional): Path to a text file containing issuer VAT numbers to filter by. If omitted, all invoices for the period are included.

### Optional Arguments

- `-o, --output`: Output file name without extension (default: invoice_report)
- `-f, --format`: Output format - xlsx, csv, or both (default: xlsx)
- `--vat-out`: Output file to write all unique VAT numbers found in the fetched invoices. Useful for discovering suppliers and creating a `vat_numbers.txt` for future runs.

### Examples

Fetch all invoices for January 2026 and discover all supplier VAT numbers:
```bash
python fetch_invoices.py 2026-01-01 2026-01-31 --vat-out discovered_vats.txt
```

Fetch and filter by specific suppliers, output as Excel:
```bash
python fetch_invoices.py -f xlsx -o december_report 2025-12-01 2025-12-31 vat_numbers.txt
```

Generate both Excel and CSV with custom output name:
```bash
python fetch_invoices.py 2025-12-01 2025-12-31 vat_numbers.txt -o december_report -f both
```

Generate only CSV:
```bash
python fetch_invoices.py 2025-12-01 2025-12-31 vat_numbers.txt -f csv
```

## VAT Numbers File Format

Create a text file (e.g., `vat_numbers.txt`) with one VAT number per line, followed by a date adjustment value (in days). You can add comments using the `#` character:

```
# Supplier VAT numbers
# Format: VAT_NUMBER  DATE_ADJUSTMENT  # optional comment

094254743  0   # ZACO - no date adjustment
998117733  -1  # bellemeat - shift dates back 1 day
998603201  0   # Daily Taste
095283785  0   # Lydia's
```

- `DATE_ADJUSTMENT`: Integer number of days to shift invoice dates for this supplier (0 = no shift, -1 = back one day, etc.). Defaults to 0 if omitted.
- Lines starting with `#` are treated as comments and ignored
- Inline comments: anything after `#` on a line is ignored
- Empty lines are ignored

The `--vat-out` option generates a file in this same format (with date adjustment defaulting to 0), so you can use it as a starting point and edit the adjustments as needed.

## Output Format

The generated report contains:

- **Rows**: One row per unique (issuer name, item description) combination
- **Columns**:
  - Column 1: Issuer name (supplier)
  - Column 2: Item description
  - Remaining columns: Dates (one column per date found in the data)
- **Header rows**: First row has dates, second row has Greek day names
- **Values**: Aggregated quantities for each item on each date

### Excel Output

The Excel file includes:
- Bold header rows
- Auto-adjusted column widths
- Empty cells for dates with no quantities

### CSV Output

The CSV file uses semicolon (;) as delimiter and follows this format:
```
;;2025-12-01;2025-12-08
;;Δευτέρα;Δευτέρα
SUPPLIER NAME;ITEM DESCRIPTION;12;20
```

## API Configuration

The script loads API credentials from a `.env` file:

- `MYDATA_USER_ID`: Your AADE user ID
- `MYDATA_API_KEY`: Your Ocp-Apim-Subscription-Key
- API Endpoint: `https://mydatapi.aade.gr/myDATA/RequestDocs`

## How It Works

1. Fetches all invoices for the specified date range from myDATA API (without VAT filtering)
2. Handles pagination automatically using continuation tokens
3. Parses XML responses to extract issuer name, issuer VAT, item descriptions, issue dates, and quantities
4. If `--vat-out` is specified, writes all unique issuer VAT numbers to the output file
5. If a VAT file is provided, filters records to only include matching issuer VAT numbers and applies per-supplier date adjustments
6. Aggregates quantities by (issuer, item, date)
7. Generates Excel and/or CSV output

## Troubleshooting

### No data returned

- Check the date range includes actual invoices
- Ensure API credentials are valid in `.env`
- Check internet connection

### No data after filtering

- Verify the VAT numbers in your file match the issuer VAT numbers (not receiver)
- Run with `--vat-out` first to discover what VAT numbers exist in the data

### XML parsing errors

The script will log parsing errors to stderr but continue processing other records.

### API errors

Connection errors and API errors are logged to stderr with details.

## License

This project is provided as-is for internal use.
