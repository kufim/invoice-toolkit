import re
from pathlib import Path

import pdfplumber

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
AMOUNT = r"([\d][\d,]*\.\d{2})"
TOTAL_LABELS = [r"Balance\s*Due", r"Amount\s*Due", r"Total\s*Due", r"Grand\s*Total", r"(?<!Sub)Total"]


def extract_text(path):
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def currency_of(text):
    for symbol in ("€", "£", "$"):
        if symbol in text:
            return symbol
    return "$"


def amount_for(text, labels):
    for label in labels:
        match = re.search(label + r"[^\n\d-]{0,12}?" + AMOUNT, text, re.I)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def invoice_number(text):
    for pattern in (r"#\s*([A-Za-z0-9][A-Za-z0-9\-/]*)", r"Invoice\s*(?:No\.?|Number)\s*[:#]\s*([A-Za-z0-9\-/]+)"):
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return ""


def find_date(text):
    labelled = re.search(r"(?:Invoice\s*)?Date\b[^\n\d]{0,10}(" + DATE_RE.pattern + ")", text, re.I)
    if labelled:
        return labelled.group(1)
    loose = DATE_RE.search(text)
    return loose.group(0) if loose else ""


def find_vendor(lines):
    for line in lines:
        if line.upper().startswith("INVOICE") or line.startswith("#"):
            continue
        return line
    return ""


def extract_invoice(path):
    text = extract_text(path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    total = amount_for(text, TOTAL_LABELS)
    return {
        "file": Path(path).name,
        "invoice_number": invoice_number(text),
        "vendor": find_vendor(lines),
        "date": find_date(text),
        "currency": currency_of(text),
        "total": total if total is not None else 0.0,
    }