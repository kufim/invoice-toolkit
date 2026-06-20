import csv
from collections import Counter
from pathlib import Path

from . import extraction

FIELDS = ["file", "invoice_number", "vendor", "date", "currency", "total"]


def process_folder(folder):
    pdfs = sorted(Path(folder).glob("*.pdf"))
    return [extraction.extract_invoice(p) for p in pdfs]


def write_csv(records, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)


def build_report(records):
    totals = {}
    for r in records:
        totals[r["currency"]] = round(totals.get(r["currency"], 0) + r["total"], 2)
    missing = [r["file"] for r in records if not r["invoice_number"] or not r["date"] or not r["total"]]
    counts = Counter(r["invoice_number"] for r in records if r["invoice_number"])
    duplicates = sorted(n for n, c in counts.items() if c > 1)
    return {"count": len(records), "totals": totals, "missing": missing, "duplicates": duplicates}


def format_report(report):
    lines = [f"Invoices processed: {report['count']}", "", "Totals by currency:"]
    for currency, amount in report["totals"].items():
        lines.append(f"  {currency}{amount:,.2f}")
    lines.append("")
    lines.append("Missing fields: " + (", ".join(report["missing"]) if report["missing"] else "none"))
    lines.append("Duplicate invoice numbers: " + (", ".join(report["duplicates"]) if report["duplicates"] else "none"))
    return "\n".join(lines)


def write_report(report, path):
    Path(path).write_text(format_report(report) + "\n", encoding="utf-8")