
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Teacher

# Create a Blueprint named "auth" — all routes here are prefixed with nothing
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, skip the login page
    if current_user.is_authenticated:
        return redirect(url_for("marks.select_class"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Look up teacher by email
        teacher = Teacher.query.filter_by(email=email).first()

        if teacher and teacher.check_password(password):
            login_user(teacher)
            flash(f"Welcome back, {teacher.full_name}!", "success")
            # Redirect to the page the user originally wanted, or select_class
            next_page = request.args.get("next")
            return redirect(next_page or url_for("marks.select_class"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("marks.select_class"))

    if request.method == "POST":
        full_name        = request.form.get("full_name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic server-side validation
        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        # Check if email is already registered
        if Teacher.query.filter_by(email=email).first():
            flash("That email is already registered. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        # Create and save the new teacher
        new_teacher = Teacher(full_name=full_name, email=email)
        new_teacher.set_password(password)
        db.session.add(new_teacher)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
