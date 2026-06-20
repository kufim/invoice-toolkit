# invoice-toolkit

A small Python toolkit for invoices. Two sides to it: create clean PDF invoices, and process incoming ones into data you can actually use.

## Backstory

I applied for a "Python Development for Invoice Process Automation" internship and got turned down. So I built both ends of it myself in Python, the part that makes invoices and the part that processes them.

## What's in it

**Generate invoices**

- a desktop panel: fill in a form, pick a color theme, hit generate, get a PDF
- or a command line version that turns a JSON file into the same PDF
- logo, sender and recipient, line items, automatic totals (tax, discount, shipping, amount paid, balance due), notes and terms

**Process incoming invoices**

- point it at a folder of invoice PDFs
- it reads each one and pulls out the invoice number, vendor, date, currency and total
- writes one CSV with every invoice as a row
- writes a short report: how many it processed, totals per currency, anything missing a field, and duplicate invoice numbers

## Install

```bash
pip install -r requirements.txt
```

## Generating invoices

Desktop panel:

```bash
python run.py
```

Command line, from a JSON file:

```bash
python -m invoicegen examples/sample_invoice.json -o invoice.pdf
```

## Processing invoices

Point it at a folder of invoice PDFs:

```bash
python -m invoicegen.process_cli path/to/folder -o invoices.csv -r report.txt
```

You get `invoices.csv` (one row per invoice) and `report.txt` (totals per currency, missing fields, duplicate invoice numbers).

## Project layout

```
invoicegen/
  models.py        the invoice data model
  calculations.py  totals and balance
  renderer.py      pdf output
  themes.py        color themes
  gui.py           desktop panel
  cli.py           generate from a json file
  extraction.py    read the fields out of a pdf
  processor.py     process a folder and build the report
  process_cli.py   the processing command
examples/
  sample_invoice.json
```

## License

MIT