from __future__ import annotations

import sys
from pathlib import Path
from tkinter import (
    BOTH, END, LEFT, RIGHT, TOP, X, Y, Canvas, StringVar, Tk, filedialog, messagebox, ttk,
)
import tkinter as tk

from .models import Invoice
from .renderer import render_pdf


ENTRY_W = 38
MAX_MONEY = 99_999_999.99
MAX_QTY = 1_000_000.0
CURRENCIES = [("USD", "$"), ("EUR", "€"), ("GBP", "£"), ("JPY", "¥"),
              ("CHF", "CHF"), ("CAD", "C$"), ("AUD", "A$")]


def mk_num(max_value, decimals=2):
    def validate(proposed: str) -> bool:
        p = proposed.strip()
        if p in ("", "."):
            return True
        clean = p.replace(",", "")
        try:
            value = float(clean)
        except ValueError:
            return False
        if value < 0 or value > max_value:
            return False
        if "." in clean and len(clean.split(".")[1]) > decimals:
            return False
        return True
    return validate


def mk_len(max_len):
    def validate(proposed: str) -> bool:
        return len(proposed) <= max_len
    return validate


def _to_float(value, default):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return float(default)


class ItemRow:
    def __init__(self, parent, on_remove, v_qty, v_rate, v_desc, money_fmt):
        self.frame = ttk.Frame(parent)
        self.description = ttk.Entry(self.frame, width=44, validate="key", validatecommand=v_desc)
        self.quantity = ttk.Entry(self.frame, width=8, validate="key", validatecommand=v_qty)
        self.rate = ttk.Entry(self.frame, width=12, validate="key", validatecommand=v_rate)
        self.quantity.insert(0, "1")
        self.rate.insert(0, "0.00")
        self.rate.bind("<FocusOut>", lambda e: money_fmt(self.rate))
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
        self.geometry("840x960")
        self.minsize(800, 640)
        self.rows: list[ItemRow] = []
        self.fields: dict[str, ttk.Entry] = {}

        self.v_money = (self.register(mk_num(MAX_MONEY)), "%P")
        self.v_pct = (self.register(mk_num(100.0)), "%P")
        self.v_qty = (self.register(mk_num(MAX_QTY, decimals=3)), "%P")
        self.v_cur = (self.register(mk_len(3)), "%P")
        self.v_num = (self.register(mk_len(20)), "%P")
        self.v_name = (self.register(mk_len(60)), "%P")
        self.v_addr = (self.register(mk_len(120)), "%P")
        self.v_short = (self.register(mk_len(40)), "%P")
        self.v_desc = (self.register(mk_len(70)), "%P")

        self._build()

    def _build(self):
        outer = ttk.Frame(self)
        outer.pack(fill=BOTH, expand=True)
        canvas = Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas, padding=18)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        ttk.Label(body, text="Invoice Generator", font=("Helvetica", 16, "bold")).pack(anchor="w", pady=(0, 10))

        logo = self._section(body, "Logo")
        self.logo_var = StringVar()
        lrow = ttk.Frame(logo); lrow.pack(fill=X)
        ttk.Entry(lrow, textvariable=self.logo_var, width=ENTRY_W).pack(side=LEFT, padx=(0, 6))
        ttk.Button(lrow, text="Browse", command=self._pick_logo).pack(side=LEFT)

        frm = self._section(body, "From")
        self._entry(frm, "from_name", "Name", vcmd=self.v_name)
        self._entry(frm, "from_address", "Address", vcmd=self.v_addr)

        cols = ttk.Frame(body); cols.pack(fill=X, pady=(6, 0))
        bill = self._section(cols, "Bill To", side=LEFT)
        self._entry(bill, "bill_name", "Name", vcmd=self.v_name)
        self._entry(bill, "bill_address", "Address", vcmd=self.v_addr)
        ship = self._section(cols, "Ship To", side=LEFT)
        self._entry(ship, "ship_name", "Name", vcmd=self.v_name)
        self._entry(ship, "ship_address", "Address", vcmd=self.v_addr)

        det = self._section(body, "Invoice Details")
        self._entry(det, "number", "Invoice #", default="1", vcmd=self.v_num)
        self._entry(det, "date", "Date (YYYY-MM-DD)", date=True)
        self._entry(det, "payment_terms", "Payment Terms", vcmd=self.v_short)
        self._entry(det, "due_date", "Due Date", date=True)
        self._entry(det, "po_number", "PO Number", vcmd=self.v_short)
        crow = ttk.Frame(det); crow.pack(fill=X, pady=2)
        ttk.Label(crow, text="Currency", width=18).pack(side=LEFT)
        self.currency_map = {f"{code}   {sym}": sym for code, sym in CURRENCIES}
        self.currency_var = StringVar(value="USD   $")
        ttk.Combobox(crow, textvariable=self.currency_var, values=list(self.currency_map),
                     state="readonly", width=ENTRY_W - 2).pack(side=LEFT, fill=X, expand=True)

        items = self._section(body, "Line Items")
        head = ttk.Frame(items); head.pack(fill=X, pady=(0, 2))
        ttk.Label(head, text="Description", width=44).pack(side=LEFT, padx=(0, 6))
        ttk.Label(head, text="Qty", width=8).pack(side=LEFT, padx=(0, 6))
        ttk.Label(head, text="Rate", width=12).pack(side=LEFT)
        self.items_frame = ttk.Frame(items); self.items_frame.pack(fill=X)
        ttk.Button(items, text="+ Add line item", command=self._add_row).pack(anchor="w", pady=(6, 0))
        self._add_row()

        adj = self._section(body, "Totals")
        self._entry(adj, "tax_rate", "Tax % (0-100)", default="0", vcmd=self.v_pct)
        self._entry(adj, "discount", "Discount", default="0.00", vcmd=self.v_money, money=True)
        self._entry(adj, "shipping", "Shipping", default="0.00", vcmd=self.v_money, money=True)
        self._entry(adj, "amount_paid", "Amount Paid", default="0.00", vcmd=self.v_money, money=True)

        self.notes_text = self._textbox(body, "Notes")
        self.terms_text = self._textbox(body, "Terms")

        actions = ttk.Frame(body); actions.pack(fill=X, pady=(16, 4))
        ttk.Button(actions, text="Generate PDF", command=self._generate).pack(side=LEFT)
        self.status = ttk.Label(actions, text="", foreground="#15803d")
        self.status.pack(side=LEFT, padx=12)

    def _section(self, parent, title, side=TOP):
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.pack(side=side, fill=BOTH, expand=True, padx=(0, 10) if side == LEFT else 0, pady=6)
        return box

    def _entry(self, parent, key, label, default="", vcmd=None, money=False, date=False):
        row = ttk.Frame(parent); row.pack(fill=X, pady=2)
        ttk.Label(row, text=label, width=18).pack(side=LEFT)
        e = ttk.Entry(row, width=ENTRY_W)
        if vcmd is not None:
            e.config(validate="key", validatecommand=vcmd)
        if money:
            e.bind("<FocusOut>", lambda ev: self._format_money(e, vcmd))
        if date:
            e.bind("<KeyRelease>", lambda ev: self._format_date(e))
        if default:
            e.insert(0, default)
        e.pack(side=LEFT, fill=X, expand=True)
        self.fields[key] = e

    def _textbox(self, parent, title):
        box = self._section(parent, title)
        t = tk.Text(box, height=3, width=ENTRY_W, wrap="word")
        t.pack(fill=X)
        return t

    def _format_money(self, entry, vcmd):
        raw = entry.get().replace(",", "").strip()
        if raw in ("", "-", "."):
            return
        try:
            value = float(raw)
        except ValueError:
            return
        entry.config(validate="none")
        entry.delete(0, END)
        entry.insert(0, f"{value:,.2f}")
        if vcmd is not None:
            entry.config(validate="key", validatecommand=vcmd)

    def _format_date(self, entry):
        digits = "".join(c for c in entry.get() if c.isdigit())[:8]
        year, month, day = digits[:4], digits[4:6], digits[6:8]
        if len(month) == 2:
            month = "12" if int(month) > 12 else ("01" if int(month) == 0 else month)
        if len(day) == 2:
            day = "31" if int(day) > 31 else ("01" if int(day) == 0 else day)
        formatted = "-".join(c for c in (year, month, day) if c)
        if formatted != entry.get():
            entry.delete(0, END)
            entry.insert(0, formatted)
            entry.icursor(END)

    def _add_row(self):
        self.rows.append(ItemRow(self.items_frame, self._remove_row, self.v_qty, self.v_money, self.v_desc, lambda e: self._format_money(e, self.v_money)))

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
            "currency": self.currency_map.get(self.currency_var.get(), "$"),
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
        for label, key in (("Date", "date"), ("Due Date", "due_date")):
            value = data[key]
            if value and not _valid_date(value):
                messagebox.showwarning("Check the date", f"{label} should be a full YYYY-MM-DD date.")
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


def _valid_date(value: str) -> bool:
    import datetime
    try:
        datetime.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _open_file(path):
    try:
        if sys.platform.startswith("win"):
            import os
            os.startfile(path)
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