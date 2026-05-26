
from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    
    role = db.Column(db.String(20), nullable=False, default="teacher")

    
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    students = db.relationship("Student", backref="teacher", lazy=True)

    
    def set_password(self, password):
        """Hash and store the password — never store plain text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the supplied password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    
    @property
    def is_admin(self):
        """True when this teacher account is the system administrator."""
        return self.role == "admin"

    @property
    def is_teacher(self):
        """True for regular (non-admin) teacher accounts."""
        return self.role == "teacher"

    
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

    
    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

   
    _is_active = db.Column("is_active", db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Teacher {self.email} role={self.role}>"


@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(int(user_id))


class Student(db.Model):
    __tablename__ = "students"

    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(150), nullable=False)

    
    class_name = db.Column(db.String(10), nullable=False)

    
    term       = db.Column(db.String(10), nullable=False, default="Term 1")
    year       = db.Column(db.Integer,    nullable=False, default=datetime.utcnow().year)

    
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    marks = db.relationship("Mark", backref="student", uselist=False, lazy=True)

    def __repr__(self):
        return f"<Student {self.full_name} | {self.class_name}>"


class Mark(db.Model):
    __tablename__ = "marks"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    
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


