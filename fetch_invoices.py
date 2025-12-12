#!/usr/bin/env python3
"""
Fetch invoice data from myDATA API and generate Excel spreadsheet with aggregated quantities.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import requests
from openpyxl import Workbook
from openpyxl.styles import Font

# API Constants
USER_ID = "gdfoods"
API_KEY = "988ed25ba9de0d51813d0084498edb21"
API_BASE_URL = "https://mydatapi.aade.gr/myDATA/RequestDocs"


def convert_date_to_api_format(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to DD/MM/YYYY format for API.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Date in DD/MM/YYYY format
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d/%m/%Y")


def fetch_invoices(
    date_from: str,
    date_to: str,
    receiver_vat_number: str,
    next_partition_key: Optional[str] = None,
    next_row_key: Optional[str] = None
) -> str:
    """
    Fetch invoices from myDATA API.

    Args:
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
        receiver_vat_number: VAT number of the receiver
        next_partition_key: Pagination key for next partition
        next_row_key: Pagination key for next row

    Returns:
        XML response as string
    """
    # Convert dates to DD/MM/YYYY format for API
    api_date_from = convert_date_to_api_format(date_from)
    api_date_to = convert_date_to_api_format(date_to)

    params = {
        "mark": "1",
        "dateFrom": api_date_from,
        "dateTo": api_date_to,
        "receiverVatNumber": receiver_vat_number
    }

    if next_partition_key:
        params["nextPartitionKey"] = next_partition_key
    if next_row_key:
        params["nextRowKey"] = next_row_key

    headers = {
        "aade-user-id": USER_ID,
        "Ocp-Apim-Subscription-Key": API_KEY
    }

    try:
        response = requests.get(API_BASE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for VAT {receiver_vat_number}: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response text: {e.response.text}", file=sys.stderr)
        return ""


def parse_invoices(xml_content: str) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Parse XML response and extract invoice data.

    Args:
        xml_content: XML response as string

    Returns:
        Tuple of (list of invoice records, next_partition_key, next_row_key)
    """
    if not xml_content:
        return [], None, None

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        return [], None, None

    # Define namespace
    ns = {'ns': 'http://www.aade.gr/myDATA/invoice/v1.0'}

    # Extract pagination tokens
    next_partition_key = None
    next_row_key = None

    continuation_token = root.find("ns:continuationToken", ns)
    if continuation_token is not None:
        npk = continuation_token.find("ns:nextPartitionKey", ns)
        nrk = continuation_token.find("ns:nextRowKey", ns)
        if npk is not None:
            next_partition_key = npk.text
        if nrk is not None:
            next_row_key = nrk.text

    # Extract invoice data
    records = []
    # Find invoicesDoc container first
    invoices_doc = root.find("ns:invoicesDoc", ns)
    if invoices_doc is None:
        return records, next_partition_key, next_row_key

    invoices = invoices_doc.findall("ns:invoice", ns)

    for invoice in invoices:
        # Get issuer name
        issuer = invoice.find("ns:issuer", ns)
        if issuer is None:
            continue

        issuer_name_elem = issuer.find("ns:name", ns)
        if issuer_name_elem is None or not issuer_name_elem.text:
            continue
        issuer_name = issuer_name_elem.text.strip()

        # Get issue date
        invoice_header = invoice.find("ns:invoiceHeader", ns)
        if invoice_header is None:
            continue

        issue_date_elem = invoice_header.find("ns:issueDate", ns)
        if issue_date_elem is None or not issue_date_elem.text:
            continue
        issue_date = issue_date_elem.text.strip()

        # Get invoice details
        for detail in invoice.findall("ns:invoiceDetails", ns):
            item_descr_elem = detail.find("ns:itemDescr", ns)
            quantity_elem = detail.find("ns:quantity", ns)

            if item_descr_elem is None or quantity_elem is None:
                continue

            if not item_descr_elem.text or not quantity_elem.text:
                continue

            item_descr = item_descr_elem.text.strip()
            try:
                quantity = float(quantity_elem.text)
            except ValueError:
                continue

            records.append({
                "issuer_name": issuer_name,
                "item_descr": item_descr,
                "issue_date": issue_date,
                "quantity": quantity
            })

    return records, next_partition_key, next_row_key


def fetch_all_invoices(date_from: str, date_to: str, vat_numbers: List[str]) -> List[Dict]:
    """
    Fetch all invoices for multiple VAT numbers with pagination.

    Args:
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
        vat_numbers: List of receiver VAT numbers

    Returns:
        List of all invoice records
    """
    all_records = []

    for vat_number in vat_numbers:
        vat_number = vat_number.strip()
        if not vat_number:
            continue

        print(f"Fetching invoices for VAT: {vat_number}")

        next_partition_key = None
        next_row_key = None
        page = 1

        while True:
            xml_content = fetch_invoices(
                date_from, date_to, vat_number,
                next_partition_key, next_row_key
            )

            if not xml_content:
                break

            records, next_partition_key, next_row_key = parse_invoices(xml_content)
            all_records.extend(records)

            print(f"  Page {page}: Found {len(records)} invoice items")
            page += 1

            # If no pagination tokens, we're done with this VAT number
            if not next_partition_key or not next_row_key:
                break

        print(f"  Total items for {vat_number}: {len([r for r in all_records if vat_number in str(r)])}")

    return all_records


def get_greek_day_name(date_str: str) -> str:
    """
    Get Greek day name from date string.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Greek day name
    """
    greek_days = {
        0: "Δευτέρα",     # Monday
        1: "Τρίτη",       # Tuesday
        2: "Τετάρτη",     # Wednesday
        3: "Πέμπτη",      # Thursday
        4: "Παρασκευή",   # Friday
        5: "Σάββατο",     # Saturday
        6: "Κυριακή"      # Sunday
    }
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return greek_days[date_obj.weekday()]


def aggregate_data(records: List[Dict]) -> Tuple[Dict[Tuple[str, str], Dict[str, float]], List[str]]:
    """
    Aggregate quantities by (issuer, item, date).

    Args:
        records: List of invoice records

    Returns:
        Tuple of (aggregated data dict, sorted list of dates)
    """
    # Dictionary: (issuer_name, item_descr) -> {date: quantity}
    aggregated = defaultdict(lambda: defaultdict(float))
    dates_set = set()

    for record in records:
        key = (record["issuer_name"], record["item_descr"])
        date = record["issue_date"]
        quantity = record["quantity"]

        aggregated[key][date] += quantity
        dates_set.add(date)

    # Sort dates
    sorted_dates = sorted(list(dates_set))

    return aggregated, sorted_dates


def generate_excel(aggregated_data: Dict, dates: List[str], output_file: str):
    """
    Generate Excel file with aggregated data.

    Args:
        aggregated_data: Dictionary of aggregated quantities
        dates: Sorted list of dates
        output_file: Output Excel file path
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice Quantities"

    # Write first header row (dates)
    ws.cell(1, 1, "Issuer")
    ws.cell(1, 2, "Item Description")
    for col_idx, date in enumerate(dates, start=3):
        ws.cell(1, col_idx, date)

    # Write second header row (day names in Greek)
    for col_idx, date in enumerate(dates, start=3):
        ws.cell(2, col_idx, get_greek_day_name(date))

    # Make headers bold
    for col in range(1, len(dates) + 3):
        ws.cell(1, col).font = Font(bold=True)
        ws.cell(2, col).font = Font(bold=True)

    # Write data rows
    row_idx = 3
    for (issuer_name, item_descr), date_quantities in sorted(aggregated_data.items()):
        ws.cell(row_idx, 1, issuer_name)
        ws.cell(row_idx, 2, item_descr)

        for col_idx, date in enumerate(dates, start=3):
            quantity = date_quantities.get(date, 0)
            if quantity > 0:
                ws.cell(row_idx, col_idx, quantity)

        row_idx += 1

    # Auto-adjust column widths
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 60
    for col_idx in range(3, len(dates) + 3):
        ws.column_dimensions[chr(64 + col_idx)].width = 12

    wb.save(output_file)
    print(f"\nExcel file generated: {output_file}")


def generate_csv(aggregated_data: Dict, dates: List[str], output_file: str):
    """
    Generate CSV file with aggregated data.

    Args:
        aggregated_data: Dictionary of aggregated quantities
        dates: Sorted list of dates
        output_file: Output CSV file path
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write first header row (dates)
        f.write(";;")
        f.write(";".join(dates))
        f.write("\n")

        # Write second header row (day names in Greek)
        f.write(";;")
        f.write(";".join([get_greek_day_name(date) for date in dates]))
        f.write("\n")

        # Write data rows
        for (issuer_name, item_descr), date_quantities in sorted(aggregated_data.items()):
            row = [issuer_name, item_descr]
            for date in dates:
                quantity = date_quantities.get(date, 0)
                row.append(str(int(quantity)) if quantity > 0 else "")

            f.write(";".join(row))
            f.write("\n")

    print(f"\nCSV file generated: {output_file}")


def read_vat_numbers(filename: str) -> List[str]:
    """
    Read VAT numbers from file (one per line).
    Lines starting with # are treated as comments and ignored.
    Anything after a # character on a line is also ignored.

    Args:
        filename: Path to file containing VAT numbers

    Returns:
        List of VAT numbers
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            vat_numbers = []
            for line in f:
                # Remove comments (anything after #)
                line = line.split('#')[0].strip()
                # Add non-empty lines
                if line:
                    vat_numbers.append(line)
            return vat_numbers
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}", file=sys.stderr)
        sys.exit(1)


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch invoice data from myDATA API and generate Excel/CSV report"
    )
    parser.add_argument(
        "start_date",
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "end_date",
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "vat_file",
        help="File containing receiver VAT numbers (one per line)"
    )
    parser.add_argument(
        "-o", "--output",
        default="invoice_report",
        help="Output file name (without extension, default: invoice_report)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["xlsx", "csv", "both"],
        default="xlsx",
        help="Output format (default: xlsx)"
    )

    args = parser.parse_args()

    # Validate dates
    if not validate_date(args.start_date):
        print(f"Error: Invalid start date '{args.start_date}'. Use YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)

    if not validate_date(args.end_date):
        print(f"Error: Invalid end date '{args.end_date}'. Use YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)

    # Read VAT numbers
    vat_numbers = read_vat_numbers(args.vat_file)
    if not vat_numbers:
        print("Error: No VAT numbers found in file", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(vat_numbers)} VAT number(s) to process")
    print(f"Date range: {args.start_date} to {args.end_date}\n")

    # Fetch all invoices
    records = fetch_all_invoices(args.start_date, args.end_date, vat_numbers)

    if not records:
        print("\nNo invoice data found")
        sys.exit(0)

    print(f"\nTotal invoice items fetched: {len(records)}")

    # Aggregate data
    aggregated_data, dates = aggregate_data(records)
    print(f"Unique (issuer, item) combinations: {len(aggregated_data)}")
    print(f"Date range in data: {dates[0]} to {dates[-1]}" if dates else "No dates")

    # Generate output
    if args.format in ["xlsx", "both"]:
        generate_excel(aggregated_data, dates, f"{args.output}.xlsx")

    if args.format in ["csv", "both"]:
        generate_csv(aggregated_data, dates, f"{args.output}.csv")

    print("\nDone!")


if __name__ == "__main__":
    main()
