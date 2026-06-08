# ============================================================
# models.py — SQLAlchemy Database Models
# Defines: Teacher (user with role), Student, Mark
#
# ROLES:
#   'admin'   → full access: manages teacher accounts, sees
#               all marksheets, all reports, all classes
#   'teacher' → limited access: enters marks, sees marksheets
#               and results for their own class ONLY.
#               Cannot view individual report cards.
# ============================================================

from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# -----------------------------------------------------------
# Teacher Model — represents a registered school teacher
# UserMixin gives Flask-Login helpers (is_authenticated, etc.)
# -----------------------------------------------------------
class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # -----------------------------------------------------------
    # role: 'admin' or 'teacher'
    #   - 'admin'   → set manually or via a seed script (only one)
    #   - 'teacher' → all newly registered accounts default here
    # -----------------------------------------------------------
    role = db.Column(db.String(20), nullable=False, default="teacher")

    # admin can deactivate a teacher account without deleting it
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One teacher can have many student records
    students = db.relationship("Student", backref="teacher", lazy=True)

    # ── Password helpers ────────────────────────────────────
    def set_password(self, password):
        """Hash and store the password — never store plain text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the supplied password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ── Role-check properties ───────────────────────────────
    @property
    def is_admin(self):
        """True when this teacher account is the system administrator."""
        return self.role == "admin"

    @property
    def is_teacher(self):
        """True for regular (non-admin) teacher accounts."""
        return self.role == "teacher"

    # ── Permission helpers (use these in routes + templates) ─
    @property
    def can_view_reports(self):
        """
        Only the admin can open individual student report cards.
        Regular teachers see marksheets and aggregates but NOT reports.
        """
        return self.role == "admin"

    @property
    def can_manage_accounts(self):
        """Only the admin can create, edit, or deactivate teacher accounts."""
        return self.role == "admin"

    @property
    def can_view_all_classes(self):
        """
        Admin sees every class across all teachers.
        Regular teachers only see students assigned to them.
        """
        return self.role == "admin"

    # ── Flask-Login: respect the is_active flag ─────────────
    # Flask-Login calls get_id() and checks is_active automatically
    # when @login_required is used, as long as we override this property.
    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    # Store the actual boolean in a private-ish column alias
    _is_active = db.Column("is_active", db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Teacher {self.email} role={self.role}>"


# Flask-Login callback: loads the teacher from the session by id
@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(int(user_id))


# -----------------------------------------------------------
# Student Model — one record per learner registration
# -----------------------------------------------------------
class Student(db.Model):
    __tablename__ = "students"

    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(150), nullable=False)

    # Class level: P1–P7 (Primary 1 to 7)
    class_name = db.Column(db.String(10), nullable=False)

    # Term: Term 1, Term 2, or Term 3
    term       = db.Column(db.String(10), nullable=False, default="Term 1")
    year       = db.Column(db.Integer,    nullable=False, default=datetime.utcnow().year)

    # Which teacher registered this student
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Each student has exactly one mark record
    marks = db.relationship("Mark", backref="student", uselist=False, lazy=True)

    def __repr__(self):
        return f"<Student {self.full_name} | {self.class_name}>"


# -----------------------------------------------------------
# Mark Model — stores raw marks for each subject
# -----------------------------------------------------------
class Mark(db.Model):
    __tablename__ = "marks"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    # Four core subjects for Uganda primary curriculum
    english = db.Column(db.Float, nullable=False, default=0)
    math    = db.Column(db.Float, nullable=False, default=0)
    science = db.Column(db.Float, nullable=False, default=0)
    sst     = db.Column(db.Float, nullable=False, default=0)  # Social Studies

    @property
    def total(self):
        """Sum of all four subjects (max 400)."""
        return self.english + self.math + self.science + self.sst

    @property
    def average(self):
        """Average mark across four subjects."""
        return self.total / 4

    def __repr__(self):
        return f"<Mark student_id={self.student_id} total={self.total}>"


# ============================================================
# HOW TO USE THE ROLE SYSTEM IN YOUR ROUTES
# ============================================================
#
# ── 1. Protecting a route so only admin can access it ───────
#
#   from flask_login import current_user
#   from flask import abort
#
#   @app.route('/admin/accounts')
#   @login_required
#   def manage_accounts():
#       if not current_user.can_manage_accounts:
#           abort(403)   # Forbidden
#       teachers = Teacher.query.all()
#       return render_template('admin/accounts.html', teachers=teachers)
#
#
# ── 2. Protecting the report card route ─────────────────────
#
#   @app.route('/report/<int:student_id>')
#   @login_required
#   def report_card(student_id):
#       if not current_user.can_view_reports:
#           abort(403)   # Regular teachers land here
#       student = Student.query.get_or_404(student_id)
#       return render_template('report_card.html', student=student)
#
#
# ── 3. Filtering students for regular teachers ───────────────
#
#   @app.route('/marksheet/<class_name>')
#   @login_required
#   def marksheet(class_name):
#       if current_user.can_view_all_classes:
#           # Admin sees everyone in that class
#           students = Student.query.filter_by(class_name=class_name).all()
#       else:
#           # Teacher sees only their own students
#           students = Student.query.filter_by(
#               class_name=class_name,
#               teacher_id=current_user.id
#           ).all()
#       return render_template('marksheet.html', students=students)
#
#
# ── 4. Hiding the Report button in templates ─────────────────
#
#   {% if current_user.can_view_reports %}
#     <a href="{{ url_for('report_card', student_id=s.id) }}"
#        class="btn-report">📄 Report</a>
#   {% endif %}
#
#
# ── 5. Creating the first admin (run once in Flask shell) ────
#
#   flask shell
#   >>> from models import Teacher
#   >>> from extensions import db
#   >>> admin = Teacher(full_name="Head Teacher", email="admin@greenhill.ug", role="admin")
#   >>> admin.set_password("StrongPassword123")
#   >>> db.session.add(admin)
#   >>> db.session.commit()
#
# ============================================================
