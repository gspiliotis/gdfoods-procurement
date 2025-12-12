# Get Suppliers - myDATA Invoice Fetcher

This Python project fetches invoice data from the Greek AADE myDATA API and generates Excel or CSV reports with aggregated quantities by supplier and item.

## Features

- Fetches invoice data from myDATA API for multiple supplier VAT numbers
- Handles automatic pagination for large datasets
- Aggregates quantities by (issuer, item, date) tuples
- Generates Excel or CSV output files
- Supports date range filtering

## Requirements

- Python 3.7 or higher
- Internet connection to access the myDATA API

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python fetch_invoices.py <start_date> <end_date> <vat_file>
```

### Arguments

- `start_date`: Start date in YYYY-MM-DD format (e.g., 2025-12-01)
- `end_date`: End date in YYYY-MM-DD format (e.g., 2025-12-08)
- `vat_file`: Path to a text file containing receiver VAT numbers (one per line)

### Optional Arguments

- `-o, --output`: Output file name without extension (default: invoice_report)
- `-f, --format`: Output format - xlsx, csv, or both (default: xlsx)

### Examples

Generate Excel report for December 2025:
```bash
python fetch_invoices.py 2025-12-01 2025-12-31 vat_numbers.txt
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

Create a text file (e.g., `vat_numbers.txt`) with one VAT number per line. You can add comments using the `#` character - anything after `#` on a line will be ignored:

```
# Supplier VAT numbers
# Lines starting with # are comments

094254743  # ZACO - Main supplier
123456789  # Another supplier
# 987654321  # This VAT is commented out

```

Features:
- Lines starting with `#` are treated as comments and ignored
- Inline comments: anything after `#` on a line is ignored
- Empty lines are ignored

## Output Format

The generated report contains:

- **Rows**: One row per unique (issuer name, item description) combination
- **Columns**:
  - Column 1: Issuer name (supplier)
  - Column 2: Item description
  - Remaining columns: Dates (one column per date found in the data)
- **Values**: Aggregated quantities for each item on each date

### Excel Output

The Excel file includes:
- Bold header row
- Auto-adjusted column widths
- Empty cells for dates with no quantities

### CSV Output

The CSV file uses semicolon (;) as delimiter and follows this format:
```
;;2025-12-01;2025-12-08
SUPPLIER NAME;ITEM DESCRIPTION;12;20
```

## API Configuration

The script uses the following API credentials (configured in the source code):

- User ID: `gdfoods`
- API Key: `988ed25ba9de0d51813d0084498edb21`
- API Endpoint: `https://mydatapi.aade.gr/myDATA/RequestDocs`

To modify these credentials, edit the constants at the top of `fetch_invoices.py`.

## How It Works

1. Reads VAT numbers from the input file
2. For each VAT number, makes API requests to myDATA with:
   - mark=1 (incoming invoices)
   - Date range filter
   - Receiver VAT number filter
3. Handles pagination automatically using continuation tokens
4. Parses XML responses to extract:
   - Issuer name
   - Item descriptions
   - Issue dates
   - Quantities
5. Aggregates quantities by (issuer, item, date)
6. Generates Excel and/or CSV output

## Troubleshooting

### No data returned

- Verify the VAT numbers are correct
- Check the date range includes actual invoices
- Ensure API credentials are valid
- Check internet connection

### XML parsing errors

The script will log parsing errors to stderr but continue processing other records.

### API errors

Connection errors and API errors are logged to stderr with details about which VAT number failed.

## License

This project is provided as-is for internal use.
