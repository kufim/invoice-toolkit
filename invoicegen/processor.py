import csv
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