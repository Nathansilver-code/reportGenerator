
def get_grade(mark, max_mark=100):
    """
    Convert a raw mark to a letter grade and aggregate point.

    Args:
        mark     : float — the raw mark obtained
        max_mark : float — maximum possible mark (default 100)

    Returns:
        dict with keys: grade (str), aggregate (int), remark (str)
    """
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


def get_division(aggregate_sum):
    """
    Determine division based on the total aggregate points from all subjects.
    Lower aggregate sum = better division.

    Uganda Primary Division boundaries (4 subjects):
        4–12   → Division 1
        13–24  → Division 2
        25–30 → Division 3
        31–33 → Division 4
        34+   → Ungraded (U)

    Args:
        aggregate_sum : int — sum of aggregate points for all subjects

    Returns:
        str — "Division 1", "Division 2", etc.
    """
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
    """
    Generate an automatic teacher comment based on the average mark.

    Args:
        average : float — mean mark across all subjects

    Returns:
        str — encouraging, age-appropriate comment
    """
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

    Args:
        mark_obj : Mark model instance
        max_mark : maximum mark per subject (default 100)

    Returns:
        dict with per-subject grades, totals, aggregate sum, division, comment
    """
    subjects = {
        "English":        mark_obj.english,
        "Mathematics":    mark_obj.math,
        "Science":        mark_obj.science,
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

    total   = mark_obj.total
    average = mark_obj.average

    return {
        "subjects":      subject_details,
        "total":         total,
        "average":       round(average, 1),
        "aggregate_sum": aggregate_sum,
        "division":      get_division(aggregate_sum),
        "comment":       get_teacher_comment(average),
    }
