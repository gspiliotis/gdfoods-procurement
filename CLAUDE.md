# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-script Python CLI tool (`fetch_invoices.py`) that fetches invoice data from the Greek AADE myDATA API and generates Excel/CSV reports with quantities aggregated by supplier and item per date.

## Environment Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

API credentials must be in a `.env` file (`MYDATA_USER_ID`, `MYDATA_API_KEY`). See `.env.example`.

## Running the Script

```bash
# Fetch all invoices for a period
python fetch_invoices.py 2026-01-01 2026-01-31

# Filter by VAT numbers file
python fetch_invoices.py 2025-12-01 2025-12-31 vat_numbers.txt -o report -f xlsx

# Discover all supplier VAT numbers
python fetch_invoices.py 2026-01-01 2026-01-31 --vat-out discovered_vats.txt
```

Arguments: `<start_date> <end_date> [vat_file]` with options `-o` (output name), `-f` (xlsx/csv/both), `--vat-out` (export unique VATs).

## Architecture

The script follows a pipeline: **fetch → parse → filter → aggregate → output**.

1. **Fetch**: Calls myDATA `RequestDocs` API (XML) with date range, handles pagination via continuation tokens. No per-VAT API filtering — fetches everything in one pass.
2. **Parse**: Extracts issuer name, issuer VAT, item descriptions, dates, quantities from XML (namespace: `http://www.aade.gr/myDATA/invoice/v1.0`).
3. **Filter** (optional): If a VAT file is provided, filters records by issuer VAT number and applies per-supplier date adjustments.
4. **Aggregate**: Groups quantities into `(issuer_name, item_descr) → {date: quantity}` structure.
5. **Output**: Generates Excel (openpyxl) or semicolon-delimited CSV with two header rows (dates + Greek day names).

## Key Conventions

- Dates use `YYYY-MM-DD` internally, converted to `DD/MM/YYYY` for the API.
- VAT file format: `VAT_NUMBER  DATE_ADJUSTMENT  # comment` — date adjustment shifts invoice dates per supplier.
- The `--vat-out` file uses the same format as the VAT input file, so it can be edited and reused.
- CSV uses semicolon (`;`) as delimiter, not comma.
- No tests or linting are configured.
