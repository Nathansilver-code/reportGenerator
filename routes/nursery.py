import io
import os
import re
from datetime import datetime

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, send_file, current_app)
from flask_login import login_required, current_user

from extensions import db
from models import NurseryReport
from utils.nursery_config import (
    SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_CONTACT,
    NURSERY_CLASSES, TERMS, REPORT_TYPES,
    NEXT_TERM_BEGINS, FEES_DAY, FEES_BOARDERS, SCREEN_FONT_SCALE, PRINT_FONT_SCALE,
    GRADE_LEVELS, GRADE_NAMES, GRADE_MAP, SKILLS, TRAITS, ALL_ITEMS, report_title,
)
from utils.nursery_pdf import build_nursery_pdf

nursery_bp = Blueprint("nursery", __name__)


# ── helpers ────────────────────────────────────────────────────────────────

def _visible_query():
    """Every logged-in user can see every nursery report (no per-teacher restriction)."""
    return NurseryReport.query


def _get_report(report_id):
    return _visible_query().filter(NurseryReport.id == report_id).first_or_404()


def _img_dir():
    """The project's static/img folder (crest + nursery cartoons live here)."""
    return os.path.join(current_app.root_path, "static", "img")


def _pick(value, allowed, default):
    return value if value in allowed else default


def _blank_form():
    """Starting values for a new report; a few fields carry over from the last one."""
    args = request.args
    return {
        "full_name":        "",
        "class_name":       _pick(args.get("class_name"), NURSERY_CLASSES, NURSERY_CLASSES[0]),
        "term":             _pick(args.get("term"), TERMS, TERMS[0]),
        "report_type":      _pick(args.get("report_type"), REPORT_TYPES, REPORT_TYPES[0]),
        "year":             datetime.utcnow().year,
        "class_planner":    args.get("planner") or current_user.full_name,
        "grades":           {},
        "head_remarks":     "",
    }


def _form_from_report(report):
    return {
        "full_name":        report.full_name,
        "class_name":       report.class_name,
        "term":             report.term,
        "report_type":      report.report_type,
        "year":             report.year,
        "class_planner":    report.class_planner,
        "grades":           dict(report.grades or {}),
        "head_remarks":     report.head_remarks,
    }


def _read_form():
    f = request.form
    return {
        "full_name":        f.get("full_name", "").strip(),
        "class_name":       f.get("class_name", ""),
        "term":             f.get("term", ""),
        "report_type":      f.get("report_type", ""),
        "year":             f.get("year", "").strip(),
        "class_planner":    f.get("class_planner", "").strip(),
        "grades":           {key: f.get(f"g_{key}", "") for key, _ in ALL_ITEMS},
        "head_remarks":     f.get("head_remarks", "").strip(),
    }


def _validate(form):
    """Returns a list of error messages (empty = OK). Converts form['year'] to int."""
    errors = []
    if not form["full_name"]:
        errors.append("Learner's name is required.")
    if form["class_name"] not in NURSERY_CLASSES:
        errors.append("Please choose a valid class.")
    if form["term"] not in TERMS:
        errors.append("Please choose a valid term.")
    if form["report_type"] not in REPORT_TYPES:
        errors.append("Please choose a valid report type.")
    try:
        form["year"] = int(form["year"])
        if not 2000 <= form["year"] <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        errors.append("Please enter a valid academic year, for example 2026.")

    limits = [("full_name", 150, "Name"), ("class_planner", 120, "Class planner"),
              ("head_remarks", 1000, "Head teacher's remarks")]
    for key, limit, label in limits:
        if len(form[key]) > limit:
            errors.append(f"{label} is too long (maximum {limit} characters).")

    missing = [label for key, label in ALL_ITEMS if form["grades"].get(key) not in GRADE_NAMES]
    if missing:
        errors.append("Please grade every item. Missing: " + ", ".join(missing) + ".")
    return errors


def _find_duplicate(form, exclude_id=None):
    query = NurseryReport.query.filter(
        db.func.lower(NurseryReport.full_name) == form["full_name"].lower(),
        NurseryReport.class_name == form["class_name"],
        NurseryReport.term == form["term"],
        NurseryReport.year == form["year"],
        NurseryReport.report_type == form["report_type"],
    )
    if exclude_id:
        query = query.filter(NurseryReport.id != exclude_id)
    return query.first()


def _render_form(form, report=None):
    return render_template(
        "nursery_form.html", form=form, report=report,
        classes=NURSERY_CLASSES, terms=TERMS, report_types=REPORT_TYPES,
        next_term_begins=NEXT_TERM_BEGINS, fees_day=FEES_DAY, fees_boarders=FEES_BOARDERS,
        skills=SKILLS, traits=TRAITS, grades=GRADE_LEVELS,
    )


def _apply(report, form):
    report.full_name        = form["full_name"]
    report.class_name       = form["class_name"]
    report.term             = form["term"]
    report.year             = form["year"]
    report.report_type      = form["report_type"]
    report.class_planner    = form["class_planner"]
    report.grades           = dict(form["grades"])      # a new dict so the change is saved
    report.head_remarks     = form["head_remarks"]
    # next-term date and fees are printed from nursery_config.py, not typed in per learner
    report.next_term_begins = ""
    report.fees_day         = ""
    report.fees_boarders    = ""


def _safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "report"


# ── routes ─────────────────────────────────────────────────────────────────

@nursery_bp.route("/nursery")
@login_required
def nursery_home():
    class_name  = _pick(request.args.get("class_name"), NURSERY_CLASSES, None)
    term        = _pick(request.args.get("term"), TERMS, None)
    report_type = _pick(request.args.get("report_type"), REPORT_TYPES, None)

    query = _visible_query()
    if class_name:
        query = query.filter_by(class_name=class_name)
    if term:
        query = query.filter_by(term=term)
    if report_type:
        query = query.filter_by(report_type=report_type)

    reports = query.order_by(NurseryReport.class_name, NurseryReport.full_name).all()
    return render_template("nursery_list.html", reports=reports,
                           classes=NURSERY_CLASSES, terms=TERMS, report_types=REPORT_TYPES,
                           selected_class=class_name, selected_term=term,
                           selected_type=report_type)


@nursery_bp.route("/nursery/new", methods=["GET", "POST"])
@login_required
def new_report():
    if request.method == "POST":
        form   = _read_form()
        errors = _validate(form)

        if not errors:
            duplicate = _find_duplicate(form)
            if duplicate:
                flash(f"A {form['report_type']} report for {duplicate.full_name} already "
                      f"exists for {form['term']}. You can edit it here.", "warning")
                return redirect(url_for("nursery.edit_report", report_id=duplicate.id))

        if errors:
            for message in errors:
                flash(message, "danger")
            return _render_form(form)

        report = NurseryReport(teacher_id=current_user.id)
        _apply(report, form)
        db.session.add(report)
        db.session.commit()
        flash(f"✔ Nursery report saved for {report.full_name}.", "success")

        if request.form.get("after") == "list":
            return redirect(url_for("nursery.nursery_home",
                                    class_name=report.class_name, term=report.term))
        # Save & add another: keep class, term and the details shared by the whole class
        return redirect(url_for("nursery.new_report",
                                class_name=report.class_name, term=report.term,
                                report_type=report.report_type, planner=report.class_planner))

    return _render_form(_blank_form())


@nursery_bp.route("/nursery/<int:report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_report(report_id):
    report = _get_report(report_id)

    if request.method == "POST":
        form   = _read_form()
        errors = _validate(form)
        if not errors and _find_duplicate(form, exclude_id=report.id):
            errors.append("Another report for this learner already exists for that class, "
                          "term and report type.")
        if errors:
            for message in errors:
                flash(message, "danger")
            return _render_form(form, report)

        _apply(report, form)
        db.session.commit()
        flash(f"✔ Report updated for {report.full_name}.", "success")
        return redirect(url_for("nursery.nursery_home",
                                class_name=report.class_name, term=report.term))

    return _render_form(_form_from_report(report), report)


@nursery_bp.route("/nursery/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id):
    report = _get_report(report_id)
    class_name, term, name = report.class_name, report.term, report.full_name
    db.session.delete(report)
    db.session.commit()
    flash(f"Report deleted for {name}.", "info")
    return redirect(url_for("nursery.nursery_home", class_name=class_name, term=term))


@nursery_bp.route("/nursery/<int:report_id>/report")
@login_required
def report_card(report_id):
    report = _get_report(report_id)
    return render_template(
        "nursery_report.html", report=report, title=report_title(report.report_type),
        next_term_begins=NEXT_TERM_BEGINS, fees_day=FEES_DAY, fees_boarders=FEES_BOARDERS,
        font_scale=SCREEN_FONT_SCALE, print_font_scale=PRINT_FONT_SCALE,
        skills=SKILLS, traits=TRAITS, grades=GRADE_LEVELS, grade_map=GRADE_MAP,
        school_name=SCHOOL_NAME, school_address=SCHOOL_ADDRESS, school_contact=SCHOOL_CONTACT,
    )


@nursery_bp.route("/nursery/<int:report_id>/pdf")
@login_required
def download_pdf(report_id):
    report = _get_report(report_id)
    pdf = build_nursery_pdf([report], _img_dir())
    return send_file(
        io.BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
        download_name=f"NurseryReport_{_safe_name(report.full_name)}_"
                      f"{_safe_name(report.class_name)}_{_safe_name(report.term)}.pdf")


@nursery_bp.route("/nursery/bulk-pdf", methods=["POST"])
@login_required
def bulk_pdf():
    """Selected learners' report cards in one PDF, one card per page."""
    ids = [int(i) for i in request.form.getlist("report_ids") if i.isdigit()]
    if not ids:
        flash("Please select at least one learner.", "warning")
        return redirect(url_for("nursery.nursery_home"))

    reports = (NurseryReport.query.filter(NurseryReport.id.in_(ids))
               .order_by(NurseryReport.class_name, NurseryReport.full_name).all())
    if not reports:
        flash("No reports found for the selected learners.", "warning")
        return redirect(url_for("nursery.nursery_home"))

    pdf = build_nursery_pdf(reports, _img_dir())
    return send_file(io.BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
                     download_name="NurseryReports.pdf")red
def bulk_pdf():
    """Selected learners' report cards in one PDF, one card per page."""
    if not current_user.can_view_reports:
        abort(403)
    ids = [int(i) for i in request.form.getlist("report_ids") if i.isdigit()]
    if not ids:
        flash("Please select at least one learner.", "warning")
        return redirect(url_for("nursery.nursery_home"))

    reports = (NurseryReport.query.filter(NurseryReport.id.in_(ids))
               .order_by(NurseryReport.class_name, NurseryReport.full_name).all())
    if not reports:
        flash("No reports found for the selected learners.", "warning")
        return redirect(url_for("nursery.nursery_home"))

    pdf = build_nursery_pdf(reports, _logo_path())
    return send_file(io.BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
                     download_name="NurseryReports.pdf")