#!/usr/bin/env python3
"""PDF report generator — ReportLab Platypus engine (pharmaceutical-grade design)."""

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER, landscape as landscape_ps
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ---------------------------------------------------------------------------
# Pharma color palette
# ---------------------------------------------------------------------------

THEMES = {
    "pharma":   {"primary": (12, 35, 64),    "accent": (0, 83, 160),   "highlight": (235, 243, 250)},
    "default":  {"primary": (26, 54, 93),    "accent": (201, 160, 48), "highlight": (235, 243, 252)},
    "navy":     {"primary": (10, 36, 99),    "accent": (255, 195, 0),  "highlight": (230, 240, 255)},
    "charcoal": {"primary": (45, 45, 45),    "accent": (220, 80, 40),  "highlight": (245, 245, 245)},
    "forest":   {"primary": (20, 83, 45),    "accent": (180, 140, 20), "highlight": (230, 247, 236)},
    "burgundy": {"primary": (100, 0, 30),    "accent": (200, 160, 80), "highlight": (250, 235, 240)},
}

RISK_COLORS = {
    "LOW":      ("#1B7A3E", "#FFFFFF"),
    "MEDIUM":   ("#D4870A", "#FFFFFF"),
    "HIGH":     ("#C85200", "#FFFFFF"),
    "CRITICAL": ("#B50000", "#FFFFFF"),
}

PHARMA_BAR_PALETTE = ["#0053A0", "#63B1E5", "#1B7A3E", "#D4870A", "#C85200", "#B50000"]

# Layout constants
_HEADER_H = 32      # header band height (pt)
_FOOTER_H = 28      # footer band height (pt)
_PORT_MARGIN = 0.75 * inch   # portrait left/right margin
_LAND_MARGIN = 0.65 * inch   # landscape left/right margin


def rgb(t):
    return colors.Color(t[0] / 255, t[1] / 255, t[2] / 255)


def hx(h: str):
    return colors.HexColor(h)


# ---------------------------------------------------------------------------
# Page callbacks
# ---------------------------------------------------------------------------

def _draw_header_footer(canvas, pw, ph, meta, fonts, classification_color="#B50000"):
    """Draw solid navy header band + footer band. Used on body and landscape pages."""
    primary_navy = hx("#0C2340")
    light_text = hx("#C3D0DE")
    white = colors.white

    canvas.saveState()

    # Header band
    canvas.setFillColor(primary_navy)
    canvas.rect(0, ph - _HEADER_H, pw, _HEADER_H, fill=1, stroke=0)

    # Company name (left)
    canvas.setFillColor(white)
    canvas.setFont(fonts.get("bold", "Helvetica-Bold"), 8)
    canvas.drawString(0.6 * inch, ph - _HEADER_H + 10, meta.get("company", "AVANON").upper())

    # Classification badge (centre-right)
    classification = meta.get("classification", "")
    if classification:
        bdg_w, bdg_h = 1.3 * inch, 15
        bdg_x = pw - 0.6 * inch - bdg_w - 1.1 * inch
        bdg_y = ph - _HEADER_H + 8
        canvas.setFillColor(hx(classification_color))
        canvas.roundRect(bdg_x, bdg_y, bdg_w, bdg_h, 3, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont(fonts.get("bold", "Helvetica-Bold"), 6.5)
        canvas.drawCentredString(bdg_x + bdg_w / 2, bdg_y + 4, classification.upper())

    # Page number (right)
    canvas.setFillColor(white)
    canvas.setFont(fonts.get("regular", "Helvetica"), 8)
    canvas.drawRightString(pw - 0.6 * inch, ph - _HEADER_H + 10, f"Page {canvas.getPageNumber()}")

    # Footer band
    canvas.setFillColor(primary_navy)
    canvas.rect(0, 0, pw, _FOOTER_H, fill=1, stroke=0)

    canvas.setFillColor(light_text)
    canvas.setFont(fonts.get("regular", "Helvetica"), 7)
    doc_id = meta.get("document_id", "")
    doc_date = meta.get("date", str(date.today()))
    left_foot = f"{doc_id}  |  {doc_date}" if doc_id else doc_date
    canvas.drawString(0.6 * inch, 9, left_foot)

    title = meta.get("title", "")
    canvas.drawCentredString(pw / 2, 9, title[:55])

    canvas.drawRightString(pw - 0.6 * inch, 9, "Avanon PBM Intelligence")

    canvas.restoreState()


def make_body_page(canvas, doc):
    meta  = doc.report_meta
    fonts = getattr(doc, "report_fonts", {"regular": "Helvetica", "bold": "Helvetica-Bold"})
    pw, ph = doc.pagesize
    _draw_header_footer(canvas, pw, ph, meta, fonts)


def make_table_landscape_page(canvas, doc):
    meta  = doc.report_meta
    fonts = getattr(doc, "report_fonts", {"regular": "Helvetica", "bold": "Helvetica-Bold"})
    # Landscape Letter: width=792, height=612
    pw, ph = landscape_ps(LETTER)
    _draw_header_footer(canvas, pw, ph, meta, fonts)


def make_cover_page(canvas, doc):
    meta  = doc.report_meta
    fonts = getattr(doc, "report_fonts", {"regular": "Helvetica", "bold": "Helvetica-Bold",
                                          "italic": "Helvetica-Oblique"})
    pw, ph = doc.pagesize  # portrait LETTER: 612 × 792

    navy      = hx("#0C2340")
    pfizer    = hx("#0053A0")
    sky       = hx("#63B1E5")
    light_txt = hx("#C3D0DE")
    white     = colors.white

    canvas.saveState()

    # ── Zone A: Navy header (top 47%) ────────────────────────────────────────
    header_h = ph * 0.47
    header_y = ph - header_h
    canvas.setFillColor(navy)
    canvas.rect(0, header_y, pw, header_h, fill=1, stroke=0)

    # Company / Logo area (top-left in header)
    logo_path = meta.get("logo_path", "")
    logo_drawn = False
    if logo_path and os.path.isfile(logo_path):
        try:
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            scale = min(1.6 * inch / iw, 0.45 * inch / ih)
            canvas.drawImage(logo_path, 0.65 * inch, ph - 0.55 * inch,
                             width=iw * scale, height=ih * scale, mask="auto")
            logo_drawn = True
        except Exception:
            pass
    if not logo_drawn:
        canvas.setFillColor(sky)
        canvas.setFont(fonts["bold"], 16)
        canvas.drawString(0.65 * inch, ph - 0.48 * inch, "AVANON")

    # Classification badge (top-right in header)
    classification = meta.get("classification", "CONFIDENTIAL")
    badge_bg = {"CONFIDENTIAL": "#B50000", "INTERNAL": "#D4870A", "PUBLIC": "#1B7A3E"}.get(
        classification.upper(), "#B50000"
    )
    bw, bh = 1.4 * inch, 20
    bx = pw - 0.65 * inch - bw
    by = ph - 0.48 * inch
    canvas.setFillColor(hx(badge_bg))
    canvas.roundRect(bx, by, bw, bh, 4, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont(fonts["bold"], 7.5)
    canvas.drawCentredString(bx + bw / 2, by + 6, classification.upper())

    # Report title (centred in upper part of header)
    title = meta.get("title", "Report")
    canvas.setFillColor(white)
    font_size = 22 if len(title) > 38 else 26
    canvas.setFont(fonts["bold"], font_size)
    canvas.drawCentredString(pw / 2, header_y + header_h * 0.58, title)

    # Subtitle
    subtitle = meta.get("subtitle", "")
    if subtitle:
        canvas.setFillColor(light_txt)
        canvas.setFont(fonts["regular"], 12)
        canvas.drawCentredString(pw / 2, header_y + header_h * 0.42, subtitle)

    # "PBM INTELLIGENCE ANALYSIS" pill badge (bottom of header zone)
    pill_label = "PBM INTELLIGENCE ANALYSIS"
    pill_w = 2.4 * inch
    pill_h = 18
    pill_x = (pw - pill_w) / 2
    pill_y = header_y + header_h * 0.18
    canvas.setStrokeColor(sky)
    canvas.setFillColor(hx("#0C2340"))
    canvas.roundRect(pill_x, pill_y, pill_w, pill_h, 9, fill=1, stroke=1)
    canvas.setFillColor(sky)
    canvas.setFont(fonts["bold"], 7)
    canvas.drawCentredString(pw / 2, pill_y + 5.5, pill_label)

    # ── Zone B: Pfizer-blue accent stripe ────────────────────────────────────
    stripe_y = header_y - 8
    canvas.setFillColor(pfizer)
    canvas.rect(0, stripe_y, pw, 8, fill=1, stroke=0)

    # ── Zone C: White metadata content ───────────────────────────────────────
    label_x  = 0.8 * inch
    value_x  = 2.5 * inch
    row_y    = stripe_y - 30
    row_gap  = 22

    fields = [
        ("Prepared By",  meta.get("author", "")),
        ("Organization", meta.get("company", "")),
        ("Department",   meta.get("department", "")),
        ("Date",         meta.get("date", str(date.today()))),
        ("Document ID",  meta.get("document_id", "")),
    ]
    for label, value in fields:
        if value:
            canvas.setFillColor(navy)
            canvas.setFont(fonts["bold"], 9)
            canvas.drawString(label_x, row_y, f"{label}:")
            canvas.setFillColor(hx("#1A1A2E"))
            canvas.setFont(fonts["regular"], 9)
            canvas.drawString(value_x, row_y, str(value)[:60])
            row_y -= row_gap

    # ── Zone D: Thin Pfizer-blue rule ────────────────────────────────────────
    canvas.setStrokeColor(pfizer)
    canvas.setLineWidth(1)
    canvas.line(0.65 * inch, 0.75 * inch, pw - 0.65 * inch, 0.75 * inch)

    # ── Zone E: Navy footer strip ─────────────────────────────────────────────
    canvas.setFillColor(navy)
    canvas.rect(0, 0, pw, 0.65 * inch, fill=1, stroke=0)
    canvas.setFillColor(light_txt)
    canvas.setFont(fonts["regular"], 7)
    canvas.drawCentredString(pw / 2, 0.22 * inch, "Generated by Avanon PBM Intelligence Platform")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def build_styles(theme, fonts: dict) -> dict:
    primary   = rgb(theme["primary"])
    navy      = hx("#0C2340")
    pfizer    = hx("#0053A0")
    body_dark = hx("#1A1A2E")
    caption_c = hx("#666666")
    kpi_bg    = hx("#F5F9FE")

    fr = fonts.get("regular", "Helvetica")
    fb = fonts.get("bold",    "Helvetica-Bold")
    fi = fonts.get("italic",  "Helvetica-Oblique")

    s = {}
    s["ReportBody"] = ParagraphStyle(
        "ReportBody", fontName=fr, fontSize=10,
        leading=15, textColor=body_dark,
        spaceAfter=6, spaceBefore=0,
    )
    s["SectionHeading"] = ParagraphStyle(
        "SectionHeading", fontName=fb, fontSize=13,
        leading=17, textColor=navy,
        spaceBefore=20, spaceAfter=4,
    )
    s["SubsectionHeading"] = ParagraphStyle(
        "SubsectionHeading", fontName=fb, fontSize=10.5,
        leading=14, textColor=navy,
        spaceBefore=12, spaceAfter=4,
    )
    s["TableTitle"] = ParagraphStyle(
        "TableTitle", fontName=fb, fontSize=10,
        leading=14, textColor=navy,
        spaceBefore=14, spaceAfter=4,
    )
    s["ExecSummary"] = ParagraphStyle(
        "ExecSummary", fontName=fr, fontSize=10,
        leading=15, textColor=body_dark,
        leftIndent=12, rightIndent=12,
        spaceBefore=4, spaceAfter=4,
    )
    s["ExecSummaryTitle"] = ParagraphStyle(
        "ExecSummaryTitle", fontName=fb, fontSize=11,
        leading=15, textColor=pfizer,
        spaceBefore=0, spaceAfter=6,
    )
    s["Caption"] = ParagraphStyle(
        "Caption", fontName=fi, fontSize=8,
        leading=11, textColor=caption_c,
        alignment=TA_LEFT, spaceAfter=4,
    )
    s["SourceNote"] = ParagraphStyle(
        "SourceNote", fontName=fi, fontSize=7.5,
        leading=11, textColor=caption_c,
        spaceAfter=10, spaceBefore=2,
    )
    s["FigureCaption"] = ParagraphStyle(
        "FigureCaption", fontName=fr, fontSize=8,
        leading=11, textColor=caption_c,
        spaceAfter=10, spaceBefore=4,
    )
    s["TableHeader"] = ParagraphStyle(
        "TableHeader", fontName=fb, fontSize=8,
        textColor=colors.white, leading=10,
        alignment=TA_LEFT,
    )
    s["TableHeaderRight"] = ParagraphStyle(
        "TableHeaderRight", fontName=fb, fontSize=8,
        textColor=colors.white, leading=10,
        alignment=TA_RIGHT,
    )
    s["TableCell"] = ParagraphStyle(
        "TableCell", fontName=fr, fontSize=8.5,
        textColor=body_dark, leading=11,
        alignment=TA_LEFT,
    )
    s["TableCellRight"] = ParagraphStyle(
        "TableCellRight", fontName=fr, fontSize=8.5,
        textColor=body_dark, leading=11,
        alignment=TA_RIGHT,
    )
    s["TableCellCenter"] = ParagraphStyle(
        "TableCellCenter", fontName=fr, fontSize=8.5,
        textColor=body_dark, leading=11,
        alignment=TA_CENTER,
    )
    s["KPINumber"] = ParagraphStyle(
        "KPINumber", fontName=fb, fontSize=26,
        leading=30, textColor=pfizer,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=2,
    )
    s["KPILabel"] = ParagraphStyle(
        "KPILabel", fontName=fr, fontSize=8.5,
        leading=12, textColor=navy,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=0,
    )
    s["CalloutLabel"] = ParagraphStyle(
        "CalloutLabel", fontName=fb, fontSize=7,
        leading=10, textColor=hx("#0053A0"),
        spaceBefore=0, spaceAfter=4,
    )
    s["CalloutBody"] = ParagraphStyle(
        "CalloutBody", fontName=fr, fontSize=9,
        leading=13, textColor=body_dark,
        spaceBefore=0, spaceAfter=0,
    )
    s["TOCEntry0"] = ParagraphStyle(
        "TOCEntry0", fontName=fb, fontSize=10,
        textColor=navy, leading=14,
        leftIndent=0, spaceAfter=2,
    )
    s["TOCEntry1"] = ParagraphStyle(
        "TOCEntry1", fontName=fr, fontSize=9,
        textColor=body_dark, leading=13,
        leftIndent=18, spaceAfter=1,
    )
    return s


# ---------------------------------------------------------------------------
# Chart rendering
# ---------------------------------------------------------------------------

def _apply_pharma_chart_style(fig, ax, chart_type: str, title: str):
    """Apply pharmaceutical-grade styling to a matplotlib figure."""
    navy  = "#0C2340"
    spine_c = "#E0E8EF"

    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(spine_c)
        ax.spines[spine].set_linewidth(0.8)

    grid_axis = "x" if chart_type == "horizontal_bar" else "y"
    ax.grid(axis=grid_axis, color="#E8F0F8", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    ax.tick_params(labelsize=8.5, colors=navy, length=3)
    ax.xaxis.label.set_color(navy)
    ax.yaxis.label.set_color(navy)

    ax.set_title(title, fontsize=10.5, fontweight="bold", color=navy, pad=10, loc="left")


def render_chart(chart_spec: dict, theme: dict, tmp_dir: str, fonts: dict) -> str | None:
    if not HAS_MATPLOTLIB:
        return None

    chart_type  = chart_spec.get("type", "bar")
    title       = chart_spec.get("title", "")
    labels      = chart_spec.get("labels", [])
    datasets    = chart_spec.get("datasets", [])
    fig_number  = chart_spec.get("figure_number", "")
    source_note = chart_spec.get("source_note", "")

    fig, ax = plt.subplots(figsize=(7.0, 3.8))

    if chart_type in ("bar", "horizontal_bar"):
        x = range(len(labels))
        bar_w = 0.75 / max(len(datasets), 1)

        for i, ds in enumerate(datasets):
            offset = (i - len(datasets) / 2 + 0.5) * bar_w
            vals   = ds.get("values", [])
            clr    = PHARMA_BAR_PALETTE[i % len(PHARMA_BAR_PALETTE)]

            if chart_type == "bar":
                bars = ax.bar(
                    [xi + offset for xi in x], vals,
                    width=bar_w * 0.88, color=clr,
                    label=ds.get("label", ""), zorder=3,
                )
                labels_str = [f"${v:,.0f}" if max(vals or [0]) > 100 else f"{v:.1f}%"
                              for v in vals]
                ax.bar_label(bars, labels=labels_str, padding=4,
                             fontsize=7.5, color="#0C2340", fontweight="bold")
                ax.set_xticks(list(x))
                ax.set_xticklabels(labels, fontsize=8)
            else:
                hbars = ax.barh(
                    [xi + offset for xi in x], vals,
                    height=bar_w * 0.88, color=clr,
                    label=ds.get("label", ""), zorder=3,
                )
                labels_str = [f"{v:.1f}%" for v in vals]
                ax.bar_label(hbars, labels=labels_str, padding=4,
                             fontsize=7.5, color="#0C2340", fontweight="bold")
                ax.set_yticks(list(x))
                ax.set_yticklabels(labels, fontsize=8)

    elif chart_type == "line":
        for i, ds in enumerate(datasets):
            clr = PHARMA_BAR_PALETTE[i % len(PHARMA_BAR_PALETTE)]
            ax.plot(labels, ds.get("values", []), marker="o", linewidth=2,
                    color=clr, label=ds.get("label", ""), zorder=3)

    elif chart_type == "pie":
        vals = datasets[0].get("values", []) if datasets else []
        clrs = PHARMA_BAR_PALETTE[:len(vals)]
        wedges, texts, autotexts = ax.pie(
            vals, labels=labels, colors=clrs,
            autopct="%1.1f%%", startangle=90,
            textprops={"fontsize": 8, "color": "#0C2340"},
        )
        ax.axis("equal")

    if chart_type != "pie":
        _apply_pharma_chart_style(fig, ax, chart_type, title="")  # title handled separately

        if any(ds.get("label") for ds in datasets):
            ax.legend(fontsize=8, framealpha=0.9, edgecolor="#E0E8EF")

    plt.tight_layout(pad=0.6)

    path = os.path.join(tmp_dir, f"chart_{abs(hash(title))}.png")
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Flowable builders
# ---------------------------------------------------------------------------

def build_table(tbl_spec: dict, styles: dict, theme: dict, fonts: dict, avail_w: float):
    """Returns a list of flowables: [table_title?, table, source_note?]."""
    primary   = rgb(theme["primary"])
    navy      = hx("#0C2340")
    alt_row   = hx("#EBF3FA")
    border_c  = hx("#C5D9EC")
    fb        = fonts.get("bold", "Helvetica-Bold")

    headers    = tbl_spec.get("headers", [])
    rows       = tbl_spec.get("rows", [])
    risk_flags = tbl_spec.get("risk_flags", [])
    risk_col   = tbl_spec.get("risk_col_index", -1)

    # Columns to right-align (numeric columns, 0-indexed)
    right_cols = set(tbl_spec.get("right_align_cols", list(range(2, len(headers)))))

    # Build header row
    header_row = []
    for i, h in enumerate(headers):
        style = styles["TableHeaderRight"] if i in right_cols else styles["TableHeader"]
        header_row.append(Paragraph(str(h), style))

    # Build data rows
    data = [header_row]
    for row in rows:
        cells = []
        for i, c in enumerate(row):
            if i in right_cols:
                cells.append(Paragraph(str(c), styles["TableCellRight"]))
            else:
                cells.append(Paragraph(str(c), styles["TableCell"]))
        data.append(cells)

    # Column widths
    spec_widths = tbl_spec.get("col_widths")
    col_count   = max(len(headers), 1)
    if spec_widths and len(spec_widths) == col_count:
        total_spec = sum(spec_widths) * inch
        scale      = avail_w / total_spec
        col_ws     = [w * inch * scale for w in spec_widths]
    else:
        col_ws = [avail_w / col_count] * col_count

    # Base table style
    ts = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  navy),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  fb),
        ("ROWBACKGROUND",(0, 0), (-1, 0),  navy),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",         (0, 0), (-1, -1), 0.4, border_c),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT",    (0, 0), (0, 0),   24),
    ])

    # Alternating row backgrounds
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.add("BACKGROUND", (0, i), (-1, i), alt_row)

    # Risk column color-coding
    if risk_col >= 0 and risk_flags:
        for row_i, flag in enumerate(risk_flags, start=1):
            if row_i < len(data):
                flag_key = str(flag).upper()
                if flag_key in RISK_COLORS:
                    bg_hex, fg_hex = RISK_COLORS[flag_key]
                    ts.add("BACKGROUND", (risk_col, row_i), (risk_col, row_i), hx(bg_hex))
                    ts.add("TEXTCOLOR",  (risk_col, row_i), (risk_col, row_i), hx(fg_hex))
                    ts.add("FONTNAME",   (risk_col, row_i), (risk_col, row_i), fb)
                    ts.add("ALIGN",      (risk_col, row_i), (risk_col, row_i), "CENTER")

    tbl = Table(data, colWidths=col_ws, style=ts, repeatRows=1, hAlign="LEFT")

    flowables = [tbl]

    source_note = tbl_spec.get("source_note", "")
    if source_note:
        flowables.append(Paragraph(source_note, styles["SourceNote"]))

    return flowables


def build_exec_summary(text: str, styles: dict, theme: dict, avail_w: float):
    pfizer    = hx("#0053A0")
    highlight = hx("#EBF3FA")
    border_c  = hx("#C5D9EC")

    title_cell = Paragraph("Executive Summary", styles["ExecSummaryTitle"])
    body_cell  = Paragraph(text.replace("\n", "<br/>"), styles["ExecSummary"])

    ts = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), highlight),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LINEBEFORE",   (0, 0), (0, -1),  3, pfizer),
        ("BOX",          (0, 0), (-1, -1), 0.5, border_c),
    ])
    inner = [[title_cell], [body_cell]]
    return Table(inner, colWidths=[avail_w], style=ts)


def build_kpi_banner(kpi_list: list, styles: dict, avail_w: float):
    """3-cell KPI banner with large metric values."""
    if not kpi_list:
        return None

    pfizer   = hx("#0053A0")
    navy     = hx("#0C2340")
    bg       = hx("#F5F9FE")
    divider  = hx("#C5D9EC")

    n = min(len(kpi_list), 4)
    cell_w = avail_w / n

    cells = []
    for kpi in kpi_list[:n]:
        val_p = Paragraph(kpi.get("value", ""), styles["KPINumber"])
        lbl_p = Paragraph(kpi.get("label", ""), styles["KPILabel"])
        inner = Table([[val_p], [lbl_p]],
                      colWidths=[cell_w - 12],
                      style=TableStyle([
                          ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                          ("TOPPADDING",   (0, 0), (-1, -1), 0),
                          ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
                          ("LEFTPADDING",  (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                      ]))
        cells.append(inner)

    banner_ts = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg),
        ("BOX",          (0, 0), (-1, -1), 1.5, pfizer),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ])
    for i in range(n - 1):
        banner_ts.add("LINEAFTER", (i, 0), (i, 0), 0.75, divider)

    return Table([cells], colWidths=[cell_w] * n, style=banner_ts)


def build_callout_box(text: str, label: str, styles: dict, avail_w: float):
    """Sky-blue left-border callout box for regulatory context."""
    sky_blue = hx("#63B1E5")
    bg       = hx("#EBF3FA")

    label_p = Paragraph(label.upper(), styles["CalloutLabel"])
    body_p  = Paragraph(text.replace("\n\n", "<br/><br/>"), styles["CalloutBody"])

    ts = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg),
        ("LINEBEFORE",   (0, 0), (0, -1),  4, sky_blue),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ])
    inner = [[label_p], [body_p]]
    return Table(inner, colWidths=[avail_w], style=ts)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_report(spec: dict, output_path: str):
    # Load fonts (download Noto Sans if needed, fallback to DejaVu/Helvetica)
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from lib.font_loader import load_report_fonts
        fonts = load_report_fonts()
    except Exception:
        fonts = {"regular": "Helvetica", "bold": "Helvetica-Bold",
                 "italic": "Helvetica-Oblique", "bolditalic": "Helvetica-BoldOblique"}

    meta = spec.get("metadata", {})

    # Resolve theme
    theme_spec = spec.get("theme", "pharma")
    if isinstance(theme_spec, str) and theme_spec in THEMES:
        t = dict(THEMES[theme_spec])
    else:
        t = dict(THEMES["pharma"])
        if isinstance(theme_spec, dict):
            if "primary_color"   in theme_spec: t["primary"]   = tuple(theme_spec["primary_color"])
            if "accent_color"    in theme_spec: t["accent"]    = tuple(theme_spec["accent_color"])
            if "highlight_color" in theme_spec: t["highlight"] = tuple(theme_spec["highlight_color"])

    # Page sizes
    pw, ph   = LETTER          # portrait: 612 × 792
    lw, lh   = landscape_ps(LETTER)   # landscape: 792 × 612

    # Available content widths
    port_avail = pw - 2 * _PORT_MARGIN
    land_avail = lw - 2 * _LAND_MARGIN

    # Styles
    styles = build_styles(t, fonts)

    # Doc setup
    doc = BaseDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=_PORT_MARGIN, rightMargin=_PORT_MARGIN,
        topMargin=_HEADER_H + 8, bottomMargin=_FOOTER_H + 8,
        title=meta.get("title", ""),
        author=meta.get("author", ""),
    )
    doc.report_meta  = meta
    doc.report_theme = t
    doc.report_fonts = fonts

    # Page frames
    cover_frame = Frame(0, 0, pw, ph,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover")

    body_frame  = Frame(
        _PORT_MARGIN, _FOOTER_H + 5,
        port_avail, ph - _HEADER_H - _FOOTER_H - 14,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0, id="body",
    )

    land_frame  = Frame(
        _LAND_MARGIN, _FOOTER_H + 5,
        land_avail, lh - _HEADER_H - _FOOTER_H - 14,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0, id="landscape",
    )

    cover_tpl    = PageTemplate(id="Cover",          frames=[cover_frame], onPage=make_cover_page)
    body_tpl     = PageTemplate(id="Body",           frames=[body_frame],  onPage=make_body_page)
    land_tpl     = PageTemplate(id="TableLandscape", frames=[land_frame],  onPage=make_table_landscape_page,
                                pagesize=(lw, lh))
    doc.addPageTemplates([cover_tpl, body_tpl, land_tpl])

    story = []

    # ── Cover ──────────────────────────────────────────────────────────────
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    # ── Table of Contents ──────────────────────────────────────────────────
    toc = TableOfContents()
    toc.levelStyles = [styles["TOCEntry0"], styles["TOCEntry1"]]
    story.append(Paragraph("Table of Contents", styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", thickness=2, color=hx("#0053A0"), spaceAfter=8))
    story.append(Spacer(1, 4))
    story.append(toc)
    story.append(PageBreak())

    # ── Executive Summary ──────────────────────────────────────────────────
    exec_text = spec.get("executive_summary", "")
    if exec_text:
        story.append(build_exec_summary(exec_text, styles, t, port_avail))
        story.append(Spacer(1, 14))

    # ── KPI Banner ─────────────────────────────────────────────────────────
    kpi_metrics = spec.get("kpi_metrics")
    if kpi_metrics:
        banner = build_kpi_banner(kpi_metrics, styles, port_avail)
        if banner:
            story.append(banner)
            story.append(Spacer(1, 18))

    # Build placement maps
    tables_by_section = {}
    for tbl in spec.get("tables", []):
        tables_by_section.setdefault(tbl.get("after_section", 0), []).append(tbl)

    charts_by_section = {}
    for cht in spec.get("charts", []):
        charts_by_section.setdefault(cht.get("after_section", 0), []).append(cht)

    images_by_section = {}
    for img in spec.get("images", []):
        images_by_section.setdefault(img.get("after_section", 0), []).append(img)

    tmp_dir = tempfile.mkdtemp()

    # ── Sections ───────────────────────────────────────────────────────────
    for sec_idx, section in enumerate(spec.get("sections", [])):
        heading  = section.get("heading", f"Section {sec_idx + 1}")
        body     = section.get("body", "")
        callout  = section.get("callout", "")

        # Section heading + Pfizer-blue underline rule
        story.append(Paragraph(f"{sec_idx + 1}.  {heading}", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=2, color=hx("#0053A0"), spaceAfter=8))

        for para_text in body.split("\n\n"):
            para_text = para_text.strip()
            if para_text:
                story.append(Paragraph(para_text, styles["ReportBody"]))

        for sub in section.get("subsections", []):
            story.append(Paragraph(sub.get("heading", ""), styles["SubsectionHeading"]))
            for para_text in sub.get("body", "").split("\n\n"):
                para_text = para_text.strip()
                if para_text:
                    story.append(Paragraph(para_text, styles["ReportBody"]))

        if callout:
            story.append(Spacer(1, 8))
            story.append(build_callout_box(callout, "Regulatory Context", styles, port_avail))

        # Tables after this section
        for tbl_spec_item in tables_by_section.get(sec_idx, []):
            tbl_title = tbl_spec_item.get("title", "")
            if tbl_spec_item.get("landscape"):
                story.append(NextPageTemplate("TableLandscape"))
                story.append(PageBreak())
                if tbl_title:
                    story.append(Paragraph(tbl_title, styles["TableTitle"]))
                    story.append(Spacer(1, 4))
                story.extend(build_table(tbl_spec_item, styles, t, fonts, land_avail))
                story.append(NextPageTemplate("Body"))
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 8))
                if tbl_title:
                    story.append(Paragraph(tbl_title, styles["TableTitle"]))
                story.extend(build_table(tbl_spec_item, styles, t, fonts, port_avail))
                story.append(Spacer(1, 8))

        # Charts after this section
        for cht_spec in charts_by_section.get(sec_idx, []):
            chart_path = render_chart(cht_spec, t, tmp_dir, fonts)
            if chart_path:
                story.append(Spacer(1, 10))
                img_w = min(port_avail, 6.0 * inch)
                story.append(Image(chart_path, width=img_w, height=img_w * 0.543))

                fig_num  = cht_spec.get("figure_number", "")
                cap_text = cht_spec.get("title", "")
                src_note = cht_spec.get("source_note", "")

                if fig_num:
                    caption_line = f"<b>{fig_num}.</b>  {cap_text}"
                else:
                    caption_line = cap_text
                story.append(Paragraph(caption_line, styles["FigureCaption"]))
                if src_note:
                    story.append(Paragraph(src_note, styles["SourceNote"]))

        # Images after this section
        for img_spec in images_by_section.get(sec_idx, []):
            img_path = img_spec.get("path", "")
            if img_path and os.path.isfile(img_path):
                w = min(img_spec.get("width_inches", 5.0) * inch, port_avail)
                story.append(Spacer(1, 8))
                story.append(Image(img_path, width=w))
                if img_spec.get("caption"):
                    story.append(Paragraph(img_spec["caption"], styles["Caption"]))

    doc.multiBuild(story)

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate a pharma-grade PDF report from a JSON spec.")
    parser.add_argument("--spec",   help="Path to JSON spec file (omit to read from stdin)")
    parser.add_argument("--output", required=True, help="Output PDF path")
    args = parser.parse_args()

    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    else:
        spec = json.load(sys.stdin)

    build_report(spec, args.output)
    print(f"PDF written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
