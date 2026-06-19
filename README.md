# invoice-generator

A small command-line tool that turns a JSON file into a clean, professional PDF invoice. Logo, sender and recipient details, line items, automatic totals (tax, discount, shipping, amount paid, balance due), notes and terms.

## Backstory

I applied for a "Python Development for Invoice Process Automation" internship and got turned down. So I built the invoice side of it myself, end to end, in Python.

## Features

- Single JSON file in, polished PDF out
- Optional logo
- Bill-to and ship-to parties
- Unlimited line items, `quantity x rate` totalled automatically
- Subtotal, percentage tax, flat discount, shipping, amount paid and balance due
- Any currency symbol
- Notes and terms sections
- No web service or account, everything runs locally

## Install

```bash
pip install -r requirements.txt
```

Or install it as a command:

```bash
pip install .
```

## Input panel

Prefer filling in a form over editing JSON? Launch the desktop panel:

```bash
python run.py
```

(or `python -m invoicegen.gui`, or `invoicegen-gui` once installed). Fill in the fields, add line items, pick a logo, and click **Generate PDF**.

## Command line

```bash
python -m invoicegen examples/sample_invoice.json
```

Choose the output path:

```bash
python -m invoicegen examples/sample_invoice.json -o acme.pdf
```

If installed as a package, the `invoicegen` command works the same way:

```bash
invoicegen examples/sample_invoice.json -o acme.pdf
```

## Invoice file

```json
{
  "number": "1024",
  "from": { "name": "Northwind Studio", "address": "12 Keizersgracht\n1015 Amsterdam" },
  "bill_to": { "name": "Acme Corp", "address": "440 Market Street\nSan Francisco, CA" },
  "ship_to": { "name": "Acme Warehouse", "address": "8 Dockside Road\nOakland, CA" },
  "date": "2026-06-20",
  "payment_terms": "Net 14",
  "due_date": "2026-07-04",
  "po_number": "PO-5567",
  "currency": "$",
  "items": [
    { "description": "Brand identity design", "quantity": 1, "rate": 2400 },
    { "description": "Copywriting (per page)", "quantity": 6, "rate": 120 }
  ],
  "tax_rate": 9,
  "discount": 250,
  "shipping": 0,
  "amount_paid": 1000,
  "notes": "Thanks for your business.",
  "terms": "Payment due within 14 days."
}
```

Every field is optional except the line items. `logo` takes a path to an image file.

## Project layout

```
invoicegen/
  models.py        data model (Invoice, LineItem, Party)
  calculations.py  totals and balance
  renderer.py      PDF rendering
  cli.py           command-line entry point
examples/
  sample_invoice.json
```

## License

MIT