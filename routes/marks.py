from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Mark, LOWER_PRIMARY_CLASSES

marks_bp = Blueprint("marks", __name__)

PRIMARY_CLASSES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
TERMS           = ["Term 1", "Term 2", "Term 3"]
EXAM_TYPES      = ["Mid Term", "Pre-End", "End of Term"]


@marks_bp.route("/select-class", methods=["GET", "POST"])
@login_required
def select_class():
    if request.method == "POST":
        selected_class = request.form.get("class_name")
        selected_term  = request.form.get("term")
        selected_exam  = request.form.get("exam_type", "Mid Term")

        if selected_class not in PRIMARY_CLASSES:
            flash("Please select a valid class.", "danger")
            return render_template("select_class.html",
                                   classes=PRIMARY_CLASSES,
                                   terms=TERMS,
                                   exam_types=EXAM_TYPES)

        return redirect(url_for("marks.register_student",
                                class_name=selected_class,
                                term=selected_term,
                                exam_type=selected_exam))

    return render_template("select_class.html",
                           classes=PRIMARY_CLASSES,
                           terms=TERMS,
                           exam_types=EXAM_TYPES)


@marks_bp.route("/register-student", methods=["GET", "POST"])
@login_required
def register_student():
    class_name = request.args.get("class_name") or request.form.get("class_name")
    term       = request.args.get("term")       or request.form.get("term", "Term 1")
    exam_type  = request.args.get("exam_type")  or request.form.get("exam_type", "Mid Term")

    if not class_name:
        flash("No class selected. Please start again.", "warning")
        return redirect(url_for("marks.select_class"))

    is_lower = class_name in LOWER_PRIMARY_CLASSES

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()

        if not full_name:
            flash("Student name is required.", "danger")
            return render_template("register_student.html",
                                   class_name=class_name, term=term,
                                   exam_type=exam_type, is_lower=is_lower)

        try:
            english = float(request.form.get("english", 0))
            math    = float(request.form.get("math",    0))

            if is_lower:
                lit_a = float(request.form.get("lit_a", 0))
                lit_b = float(request.form.get("lit_b", 0))
                re    = float(request.form.get("re",    0))
                lug   = float(request.form.get("lug",   0))
                science, sst = 0, 0
            else:
                science = float(request.form.get("science", 0))
                sst     = float(request.form.get("sst",     0))
                lit_a = lit_b = re = lug = 0

        except ValueError:
            flash("Please enter valid numeric marks.", "danger")
            return render_template("register_student.html",
                                   class_name=class_name, term=term,
                                   exam_type=exam_type, is_lower=is_lower)

        # Validate marks are 0–100
        if is_lower:
            checks = [("Literacy A", lit_a), ("Literacy B", lit_b),
                      ("English", english), ("Mathematics", math),
                      ("R.E.", re), ("Luganda", lug)]
        else:
            checks = [("English", english), ("Mathematics", math),
                      ("Science", science), ("SST", sst)]

        for subject, mark in checks:
            if not (0 <= mark <= 100):
                flash(f"{subject} mark must be between 0 and 100.", "danger")
                return render_template("register_student.html",
                                       class_name=class_name, term=term,
                                       exam_type=exam_type, is_lower=is_lower)

        from datetime import datetime
        student = Student(
            full_name  = full_name,
            class_name = class_name,
            term       = term,
            year       = datetime.utcnow().year,
            teacher_id = current_user.id
        )
        db.session.add(student)
        db.session.flush()

        mark_record = Mark(
            student_id = student.id,
            exam_type  = exam_type,
            english    = english,
            math       = math,
            science    = science,
            sst        = sst,
            lit_a      = lit_a,
            lit_b      = lit_b,
            re         = re,
            lug        = lug,
        )
        db.session.add(mark_record)
        db.session.commit()

        flash(f"✔ {full_name} registered successfully!", "success")
        return redirect(url_for("marks.register_student",
                                class_name=class_name,
                                term=term,
                                exam_type=exam_type))

    return render_template("register_student.html",
                           class_name=class_name, term=term,
                           exam_type=exam_type, is_lower=is_lower)


@marks_bp.route("/add-marks/<int:student_id>", methods=["GET", "POST"])
@login_required
def add_marks(student_id):
    """Add a second set of marks (End of Term) for an existing student."""
    student   = Student.query.filter_by(id=student_id, teacher_id=current_user.id).first_or_404()
    is_lower  = student.class_name in LOWER_PRIMARY_CLASSES
    exam_type = request.args.get("exam_type") or request.form.get("exam_type", "End of Term")

    # Check if marks for this exam type already exist
    existing = Mark.query.filter_by(student_id=student_id, exam_type=exam_type).first()

    if request.method == "POST":
        try:
            english = float(request.form.get("english", 0))
            math    = float(request.form.get("math",    0))

            if is_lower:
                lit_a = float(request.form.get("lit_a", 0))
                lit_b = float(request.form.get("lit_b", 0))
                re    = float(request.form.get("re",    0))
                lug   = float(request.form.get("lug",   0))
                science, sst = 0, 0
            else:
                science = float(request.form.get("science", 0))
                sst     = float(request.form.get("sst",     0))
                lit_a = lit_b = re = lug = 0

        except ValueError:
            flash("Please enter valid numeric marks.", "danger")
            return render_template("add_marks.html",
                                   student=student, exam_type=exam_type,
                                   is_lower=is_lower, existing=existing)

        if existing:
            # Update existing marks
            existing.english = english
            existing.math    = math
            existing.science = science
            existing.sst     = sst
            existing.lit_a   = lit_a
            existing.lit_b   = lit_b
            existing.re      = re
            existing.lug     = lug
        else:
            # Create new mark record
            mark_record = Mark(
                student_id = student_id,
                exam_type  = exam_type,
                english    = english,
                math       = math,
                science    = science,
                sst        = sst,
                lit_a      = lit_a,
                lit_b      = lit_b,
                re         = re,
                lug        = lug,
            )
            db.session.add(mark_record)

        db.session.commit()
        flash(f"✔ {exam_type} marks saved for {student.full_name}!", "success")
        return redirect(url_for("marks.list_students",
                                class_name=student.class_name,
                                term=student.term))

    return render_template("add_marks.html",
                           student=student, exam_type=exam_type,
                           is_lower=is_lower, existing=existing)


@marks_bp.route("/students")
@login_required
def list_students():
    class_name = request.args.get("class_name")
    term       = request.args.get("term")

    query = Student.query.filter_by(teacher_id=current_user.id)
    if class_name:
        query = query.filter_by(class_name=class_name)
    if term:
        query = query.filter_by(term=term)

    students = query.order_by(Student.class_name, Student.full_name).all()
    return render_template("students_list.html",
                           students=students,
                           classes=PRIMARY_CLASSES,
                           terms=TERMS,
                           exam_types=EXAM_TYPES,
                           selected_class=class_name,
                           selected_term=term)


@marks_bp.route("/delete-student/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    student = Student.query.filter_by(
        id=student_id, teacher_id=current_user.id
    ).first_or_404()

    class_name = student.class_name
    term       = student.term

    # Delete all mark records for this student
    for mark in student.marks:
        db.session.delete(mark)
    db.session.delete(student)
    db.session.commit()

    flash("Student record deleted.", "info")
    return redirect(url_for("marks.list_students",
                            class_name=class_name, term=term))