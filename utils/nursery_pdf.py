"""Builds the nursery report card PDF (one card per A4 page, any number of learners).

Artwork lives in static/img/nursery/:  crest, header_cartoon, skills_cartoon,
character_cartoon, footer_strip  (all .png). Replace any of them with your own picture of
the same name to change the look. A missing picture is simply left out.

The writing is made as large as possible while the whole card still fits on one page:
every size grows by the same factor (see PDF_MAX_FONT_SCALE in nursery_config.py).
"""
import io
import math
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepInFrame, Image,
)

from utils.nursery_config import (
    SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_CONTACT,
    NEXT_TERM_BEGINS, FEES_DAY, FEES_BOARDERS, PDF_MAX_FONT_SCALE,
    SKILLS, TRAITS, GRADE_LEVELS, GRADE_MAP, report_title,
)

NAVY = colors.HexColor("#0d2b6e")
BLUE = colors.HexColor("#1a56b0")
PALE = colors.HexColor("#eff6ff")
LINE = colors.HexColor("#c7d7ef")
GOLD = colors.HexColor("#c9a227")
WHITE = colors.white

PAGE_MARGIN = 40          # space between the page edge and the content
ROW_H = 25                # height of a grade-table row at normal writing size
ART_W = 124               # width of the cartoon beside each grade table


# ── small helpers ──────────────────────────────────────────────────────────

def _style(name, **kw):
    return ParagraphStyle(name, spaceBefore=0, spaceAfter=0, **kw)


def _asset(img_dir, *parts):
    """Full path of a picture, or None if it is not there."""
    if not img_dir:
        return None
    path = os.path.join(img_dir, *parts)
    return path if os.path.exists(path) else None


def _fit_image(path, max_w, max_h):
    iw, ih = ImageReader(path).getSize()
    scale = min(max_w / iw, max_h / ih)
    img = Image(path, width=iw * scale, height=ih * scale)
    img.hAlign = "CENTER"
    return img


def _star_path(canvas, cx, cy, r):
    path = canvas.beginPath()
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    path.close()
    return path


def _content_height(flowables, width):
    return sum(fl.wrap(width, 10000)[1] for fl in flowables)


# ── the page border ─────────────────────────────────────────────────────────

def _page_border(canvas, doc):
    pw, ph = A4
    bead_colors = [colors.HexColor(g["color"]) for g in GRADE_LEVELS]
    canvas.saveState()

    outer, mid, inner = 14, 22, 30
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(1.6)
    canvas.roundRect(outer, outer, pw - 2 * outer, ph - 2 * outer, 12)
    canvas.setLineWidth(0.8)
    canvas.roundRect(inner, inner, pw - 2 * inner, ph - 2 * inner, 5)

    # a string of coloured beads between the two lines
    n = 0
    x0, y0, x1, y1 = mid, mid, pw - mid, ph - mid
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        length = math.hypot(bx - ax, by - ay)
        count = int(length // 12)
        for i in range(1, count):
            t = i / count
            canvas.setFillColor(bead_colors[n % len(bead_colors)])
            canvas.circle(ax + (bx - ax) * t, ay + (by - ay) * t, 3.4, stroke=0, fill=1)
            n += 1

    # a gold star in each corner
    canvas.setLineWidth(1.4)
    canvas.setStrokeColor(colors.HexColor("#f08c00"))
    canvas.setFillColor(colors.HexColor("#ffd43b"))
    for cx, cy in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        canvas.drawPath(_star_path(canvas, cx, cy, 11), stroke=1, fill=1)

    canvas.restoreState()


# ── building blocks of the card (S = writing-size factor) ────────────────────

def _grade_table(heading, items, grades, width, S):
    """Heading row + one row per item; the grade cell is filled with the grade colour."""
    data = [[heading, "GRADE"]]
    for key, label in items:
        data.append([label, grades.get(key) or "-"])

    row_h = ROW_H * S
    table = Table(data, colWidths=[width * 0.60, width * 0.40], rowHeights=[row_h] * len(data))
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9 * S),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (0, -1), 10 * S),
        ("TEXTCOLOR",     (0, 1), (0, -1), NAVY),
        ("LINEBELOW",     (0, 1), (0, -1), 0.6, LINE),
        ("FONTNAME",      (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (1, 1), (1, -1), 9.5 * S),
        ("LINEBELOW",     (1, 1), (1, -1), 3, WHITE),     # white gaps between colour bars
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (0, -1), 8),
    ]
    for i, (key, _label) in enumerate(items, start=1):
        level = GRADE_MAP.get(grades.get(key))
        if level:
            cmds.append(("BACKGROUND", (1, i), (1, i), colors.HexColor(level["color"])))
            cmds.append(("TEXTCOLOR",  (1, i), (1, i), colors.HexColor(level["text"])))
        else:
            cmds.append(("TEXTCOLOR",  (1, i), (1, i), colors.grey))
    table.setStyle(TableStyle(cmds))
    return table


def _grade_section(heading, items, grades, width, art_path, S):
    """A grade table with a cartoon beside it (full width if the picture is missing)."""
    if not art_path:
        return _grade_table(heading, items, grades, width, S)
    table_w = width - ART_W - 8
    table = _grade_table(heading, items, grades, table_w, S)
    art = _fit_image(art_path, ART_W - 6, ROW_H * S * (len(items) + 1))
    outer = Table([[table, art]], colWidths=[table_w + 8, ART_W])
    outer.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer


def _header(width, img_dir, S):
    name_style = _style("nm", fontName="Helvetica-Bold", fontSize=15 * S, leading=18 * S,
                        textColor=NAVY, alignment=1)
    addr_style = _style("ad", fontName="Helvetica", fontSize=8.5 * S, leading=10.5 * S,
                        textColor=BLUE, alignment=1)

    logo = _asset(img_dir, "nursery", "crest.png") or _asset(img_dir, "logo.png")
    cartoon = _asset(img_dir, "nursery", "header_cartoon.png")

    cells, widths = [], []
    if logo:
        iw, ih = ImageReader(logo).getSize()
        logo_h = 2.3 * cm
        cells.append(Image(logo, width=logo_h * iw / ih, height=logo_h))
        widths.append(logo_h * iw / ih + 8)
    art_w = 100 if cartoon else 0
    text_w = width - sum(widths) - art_w

    # the school name uses the writing size, but never more than one line wide
    size = min(15 * S, (text_w - 6) / stringWidth(SCHOOL_NAME, "Helvetica-Bold", 1))
    name_style.fontSize, name_style.leading = size, size * 1.2
    cells.append([Paragraph(escape(SCHOOL_NAME), name_style), Spacer(1, 3),
                  Paragraph(escape(SCHOOL_ADDRESS), addr_style),
                  Paragraph(escape(SCHOOL_CONTACT), addr_style)])
    widths.append(text_w)
    if cartoon:
        cells.append(_fit_image(cartoon, art_w, 66))
        widths.append(art_w)

    header = Table([cells], colWidths=widths)
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 2, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    return header


def _card(report, width, img_dir, S):
    label = _style("lbl", fontName="Helvetica-Bold", fontSize=9 * S, leading=11 * S, textColor=NAVY)
    value = _style("val", fontName="Helvetica", fontSize=10.5 * S, leading=13 * S, textColor=colors.black)
    remark = _style("rem", fontName="Helvetica-Oblique", fontSize=11 * S, leading=15 * S, textColor=NAVY)
    title_style = _style("tt", fontName="Helvetica-Bold", fontSize=13 * S, leading=16 * S,
                         textColor=NAVY, alignment=1)
    foot_style = _style("ft", fontName="Helvetica-Bold", fontSize=8 * S, leading=10 * S,
                        textColor=BLUE, alignment=1)

    story = [_header(width, img_dir, S), Spacer(1, 8)]
    story += [Paragraph(f"<u>{escape(report_title(report.report_type))}</u>", title_style),
              Spacer(1, 8)]

    # ---- Learner details ----
    info = Table([
        [Paragraph("NAME:", label),          Paragraph(f"<b>{escape(report.full_name)}</b>", value),
         Paragraph("CLASS:", label),         Paragraph(escape(report.class_name), value)],
        [Paragraph("CLASS PLANNER:", label), Paragraph(escape(report.class_planner or "-"), value),
         Paragraph("TERM:", label),          Paragraph(f"{escape(report.term)} - {report.year}", value)],
    ], colWidths=[width * 0.22, width * 0.34, width * 0.13, width * 0.31])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX",        (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [info, Spacer(1, 8)]

    grades = report.grades or {}
    story += [_grade_section("SKILLS AND ABILITIES", SKILLS, grades, width,
                             _asset(img_dir, "nursery", "skills_cartoon.png"), S), Spacer(1, 8)]
    story += [_grade_section("PERSONALITY AND CHARACTER", TRAITS, grades, width,
                             _asset(img_dir, "nursery", "character_cartoon.png"), S), Spacer(1, 8)]

    # ---- Head teacher's remarks ----
    remark_text = escape(report.head_remarks).replace("\n", "<br/>") if report.head_remarks \
        else "&nbsp;<br/>&nbsp;"
    remarks = Table([[Paragraph("HEAD TEACHER'S REMARKS:", label), Paragraph(remark_text, remark)]],
                    colWidths=[width * 0.30, width * 0.70])
    remarks.setStyle(TableStyle([
        ("BOX",   (0, 0), (-1, -1), 0.8, LINE),
        ("BACKGROUND", (0, 0), (0, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [remarks, Spacer(1, 6)]

    # ---- Next term and fees: the same on every card (set in nursery_config.py) ----
    terms_tbl = Table([
        [Paragraph("NEXT TERM BEGINS ON:", label), Paragraph(escape(NEXT_TERM_BEGINS), value)],
        [Paragraph("FEES (DAY):", label),          Paragraph(escape(FEES_DAY), value)],
        [Paragraph("FEES (BOARDERS):", label),     Paragraph(escape(FEES_BOARDERS), value)],
    ], colWidths=[width * 0.31, width * 0.69])
    terms_tbl.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, LINE),
        ("BACKGROUND", (0, 0), (0, -1), PALE),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [terms_tbl, Spacer(1, 8)]

    # ---- Grading system legend ----
    cells = [g["name"].upper() for g in GRADE_LEVELS]
    legend = Table([["GRADING SYSTEM"] + [""] * (len(cells) - 1), cells],
                   colWidths=[width / len(cells)] * len(cells))
    lcmds = [
        ("SPAN",       (0, 0), (-1, 0)),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8.5 * S),
        ("TEXTCOLOR",  (0, 0), (-1, 0), NAVY),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 7.5 * S),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEAFTER",  (0, 1), (-2, 1), 2, WHITE),
    ]
    for i, g in enumerate(GRADE_LEVELS):
        lcmds.append(("BACKGROUND", (i, 1), (i, 1), colors.HexColor(g["color"])))
        lcmds.append(("TEXTCOLOR",  (i, 1), (i, 1), colors.HexColor(g["text"])))
    legend.setStyle(TableStyle(lcmds))
    story += [legend, Spacer(1, 6)]

    strip = _asset(img_dir, "nursery", "footer_strip.png")
    if strip:
        story += [_fit_image(strip, width * 0.80, 32), Spacer(1, 3)]
    story.append(Paragraph("NOT VALID WITHOUT THE SCHOOL STAMP", foot_style))
    return story


def _fit_card(report, width, height, img_dir):
    """Biggest writing size (every size grows by the same factor) that keeps the card on one page."""
    S = PDF_MAX_FONT_SCALE
    while S >= 1.0:
        story = _card(report, width, img_dir, S)
        if _content_height(story, width) <= height:
            return story
        S = round(S - 0.02, 2)
    return _card(report, width, img_dir, 1.0)     # KeepInFrame below is the last safety net


def build_nursery_pdf(reports, img_dir=None):
    """Return PDF bytes with one nursery report card per A4 page.
    img_dir is the project's static/img folder (for the crest and cartoons)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
                            topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
    width = A4[0] - 2 * PAGE_MARGIN
    height = A4[1] - 2 * PAGE_MARGIN - 2     # small slack so a card is never "too large"

    story = []
    for i, report in enumerate(reports):
        if i:
            story.append(PageBreak())
        # "shrink" guarantees a card never spills onto a second page
        story.append(KeepInFrame(width, height, _fit_card(report, width, height, img_dir),
                                 mode="shrink", vAlign="TOP"))
    doc.build(story, onFirstPage=_page_border, onLaterPages=_page_border)
    buf.seek(0)
    return buf.read()