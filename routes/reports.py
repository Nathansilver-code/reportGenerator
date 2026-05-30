
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Student, Teacher
from utils.grading import compute_student_results

reports_bp = Blueprint("reports", __name__)

PRIMARY_CLASSES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
TERMS           = ["Term 1", "Term 2", "Term 3"]


def _rank_students(students_data):
    """
    Assign positions (1st, 2nd, …) to a list of student result dicts.
    Ranking is based on total marks (descending).
    Students with equal totals share the same position (dense ranking).
    """
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


@reports_bp.route("/marksheet")
@login_required
def marksheet():
    class_name = request.args.get("class_name")
    term       = request.args.get("term", "Term 1")

    if not class_name:
        flash("Please select a class to view the marksheet.", "warning")
        return redirect(url_for("marks.select_class"))

    # ── KEY FIX 1: Admin queries ALL students in the class ──
    # Teacher queries ONLY their own students
    if current_user.is_admin:
        # Admin sees every student in this class regardless of which
        # teacher entered them
        students = Student.query.filter_by(
            class_name = class_name,
            term       = term
        ).order_by(Student.full_name).all()
    else:
        # Regular teacher sees only the students they registered
        students = Student.query.filter_by(
            teacher_id = current_user.id,
            class_name = class_name,
            term       = term
        ).order_by(Student.full_name).all()

    if not students:
        flash(f"No students found for {class_name} in {term}.", "info")
        return redirect(url_for("reports.reports_home"))

    # Compute results for every student
    results = []
    for student in students:
        if student.marks:
            computed = compute_student_results(student.marks)
            results.append({
                "student_id":   student.id,
                "full_name":    student.full_name,
                "class_name":   student.class_name,
                "teacher_name": student.teacher.full_name,  # show which teacher entered
                "total":        computed["total"],
                "average":      computed["average"],
                "aggregate":    computed["aggregate_sum"],
                "division":     computed["division"],
                "subjects":     computed["subjects"],
            })

    # Assign positions based on total marks
    position_map = _rank_students(results)
    for entry in results:
        entry["position"] = position_map.get(entry["student_id"], "-")

    # Re-sort by position for display
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

    # ── KEY FIX 2: Block teachers immediately ──────────────
    # If the logged-in user is NOT admin, deny access entirely.
    # abort(403) shows a "Forbidden" error page.
    if not current_user.can_view_reports:
        abort(403)

    # Admin can view ANY student's report card — no teacher_id filter
    student = Student.query.get_or_404(student_id)

    if not student.marks:
        flash("No marks found for this student.", "warning")
        return redirect(url_for("reports.reports_home"))

    # Compute full results
    computed = compute_student_results(student.marks)

    # Determine position within the class & term
    # Admin sees all classmates across all teachers for accurate ranking
    classmates = Student.query.filter_by(
        class_name = student.class_name,
        term       = student.term
    ).all()

    # Build ranking list from all classmates
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

    # Pass the student's own teacher name for display on the report card
    teacher = student.teacher

    return render_template(
        "report_card.html",
        student        = student,
        computed       = computed,
        position       = position,
        total_in_class = total_in_class,
        teacher        = teacher,
    )


# -----------------------------------------------------------
# Selector page — choose class/term before viewing marksheet
# -----------------------------------------------------------
@reports_bp.route("/reports")
@login_required
def reports_home():
    return render_template("reports_home.html",
                           classes=PRIMARY_CLASSES, terms=TERMS)
