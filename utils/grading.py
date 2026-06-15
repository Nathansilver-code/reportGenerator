LOWER_PRIMARY_CLASSES = ["P1", "P2", "P3"]


def get_grade(mark, max_mark=100):
    percentage = (mark / max_mark) * 100 if max_mark > 0 else 0

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
        return {"grade": "P7", "aggregate": 6, "remark": "Weak Pass"}
    elif percentage >= 35:
        return {"grade": "P8", "aggregate": 6, "remark": "Weak Pass"}
    else:
        return {"grade": "F9", "aggregate": 7, "remark": "Fail"}


def get_division(aggregate_sum, num_subjects=4):
    """
    Division boundaries scale with number of subjects.
    P1-P3 has 6 subjects; P4-P7 has 4 subjects.
    """
    if num_subjects == 6:
        # Lower primary (6 subjects, max aggregate = 42)
        if aggregate_sum <= 18:
            return "Division 1"
        elif aggregate_sum <= 36:
            return "Division 2"
        elif aggregate_sum <= 45:
            return "Division 3"
        elif aggregate_sum <= 51:
            return "Division 4"
        else:
            return "Ungraded (U)"
    else:
        # Upper primary (4 subjects, max aggregate = 28)
        if aggregate_sum <= 12:
            return "Division 1"
        elif aggregate_sum <= 24:
            return "Division 2"
        elif aggregate_sum <= 30:
            return "Division 3"
        elif aggregate_sum <= 33:
            return "Division 4"
        else:
            return "Ungraded (U)"


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
    Automatically detects lower vs upper primary from the student's class.
    """
    student = mark_obj.student
    is_lower = student and student.class_name in LOWER_PRIMARY_CLASSES

    if is_lower:
        # P1–P3: Lit A, Lit B, RE, English, Math, Luganda
        subjects = {
            "Literacy A":  mark_obj.lit_a,
            "Literacy B":  mark_obj.lit_b,
            "English":     mark_obj.english,
            "Mathematics": mark_obj.math,
            "R.E.":        mark_obj.re,
            "Luganda":     mark_obj.lug,
        }
    else:
        # P4–P7: English, Math, Science, SST
        subjects = {
            "English":       mark_obj.english,
            "Mathematics":   mark_obj.math,
            "Science":       mark_obj.science,
            "Social Studies": mark_obj.sst,
        }

    subject_details = {}
    aggregate_sum = 0

    for subject, raw_mark in subjects.items():
        grading = get_grade(raw_mark, max_mark)
        subject_details[subject] = {
            "mark":      raw_mark,
            "grade":     grading["grade"],
            "aggregate": grading["aggregate"],
            "remark":    grading["remark"],
        }
        aggregate_sum += grading["aggregate"]

    total        = mark_obj.total
    average      = mark_obj.average
    num_subjects = mark_obj.num_subjects

    return {
        "subjects":       subject_details,
        "total":          total,
        "max_total":      num_subjects * 100,
        "average":        round(average, 1),
        "aggregate_sum":  aggregate_sum,
        "division":       get_division(aggregate_sum, num_subjects),
        "comment":        get_teacher_comment(average),
        "is_lower":       is_lower,
    }