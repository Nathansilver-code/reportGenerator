LOWER_PRIMARY_CLASSES = ["P1", "P2", "P3"]
P3_CLASSES = ["P3"]
LOWER_PRIMARY_ONLY = ["P1", "P2"]


def get_grade(mark, max_mark=100, class_name=None):

    if mark is None or max_mark is None or max_mark == 0:
        return {"grade": "N/A", "aggregate": 0, "remark": "No Mark"}

    percentage = (mark / max_mark) * 100

    if class_name in P3_CLASSES:
        # P3 grading
        if percentage >= 90:
            return {"grade": "D1", "aggregate": 1, "remark": "Excellent"}
        elif percentage >= 80:
            return {"grade": "D2", "aggregate": 2, "remark": "Very Good"}
        elif percentage >= 70:
            return {"grade": "C3", "aggregate": 3, "remark": "Good"}
        elif percentage >= 60:
            return {"grade": "C4", "aggregate": 4, "remark": "Fair"}
        elif percentage >= 55:
            return {"grade": "C5", "aggregate": 5, "remark": "Pass"}
        elif percentage >= 50:
            return {"grade": "C6", "aggregate": 6, "remark": "Pass"}
        elif percentage >= 45:
            return {"grade": "P7", "aggregate": 7, "remark": "Weak Pass"}
        elif percentage >= 40:
            return {"grade": "P8", "aggregate": 8, "remark": "Weak Pass"}
        else:
            return {"grade": "F9", "aggregate": 9, "remark": "Fail"}
    else:
        # P1 & P2 grading
        if percentage >= 90:
            return {"grade": "D1", "aggregate": 1, "remark": "Excellent"}
        elif percentage >= 80:
            return {"grade": "D2", "aggregate": 2, "remark": "Very Good"}
        elif percentage >= 75:
            return {"grade": "C3", "aggregate": 3, "remark": "Good"}
        elif percentage >= 70:
            return {"grade": "C4", "aggregate": 4, "remark": "Fair"}
        elif percentage >= 60:
            return {"grade": "C5", "aggregate": 5, "remark": "Pass"}
        elif percentage >= 55:
            return {"grade": "C6", "aggregate": 6, "remark": "Pass"}
        elif percentage >= 45:
            return {"grade": "P7", "aggregate": 7, "remark": "Weak Pass"}
        elif percentage >= 40:
            return {"grade": "P8", "aggregate": 8, "remark": "Weak Pass"}
        else:
            return {"grade": "F9", "aggregate": 9, "remark": "Fail"}


def get_division(total_marks, class_name=None):
    """
    Division based on total marks for lower primary.
    P1 & P2 use one set of boundaries, P3 uses another.
    """
    if class_name in P3_CLASSES:
        # P3 division boundaries
        if total_marks >= 480:
            return "1"
        elif total_marks >= 400:
            return "2"
        elif total_marks >= 300:
            return "3"
        elif total_marks >= 250:
            return "4"
        else:
            return "F"
    elif class_name in LOWER_PRIMARY_ONLY:
        # P1 & P2 division boundaries
        if total_marks >= 510:
            return "1"
        elif total_marks >= 480:
            return "2"
        elif total_marks >= 450:
            return "3"
        elif total_marks >= 420:
            return "4"
        else:
            return "F"
    else:
        # Upper primary (P4–P7) — aggregate based
        if total_marks <= 12:
            return "1"
        elif total_marks <= 24:
            return "2"
        elif total_marks <= 30:
            return "3"
        elif total_marks <= 33:
            return "4"
        else:
            return "U"


def get_teacher_comment(average):
    if average >= 80:
        return ("Outstanding performance! Keep up the excellent work "
                "and continue to set a great example for your classmates.")
    elif average >= 70:
        return ("Very good work this term. You have shown great effort and "
                "understanding. Keep pushing to reach even greater heights.")
    elif average >= 60:
        return ("Good performance. You are working well. Focus on your weaker "
                "areas and you will achieve even better results next term.")
    elif average >= 50:
        return ("Fair performance. There is room for improvement. Work harder, "
                "attend all classes, and seek help where you find difficulty.")
    elif average >= 40:
        return ("You have passed but you can do much better. Please study more "
                "regularly and ask your teacher for guidance in difficult topics.")
    elif average >= 30:
        return ("You narrowly passed this term. Extra effort and regular revision "
                "are strongly advised. Talk to your teacher for extra support.")
    else:
        return ("You need to work much harder next term. Please revise your work "
                "regularly, attend all lessons, and do not hesitate to ask for help.")


def compute_student_results(mark_obj, max_mark=100):
    """
    Compute full grading details for a student's mark record.
    Automatically detects class and applies correct grading/division system.
    """
    student = mark_obj.student
    class_name = student.class_name if student else None
    is_lower = class_name in LOWER_PRIMARY_CLASSES

    if is_lower:
        subjects = {
            "Literacy A":  mark_obj.lit_a,
            "Literacy B":  mark_obj.lit_b,
            "English":     mark_obj.english,
            "Mathematics": mark_obj.math,
            "R.E.":        mark_obj.re,
            "Luganda":     mark_obj.lug,
        }
    else:
        subjects = {
            "English":        mark_obj.english,
            "Mathematics":    mark_obj.math,
            "Science":        mark_obj.science,
            "Social Studies": mark_obj.sst,
        }

    subject_details = {}
    aggregate_sum = 0
    total_marks = 0

    for subject, raw_mark in subjects.items():
        raw_mark = raw_mark if raw_mark is not None else 0
        grading = get_grade(raw_mark, max_mark, class_name=class_name)
        subject_details[subject] = {
            "mark":      raw_mark,
            "grade":     grading["grade"],
            "aggregate": grading["aggregate"],
            "remark":    grading["remark"],
        }
        aggregate_sum += grading["aggregate"]
        total_marks += raw_mark

    total        = mark_obj.total
    average      = mark_obj.average
    num_subjects = mark_obj.num_subjects

    # Use total marks for lower primary division, aggregate for upper primary
    division_input = total_marks if is_lower else aggregate_sum

    return {
        "subjects":      subject_details,
        "total":         total,
        "max_total":     num_subjects * 100,
        "average":       round(average, 1),
        "aggregate_sum": aggregate_sum,
        "division":      get_division(division_input, class_name=class_name),
        "comment":       get_teacher_comment(average),
        "is_lower":      is_lower,
    }