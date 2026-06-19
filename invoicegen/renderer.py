from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from . import calculations as calc
from . import themes
from .models import Invoice

INK = (17, 18, 20)
MUTED = (113, 118, 125)
LIGHT = (190, 194, 200)
LINE = (228, 230, 233)

PAGE_W = 210.0
MARGIN = 16.0
CONTENT_W = PAGE_W - 2 * MARGIN
BAND_H = 46.0


def _money(currency: str, value: float) -> str:
    if value < 0:
        return f"-{currency}{abs(value):,.2f}"
    return f"{currency}{value:,.2f}"


class InvoicePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        pass


def render_pdf(invoice: Invoice, output: str | Path, theme: str = themes.DEFAULT) -> Path:
    output = Path(output)
    pal = themes.palette(theme)
    pdf = InvoicePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(MARGIN, MARGIN, MARGIN)

    fonts = Path(__file__).parent / "assets"
    pdf.add_font("DejaVu", "", str(fonts / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(fonts / "DejaVuSans-Bold.ttf"))

    pdf.add_page()

    _header_band(pdf, invoice, pal)
    pdf.set_y(BAND_H + 12)
    _meta_and_parties(pdf, invoice, pal)
    _items_table(pdf, invoice, pal)
    _totals_block(pdf, invoice, pal)
    _notes_block(pdf, invoice)

    pdf.output(str(output))
    return output


def _header_band(pdf, invoice, pal):
    pdf.set_fill_color(*pal["header"])
    pdf.rect(0, 0, PAGE_W, BAND_H, style="F")

    y = 14
    if invoice.logo and Path(invoice.logo).exists():
        pdf.image(invoice.logo, x=MARGIN, y=y, h=18)
    else:
        pdf.set_xy(MARGIN, y)
        pdf.set_font("DejaVu", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(CONTENT_W * 0.6, 8, invoice.sender.name or "")
        if invoice.sender.address:
            pdf.set_xy(MARGIN, y + 9)
            pdf.set_font("DejaVu", "", 8.5)
            pdf.set_text_color(*LIGHT)
            pdf.multi_cell(CONTENT_W * 0.55, 4.2, invoice.sender.address)

    pdf.set_xy(MARGIN, 12)
    pdf.set_font("DejaVu", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(CONTENT_W, 12, "INVOICE", align="R")
    pdf.set_xy(MARGIN, 27)
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(*LIGHT)
    pdf.cell(CONTENT_W, 6, f"# {invoice.number}", align="R")


def _meta_and_parties(pdf, invoice, pal):
    top = pdf.get_y()
    col = CONTENT_W / 2

    _party_column(pdf, MARGIN, top, col - 6, "Billed To", invoice.bill_to)
    if invoice.ship_to.name:
        _party_column(pdf, MARGIN + col * 0.62, top, col - 6, "Shipped To", invoice.ship_to)

    meta = [
        ("Date", invoice.date),
        ("Payment Terms", invoice.payment_terms),
        ("Due Date", invoice.due_date),
        ("PO Number", invoice.po_number),
    ]
    meta = [(k, v) for k, v in meta if v]
    if meta:
        bx = PAGE_W - MARGIN - 64
        pdf.set_fill_color(*pal["soft"])
        pdf.rect(bx, top - 2, 64, 6.5 * len(meta) + 4, style="F")
        my = top + 1
        for label, value in meta:
            pdf.set_xy(bx + 4, my)
            pdf.set_font("DejaVu", "", 8.5)
            pdf.set_text_color(*MUTED)
            pdf.cell(30, 5, label)
            pdf.set_font("DejaVu", "B", 8.5)
            pdf.set_text_color(*INK)
            pdf.cell(26, 5, value, align="R")
            my += 6.5

    pdf.set_y(max(top + 26, pdf.get_y()))


def _party_column(pdf, x, y, w, label, party):
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(w, 4.5, label.upper())
    pdf.set_xy(x, y + 5.5)
    pdf.set_font("DejaVu", "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.cell(w, 5, party.name)
    if party.address:
        pdf.set_xy(x, y + 10.5)
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(w, 4.2, party.address)


def _items_table(pdf, invoice, pal):
    widths = [CONTENT_W * 0.52, CONTENT_W * 0.14, CONTENT_W * 0.17, CONTENT_W * 0.17]
    pdf.set_fill_color(*pal["accent"])
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 8.5)
    pdf.set_x(MARGIN)
    pdf.cell(widths[0], 9, "  ITEM", fill=True)
    pdf.cell(widths[1], 9, "QTY", align="C", fill=True)
    pdf.cell(widths[2], 9, "RATE", align="C", fill=True)
    pdf.cell(widths[3], 9, "AMOUNT  ", align="R", fill=True)
    pdf.ln(9)

    pdf.set_font("DejaVu", "", 9.5)
    pdf.set_draw_color(*LINE)
    for item in invoice.items:
        pdf.set_x(MARGIN)
        pdf.set_text_color(*INK)
        pdf.cell(widths[0], 8.5, "  " + item.description)
        pdf.set_text_color(*MUTED)
        pdf.cell(widths[1], 8.5, _fmt_qty(item.quantity), align="C")
        pdf.cell(widths[2], 8.5, _money(invoice.currency, item.rate), align="C")
        pdf.set_text_color(*INK)
        pdf.cell(widths[3], 8.5, _money(invoice.currency, item.amount) + "  ", align="R")
        pdf.ln(8.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
    pdf.ln(6)


def _totals_block(pdf, invoice, pal):
    s = calc.summary(invoice)
    label_w = CONTENT_W * 0.28
    value_w = CONTENT_W * 0.22
    x = PAGE_W - MARGIN - label_w - value_w

    rows = [("Subtotal", s["subtotal"]), ("Tax", s["tax"])]
    if invoice.discount:
        rows.append(("Discount", -s["discount"]))
    if invoice.shipping:
        rows.append(("Shipping", s["shipping"]))
    rows.append(("Total", s["total"]))
    if invoice.amount_paid:
        rows.append(("Amount Paid", s["amount_paid"]))

    for label, value in rows:
        bold = label == "Total"
        pdf.set_x(x)
        pdf.set_font("DejaVu", "B" if bold else "", 10 if bold else 9.5)
        pdf.set_text_color(*(INK if bold else MUTED))
        pdf.cell(label_w, 7, label)
        pdf.set_font("DejaVu", "B" if bold else "", 10 if bold else 9.5)
        pdf.set_text_color(*INK)
        pdf.cell(value_w, 7, _money(invoice.currency, value), align="R")
        pdf.ln(7)

    pdf.ln(2)
    by = pdf.get_y()
    pdf.set_fill_color(*pal["accent"])
    pdf.rect(x, by, label_w + value_w, 13, style="F")
    pdf.set_xy(x + 4, by)
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(label_w, 13, "Balance Due")
    pdf.set_xy(x, by)
    pdf.cell(label_w + value_w - 4, 13, _money(invoice.currency, s["balance_due"]), align="R")
    pdf.ln(20)


def _notes_block(pdf, invoice):
    for label, text in (("Notes", invoice.notes), ("Terms", invoice.terms)):
        if not text:
            continue
        pdf.set_x(MARGIN)
        pdf.set_font("DejaVu", "B", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(CONTENT_W, 5.5, label.upper())
        pdf.ln(5.5)
        pdf.set_x(MARGIN)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(CONTENT_W, 4.8, text)
        pdf.ln(3)


def _fmt_qty(value):
    return str(int(value)) if float(value).is_integer() else f"{value:g}"