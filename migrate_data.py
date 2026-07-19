from app import create_app
from models import Student
from extensions import db


app = create_app()

with app.app_context():
    for student in Student.query.all():
        for mark in student.marks:
            mark.term = student.term
            mark.year = student.year
    db.session.commit()
    print("Done! Term and year copied to all marks.")