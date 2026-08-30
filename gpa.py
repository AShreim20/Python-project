
GRADE_POINTS = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "D-": 0.7,
    "F": 0.0,
}

VALID_GRADES = list(GRADE_POINTS.keys())


def grade_to_points(letter_grade):
    """Convert a letter grade like 'B+' into grade points like 3.3."""
    letter_grade = letter_grade.strip().upper()
    if letter_grade not in GRADE_POINTS:
        raise ValueError(
            f"Unknown grade '{letter_grade}'. Valid grades: {', '.join(VALID_GRADES)}"
        )
    return GRADE_POINTS[letter_grade]


def calculate_gpa(courses):
    """
    courses: a list of dicts, each with at least 'credit_hours' and 'grade'
             (as returned by db.list_courses()).

    Returns (gpa, total_credit_hours). gpa is 0.0 if there are no courses.
    """
    total_points = 0.0
    total_hours = 0.0

    for course in courses:
        hours = float(course["credit_hours"])
        points = grade_to_points(course["grade"])
        total_points += hours * points
        total_hours += hours

    if total_hours == 0:
        return 0.0, 0.0

    gpa = total_points / total_hours
    return round(gpa, 2), total_hours
