from __future__ import annotations

import sys
from pathlib import Path
from tkinter import (
    BOTH, END, LEFT, RIGHT, TOP, X, Y, Canvas, StringVar, Tk, filedialog, messagebox, ttk,
)
import tkinter as tk

from .models import Invoice
from .renderer import render_pdf


PAD = 8
ENTRY_W = 38


class ItemRow:
    def __init__(self, parent, on_remove):
        self.frame = ttk.Frame(parent)
        self.description = ttk.Entry(self.frame, width=44)
        self.quantity = ttk.Entry(self.frame, width=8)
        self.rate = ttk.Entry(self.frame, width=12)
        self.quantity.insert(0, "1")
        self.rate.insert(0, "0")
        self.description.pack(side=LEFT, padx=(0, 6))
        self.quantity.pack(side=LEFT, padx=(0, 6))
        self.rate.pack(side=LEFT, padx=(0, 6))
        ttk.Button(self.frame, text="✕", width=3, command=lambda: on_remove(self)).pack(side=LEFT)
        self.frame.pack(fill=X, pady=3)

    def value(self):
        desc = self.description.get().strip()
        if not desc:
            return None
        return {
            "description": desc,
            "quantity": _to_float(self.quantity.get(), 1),
            "rate": _to_float(self.rate.get(), 0),
        }

    def destroy(self):
        self.frame.destroy()


class InvoiceApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Invoice Generator")
        self.geometry("760x820")
        self.minsize(680, 600)
        self.rows: list[ItemRow] = []
        self.fields: dict[str, ttk.Entry] = {}
        self._build()

    def _build(self):
        outer = ttk.Frame(self)
        outer.pack(fill=BOTH, expand=True)
        canvas = Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas, padding=18)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        self._heading(body, "Invoice Generator", 16)

        logo = self._section(body, "Logo")
        self.logo_var = StringVar()
        lrow = ttk.Frame(logo); lrow.pack(fill=X)
        ttk.Entry(lrow, textvariable=self.logo_var, width=ENTRY_W).pack(side=LEFT, padx=(0, 6))
        ttk.Button(lrow, text="Browse", command=self._pick_logo).pack(side=LEFT)

        frm = self._section(body, "From")
        self._entry(frm, "from_name", "Name")
        self._entry(frm, "from_address", "Address")

        cols = ttk.Frame(body); cols.pack(fill=X, pady=(6, 0))
        bill = self._section(cols, "Bill To", side=LEFT)
        self._entry(bill, "bill_name", "Name")
        self._entry(bill, "bill_address", "Address")
        ship = self._section(cols, "Ship To", side=LEFT)
        self._entry(ship, "ship_name", "Name")
        self._entry(ship, "ship_address", "Address")

        det = self._section(body, "Invoice Details")
        self._entry(det, "number", "Invoice #", default="1")
        self._entry(det, "date", "Date (YYYY-MM-DD)")
        self._entry(det, "payment_terms", "Payment Terms")
        self._entry(det, "due_date", "Due Date")
        self._entry(det, "po_number", "PO Number")
        self._entry(det, "currency", "Currency", default="$")

        items = self._section(body, "Line Items")
        head = ttk.Frame(items); head.pack(fill=X, pady=(0, 2))
        ttk.Label(head, text="Description", width=44).pack(side=LEFT, padx=(0, 6))
        ttk.Label(head, text="Qty", width=8).pack(side=LEFT, padx=(0, 6))
        ttk.Label(head, text="Rate", width=12).pack(side=LEFT)
        self.items_frame = ttk.Frame(items); self.items_frame.pack(fill=X)
        ttk.Button(items, text="+ Add line item", command=self._add_row).pack(anchor="w", pady=(6, 0))
        self._add_row()

        adj = self._section(body, "Totals")
        self._entry(adj, "tax_rate", "Tax %", default="0")
        self._entry(adj, "discount", "Discount", default="0")
        self._entry(adj, "shipping", "Shipping", default="0")
        self._entry(adj, "amount_paid", "Amount Paid", default="0")

        self.notes_text = self._textbox(body, "Notes")
        self.terms_text = self._textbox(body, "Terms")

        actions = ttk.Frame(body); actions.pack(fill=X, pady=(16, 4))
        ttk.Button(actions, text="Generate PDF", command=self._generate).pack(side=LEFT)
        self.status = ttk.Label(actions, text="", foreground="#15803d")
        self.status.pack(side=LEFT, padx=12)

    def _heading(self, parent, text, size):
        ttk.Label(parent, text=text, font=("Helvetica", size, "bold")).pack(anchor="w", pady=(0, 10))

    def _section(self, parent, title, side=TOP):
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.pack(side=side, fill=BOTH, expand=True, padx=(0, 10) if side == LEFT else 0, pady=6)
        return box

    def _entry(self, parent, key, label, default=""):
        row = ttk.Frame(parent); row.pack(fill=X, pady=2)
        ttk.Label(row, text=label, width=18).pack(side=LEFT)
        e = ttk.Entry(row, width=ENTRY_W)
        if default:
            e.insert(0, default)
        e.pack(side=LEFT, fill=X, expand=True)
        self.fields[key] = e

    def _textbox(self, parent, title):
        box = self._section(parent, title)
        t = tk.Text(box, height=3, width=ENTRY_W, wrap="word")
        t.pack(fill=X)
        return t

    def _add_row(self):
        self.rows.append(ItemRow(self.items_frame, self._remove_row))

    def _remove_row(self, row):
        if len(self.rows) <= 1:
            return
        self.rows.remove(row)
        row.destroy()

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Choose a logo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")],
        )
        if path:
            self.logo_var.set(path)

    def _collect(self) -> dict:
        f = self.fields
        items = [r.value() for r in self.rows]
        return {
            "number": f["number"].get().strip() or "1",
            "from": {"name": f["from_name"].get().strip(), "address": f["from_address"].get().strip()},
            "bill_to": {"name": f["bill_name"].get().strip(), "address": f["bill_address"].get().strip()},
            "ship_to": {"name": f["ship_name"].get().strip(), "address": f["ship_address"].get().strip()},
            "date": f["date"].get().strip(),
            "payment_terms": f["payment_terms"].get().strip(),
            "due_date": f["due_date"].get().strip(),
            "po_number": f["po_number"].get().strip(),
            "currency": f["currency"].get().strip() or "$",
            "items": [i for i in items if i],
            "tax_rate": _to_float(f["tax_rate"].get(), 0),
            "discount": _to_float(f["discount"].get(), 0),
            "shipping": _to_float(f["shipping"].get(), 0),
            "amount_paid": _to_float(f["amount_paid"].get(), 0),
            "notes": self.notes_text.get("1.0", END).strip(),
            "terms": self.terms_text.get("1.0", END).strip(),
            "logo": self.logo_var.get().strip() or None,
        }

    def _generate(self):
        data = self._collect()
        if not data["items"]:
            messagebox.showwarning("Nothing to invoice", "Add at least one line item.")
            return
        path = filedialog.asksaveasfilename(
            title="Save invoice",
            defaultextension=".pdf",
            initialfile=f"invoice_{data['number']}.pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not path:
            return
        try:
            render_pdf(Invoice.parse(data), path)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.status.config(text=f"Saved {Path(path).name}")
        _open_file(path)


def _to_float(value, default):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return float(default)


def _open_file(path):
    try:
        if sys.platform.startswith("win"):
            import os
            os.startfile(path)  # noqa: type-ignore
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", path], check=False)
        else:
            import subprocess
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def main():
    InvoiceApp().mainloop()


if __name__ == "__main__":
    main()