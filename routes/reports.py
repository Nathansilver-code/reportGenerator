from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from models import Student, Teacher
from utils.grading import compute_student_results

import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


reports_bp = Blueprint("reports", __name__)

PRIMARY_CLASSES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
TERMS           = ["Term 1", "Term 2", "Term 3"]


def _rank_students(students_data):
    sorted_data = sorted(students_data, key=lambda x: x["total"], reverse=True)
    position   = 1
    prev_total = None
    for i, entry in enumerate(sorted_data):
        if entry["total"] != prev_total:
            position   = i + 1
            prev_total = entry["total"]
        entry["position"] = position
    position_map = {entry["student_id"]: entry["position"] for entry in sorted_data}
    return position_map


def _get_marksheet_data(class_name, term):
    if current_user.is_admin:
        students = Student.query.filter_by(class_name=class_name, term=term).all()
    else:
        students = Student.query.filter_by(teacher_id=current_user.id, class_name=class_name, term=term).all()

    results = []
    for student in students:
        if student.marks:
            computed = compute_student_results(student.marks)
            results.append({
                "student_id": student.id,
                "full_name":  student.full_name,
                "total":      computed["total"],
                "aggregate":  computed["aggregate_sum"],
                "division":   computed["division"],
                "subjects":   computed["subjects"],
                "is_lower":   computed["is_lower"],
            })

    position_map = _rank_students(results)
    for entry in results:
        entry["position"] = position_map.get(entry["student_id"], "-")
    results.sort(key=lambda x: x["position"])
    return results


@reports_bp.route("/report-card/<int:student_id>/pdf")
@login_required
def download_report_pdf(student_id):
    student = Student.query.get_or_404(student_id)

    if not student.marks:
        flash("No marks found for this student.", "warning")
        return redirect(url_for("reports.reports_home"))

    computed = compute_student_results(student.marks)

    classmates = Student.query.filter_by(
        class_name=student.class_name,
        term=student.term
    ).all()
    class_results = []
    for cm in classmates:
        if cm.marks:
            class_results.append({"student_id": cm.id, "total": cm.marks.total})
    position_map   = _rank_students(class_results)
    position       = position_map.get(student_id, "-")
    total_in_class = len(class_results)
    teacher        = student.teacher

    # Safe year fallback
    student_year = getattr(student, 'year', None) or datetime.utcnow().year

    buf = io.BytesIO()
    # ── A4 portrait ──
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    # A4 usable width = 21cm - 3cm margins = 18cm
    PAGE_W = 18*cm

    NAVY  = colors.HexColor("#0d2b6e")
    BLUE  = colors.HexColor("#1a56b0")
    PALE  = colors.HexColor("#eff6ff")
    WHITE = colors.white

    title_style = ParagraphStyle("title",
        fontName="Helvetica-Bold", fontSize=16,
        textColor=WHITE, alignment=1, spaceAfter=3)
    sub_style = ParagraphStyle("sub",
        fontName="Helvetica", fontSize=10,
        textColor=WHITE, alignment=1, spaceAfter=4)
    section_style = ParagraphStyle("section",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=BLUE, spaceBefore=8, spaceAfter=5)
    comment_style = ParagraphStyle("comment",
        fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#0d2b6e"),
        leading=14, spaceBefore=4, spaceAfter=4)

    story = []

    # ── Banner ──
    banner_data = [
        [Paragraph("MARANATHA SCHOOLS", title_style)],
        [Paragraph(
            f"Student Report Card  |  {student.term}  |  Academic Year {student_year}",
            sub_style)],
    ]
    banner = Table(banner_data, colWidths=[PAGE_W])
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.3*cm))

    # ── Student Info ──
    story.append(Paragraph("STUDENT INFORMATION", section_style))
    info_data = [
        ["Full Name",     student.full_name,  "Class",         student.class_name],
        ["Term",          student.term,        "Academic Year", str(student_year)],
        ["Class Teacher", teacher.full_name,   "Position",      f"{position} / {total_in_class}"],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTNAME",      (2,0), (2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("BACKGROUND",    (0,0), (-1,-1), PALE),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#dbeafe")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Academic Performance ──
    story.append(Paragraph("ACADEMIC PERFORMANCE", section_style))
    subj_data = [["Subject", "Marks (/100)", "Grade", "Agg.", "Remark"]]
    for subj, details in computed["subjects"].items():
        subj_data.append([
            subj,
            str(details["mark"]),
            details["grade"],
            str(details["aggregate"]),
            details["remark"],
        ])
    subj_table = Table(subj_data,
        colWidths=[5*cm, 3.5*cm, 2*cm, 2*cm, 5.5*cm],
        repeatRows=1)
    subj_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#dbeafe")),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, PALE]),
        ("ALIGN",         (1,0), (3,-1),  "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(subj_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Summary ──
    summary_data = [[
        Paragraph(f"<b><font color='#93c5fd' size=16>{computed['total']}</font></b><br/>"
                  f"<font color='white' size=8>Total / {computed['max_total']}</font>",
                  ParagraphStyle("s", alignment=1)),
        Paragraph(f"<b><font color='#93c5fd' size=16>{computed['aggregate_sum']}</font></b><br/>"
                  f"<font color='white' size=8>Aggregate Sum</font>",
                  ParagraphStyle("s", alignment=1)),
        Paragraph(f"<b><font color='#93c5fd' size=16>{computed['division']}</font></b><br/>"
                  f"<font color='white' size=8>Division</font>",
                  ParagraphStyle("s", alignment=1)),
    ]]
    summary_table = Table(summary_data, colWidths=[6*cm, 6*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Comment ──
    story.append(Paragraph("CLASS TEACHER'S COMMENT", section_style))
    story.append(Paragraph(computed["comment"], comment_style))
    story.append(Spacer(1, 0.5*cm))

    # ── Signatures ──
    sig_data = [["Class Teacher's Signature & Date", "Head Teacher's Signature & Date"]]
    sig_table = Table(sig_data, colWidths=[9*cm, 9*cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("TEXTCOLOR",   (0,0), (-1,-1), BLUE),
        ("LINEABOVE",   (0,0), (-1,-1), 0.5, BLUE),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
    ]))
    story.append(sig_table)

    doc.build(story)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"ReportCard_{student.full_name}_{student.term}.pdf"
    )


@reports_bp.route("/marksheet")
@login_required
def marksheet():
    class_name = request.args.get("class_name")
    term       = request.args.get("term", "Term 1")

    if not class_name:
        flash("Please select a class to view the marksheet.", "warning")
        return redirect(url_for("marks.select_class"))

    if current_user.is_admin:
        students = Student.query.filter_by(
            class_name=class_name, term=term
        ).order_by(Student.full_name).all()
    else:
        students = Student.query.filter_by(
            teacher_id=current_user.id, class_name=class_name, term=term
        ).order_by(Student.full_name).all()

    if not students:
        flash(f"No students found for {class_name} in {term}.", "info")
        return redirect(url_for("reports.reports_home"))

    results = []
    for student in students:
        if student.marks:
            computed = compute_student_results(student.marks)
            results.append({
                "student_id":   student.id,
                "full_name":    student.full_name,
                "class_name":   student.class_name,
                "teacher_name": student.teacher.full_name,
                "total":        computed["total"],
                "average":      computed["average"],
                "aggregate":    computed["aggregate_sum"],
                "division":     computed["division"],
                "subjects":     computed["subjects"],
            })

    position_map = _rank_students(results)
    for entry in results:
        entry["position"] = position_map.get(entry["student_id"], "-")
    results.sort(key=lambda x: x["position"])

    return render_template(
        "marksheet.html",
        results    = results,
        class_name = class_name,
        term       = term,
        teacher    = current_user,
        classes    = PRIMARY_CLASSES,
        terms      = TERMS,
    )


@reports_bp.route("/report/<int:student_id>")
@login_required
def report_card(student_id):
    if not current_user.can_view_reports:
        abort(403)

    student = Student.query.get_or_404(student_id)

    if not student.marks:
        flash("No marks found for this student.", "warning")
        return redirect(url_for("reports.reports_home"))

    computed = compute_student_results(student.marks)

    classmates = Student.query.filter_by(
        class_name=student.class_name,
        term=student.term
    ).all()

    class_results = []
    for cm in classmates:
        if cm.marks:
            class_results.append({
                "student_id": cm.id,
                "total":      cm.marks.total,
            })

    position_map   = _rank_students(class_results)
    position       = position_map.get(student_id, "-")
    total_in_class = len(class_results)
    teacher        = student.teacher

    return render_template(
        "report_card.html",
        student        = student,
        computed       = computed,
        position       = position,
        total_in_class = total_in_class,
        teacher        = teacher,
    )


@reports_bp.route("/reports")
@login_required
def reports_home():
    return render_template("reports_home.html",
                           classes=PRIMARY_CLASSES, terms=TERMS)


@reports_bp.route("/marksheet/download/excel")
@login_required
def download_excel():
    class_name = request.args.get("class_name")
    term = request.args.get("term", "Term 1")
    results = _get_marksheet_data(class_name, term)
    is_lower = class_name in ["P1", "P2", "P3"]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{class_name} {term}"

    if is_lower:
        headers = ["Pos.", "Name", "Lit A", "Lit B", "English", "Math", "R.E.", "Luganda", "Total", "Aggregate", "Division"]
        subj_order = ["Literacy A", "Literacy B", "English", "Mathematics", "R.E.", "Luganda"]
    else:
        headers = ["Pos.", "Name", "English", "Math", "Science", "SST", "Total", "Aggregate", "Division"]
        subj_order = ["English", "Mathematics", "Science", "Social Studies"]

    ws.append(headers)
    for r in results:
        row = [r["position"], r["full_name"]]
        for subj in subj_order:
            row.append(r["subjects"].get(subj, {}).get("mark", ""))
        row += [r["total"], r["aggregate"], r["division"]]
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Marksheet_{class_name}_{term}.xlsx")


@reports_bp.route("/marksheet/download/pdf")
@login_required
def download_pdf():
    class_name = request.args.get("class_name")
    term = request.args.get("term", "Term 1")
    results = _get_marksheet_data(class_name, term)
    is_lower = class_name in ["P1", "P2", "P3"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm)

    if is_lower:
        headers = ["Pos.", "Name", "Lit A", "Lit B", "Eng", "Math", "R.E.", "Lug", "Total", "Agg", "Division"]
        subj_order = ["Literacy A", "Literacy B", "English", "Mathematics", "R.E.", "Luganda"]
    else:
        headers = ["Pos.", "Name", "Eng", "Math", "Sci", "SST", "Total", "Agg", "Division"]
        subj_order = ["English", "Mathematics", "Science", "Social Studies"]

    table_data = [headers]
    for r in results:
        row = [str(r["position"]), r["full_name"]]
        for subj in subj_order:
            row.append(str(r["subjects"].get(subj, {}).get("mark", "")))
        row += [str(r["total"]), str(r["aggregate"]), r["division"]]
        table_data.append(row)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a6e3c")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("ALIGN",      (1,1), (1,-1),  "LEFT"),
    ]))

    doc.build([t])
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"Marksheet_{class_name}_{term}.pdf")