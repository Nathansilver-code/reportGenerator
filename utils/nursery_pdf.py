"""Builds the nursery report card PDF (one card per A4 page, any number of learners)."""
import io
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepInFrame, Image,
)

from utils.nursery_config import (
    SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_CONTACT,
    SKILLS, TRAITS, GRADE_LEVELS, GRADE_MAP, report_title,
)

NAVY = colors.HexColor("#0d2b6e")
BLUE = colors.HexColor("#1a56b0")
PALE = colors.HexColor("#eff6ff")
LINE = colors.HexColor("#c7d7ef")
GOLD = colors.HexColor("#c9a227")
WHITE = colors.white


def _style(name, **kw):
    return ParagraphStyle(name, spaceBefore=0, spaceAfter=0, **kw)


def _grade_table(heading, items, grades, width):
    """Heading row + one row per item; the grade cell is filled with the grade colour."""
    data = [[heading, "GRADE"]]
    for key, label in items:
        data.append([label, grades.get(key) or "-"])

    table = Table(data, colWidths=[width * 0.62, width * 0.38])
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9.5),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (0, -1), 10.5),
        ("TEXTCOLOR",     (0, 1), (0, -1), NAVY),
        ("LINEBELOW",     (0, 1), (0, -1), 0.6, LINE),
        ("FONTNAME",      (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (1, 1), (1, -1), 9.5),
        # white lines between the colour bars so each one stands apart
        ("LINEBELOW",     (1, 1), (1, -1), 3, WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
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


def _card(report, width, logo_path):
    label = _style("lbl", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=NAVY)
    value = _style("val", fontName="Helvetica", fontSize=10.5, leading=13, textColor=colors.black)
    remark = _style("rem", fontName="Helvetica-Oblique", fontSize=11, leading=15, textColor=NAVY)
    name_style = _style("nm", fontName="Helvetica-Bold", fontSize=15, leading=18,
                        textColor=NAVY, alignment=1)
    addr_style = _style("ad", fontName="Helvetica", fontSize=8.5, leading=11,
                        textColor=BLUE, alignment=1)
    title_style = _style("tt", fontName="Helvetica-Bold", fontSize=13, leading=16,
                         textColor=NAVY, alignment=1)
    foot_style = _style("ft", fontName="Helvetica-Bold", fontSize=8, leading=10,
                        textColor=BLUE, alignment=1)

    story = []

    # ---- Header: crest + school name and address ----
    text_block = [
        Paragraph(escape(SCHOOL_NAME), name_style),
        Spacer(1, 3),
        Paragraph(escape(SCHOOL_ADDRESS), addr_style),
        Paragraph(escape(SCHOOL_CONTACT), addr_style),
    ]
    if logo_path and os.path.exists(logo_path):
        iw, ih = ImageReader(logo_path).getSize()
        logo_h = 2.4 * cm
        logo = Image(logo_path, width=logo_h * iw / ih, height=logo_h)
        header = Table([[logo, text_block]], colWidths=[2.8 * cm, width - 2.8 * cm])
    else:
        header = Table([[text_block]], colWidths=[width])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 2, GOLD),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [header, Spacer(1, 10)]

    story += [Paragraph(f"<u>{escape(report_title(report.report_type))}</u>", title_style),
              Spacer(1, 10)]

    # ---- Learner details ----
    info = Table([
        [Paragraph("NAME:", label),          Paragraph(f"<b>{escape(report.full_name)}</b>", value),
         Paragraph("CLASS:", label),         Paragraph(escape(report.class_name), value)],
        [Paragraph("CLASS PLANNER:", label), Paragraph(escape(report.class_planner or "-"), value),
         Paragraph("TERM:", label),          Paragraph(f"{escape(report.term)} - {report.year}", value)],
    ], colWidths=[width * 0.18, width * 0.38, width * 0.12, width * 0.32])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX",        (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [info, Spacer(1, 12)]

    grades = report.grades or {}
    story += [_grade_table("SKILLS AND ABILITIES", SKILLS, grades, width), Spacer(1, 12)]
    story += [_grade_table("PERSONALITY AND CHARACTER", TRAITS, grades, width), Spacer(1, 12)]

    # ---- Head teacher's remarks ----
    remark_text = escape(report.head_remarks).replace("\n", "<br/>") if report.head_remarks \
        else "&nbsp;<br/>&nbsp;"
    remarks = Table([[Paragraph("HEAD TEACHER'S REMARKS:", label), Paragraph(remark_text, remark)]],
                    colWidths=[width * 0.27, width * 0.73])
    remarks.setStyle(TableStyle([
        ("BOX",   (0, 0), (-1, -1), 0.8, LINE),
        ("BACKGROUND", (0, 0), (0, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [remarks, Spacer(1, 8)]

    # ---- Next term and fees ----
    terms_tbl = Table([
        [Paragraph("NEXT TERM BEGINS ON:", label), Paragraph(escape(report.next_term_begins or "-"), value),
         Paragraph("FEES (DAY):", label),          Paragraph(escape(report.fees_day or "-"), value)],
        ["", "",
         Paragraph("FEES (BOARDERS):", label),     Paragraph(escape(report.fees_boarders or "-"), value)],
    ], colWidths=[width * 0.22, width * 0.24, width * 0.18, width * 0.36])
    terms_tbl.setStyle(TableStyle([
        ("SPAN",       (0, 0), (0, 1)),
        ("SPAN",       (1, 0), (1, 1)),
        ("BOX",        (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, LINE),
        ("BACKGROUND", (0, 0), (0, 1), PALE),
        ("BACKGROUND", (2, 0), (2, 1), PALE),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [terms_tbl, Spacer(1, 12)]

    # ---- Grading system legend ----
    cells = [g["name"].upper() for g in GRADE_LEVELS]
    legend = Table([["GRADING SYSTEM"] + [""] * (len(cells) - 1), cells],
                   colWidths=[width / len(cells)] * len(cells))
    lcmds = [
        ("SPAN",       (0, 0), (-1, 0)),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8.5),
        ("TEXTCOLOR",  (0, 0), (-1, 0), NAVY),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEAFTER",  (0, 1), (-2, 1), 2, WHITE),
    ]
    for i, g in enumerate(GRADE_LEVELS):
        lcmds.append(("BACKGROUND", (i, 1), (i, 1), colors.HexColor(g["color"])))
        lcmds.append(("TEXTCOLOR",  (i, 1), (i, 1), colors.HexColor(g["text"])))
    legend.setStyle(TableStyle(lcmds))
    story += [legend, Spacer(1, 10), Paragraph("NOT VALID WITHOUT THE SCHOOL STAMP", foot_style)]
    return story


def build_nursery_pdf(reports, logo_path=None):
    """Return PDF bytes with one nursery report card per A4 page."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    width = A4[0] - 3.0 * cm
    height = A4[1] - 2.4 * cm - 2        # small slack so a card is never "too large"

    story = []
    for i, report in enumerate(reports):
        if i:
            story.append(PageBreak())
        # "shrink" guarantees a card never spills onto a second page
        story.append(KeepInFrame(width, height, _card(report, width, logo_path),
                                 mode="shrink", vAlign="TOP"))
    doc.build(story)
    buf.seek(0)
    return buf.read()