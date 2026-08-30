
import re

import db
import gpa

HELP_TEXT = (
    "Here's what I can help with:\n"
    "  • \"how many students\" - total number of registered students\n"
    "  • \"how many courses\" / \"how many users\" - row counts for other tables\n"
    "  • \"list students\" - show every student's name and ID\n"
    "  • \"gpa <student number>\" - calculate a student's GPA\n"
    "  • \"info <student number>\" - show a student's stored info\n"
    "  • \"highest gpa\" - which student currently has the best GPA\n"
    "  • \"average gpa\" - the average GPA across all students\n"
    "  • \"how many columns in the courses table\" - schema questions about\n"
    "    the students / courses / users tables\n"
    "  • \"how many tables\" - list the database tables\n"
    "  • \"help\" - show this message again"
)

# Static description of the Supabase schema (see the migrations in the
# README) -- used to answer structural "how is the database built"
# questions without needing to query Postgres' own metadata tables.
SCHEMA = {
    "students": ["id", "student_number", "full_name", "email", "major", "year_level", "created_at"],
    "courses": ["id", "student_id", "course_name", "credit_hours", "grade", "created_at"],
    "users": ["id", "username", "password_hash", "password_salt", "created_at"],
}

# Words in a user's message that refer to each table (singular and plural,
# plus a couple of common synonyms).
_TABLE_ALIASES = {
    "students": "students",
    "student": "students",
    "courses": "courses",
    "course": "courses",
    "users": "users",
    "user": "users",
    "accounts": "users",
    "account": "users",
}

_ROW_LABELS = {
    "students": ("student", "students"),
    "courses": ("course record", "course records"),
    "users": ("user account", "user accounts"),
}


def _find_table(text):
    """Return the canonical table name ('students'/'courses'/'users') mentioned
    in `text`, or None if no table name appears."""
    for alias, table in _TABLE_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            return table
    return None


def _pluralize(count, singular, plural):
    return singular if count == 1 else plural


# Matches things like "S1001", "2023001", "id-42" typed anywhere in the message.
_ID_PATTERN = re.compile(r"[A-Za-z0-9\-]{3,}")


def _extract_student_number(original_text, keyword):
    """Pull whatever looks like a student number out of a message like 'gpa S1001'.

    `keyword` is matched case-insensitively, but the returned number keeps its
    original casing so it matches what's actually stored (e.g. "S1001").
    """
    lower_text = original_text.lower()
    keyword_pos = lower_text.find(keyword)
    if keyword_pos == -1:
        return None
    after_keyword = original_text[keyword_pos + len(keyword):]
    match = _ID_PATTERN.search(after_keyword)
    return match.group(0) if match else None


def _student_gpa_line(student):
    courses = db.list_courses(student["id"])
    if not courses:
        return f"{student['full_name']} ({student['student_number']}) has no courses recorded yet."
    value, hours = gpa.calculate_gpa(courses)
    return (
        f"{student['full_name']} ({student['student_number']}) has a GPA of "
        f"{value:.2f} across {hours:g} credit hours."
    )


def get_response(user_text):
    original = user_text.strip()
    text = original.lower()

    if not text:
        return "Type a question, or say \"help\" to see what I can do."

    if text in ("hi", "hello", "hey"):
        return "Hi! I'm the student records assistant. Type \"help\" to see what I can do."

    if "help" in text:
        return HELP_TEXT

    if "how many student" in text:
        count = len(db.list_students())
        label = _pluralize(count, "registered student", "registered students")
        return f"There are currently {count} {label}."

    if "list student" in text:
        students = db.list_students()
        if not students:
            return "No students are registered yet."
        lines = [f"  • {s['full_name']} ({s['student_number']})" for s in students]
        return "Registered students:\n" + "\n".join(lines)

    if "how many table" in text:
        names = ", ".join(SCHEMA.keys())
        return f"The database has {len(SCHEMA)} tables: {names}."

    if "column" in text:
        table = _find_table(text)
        if not table:
            return (
                "Which table do you mean? Try \"how many columns in the "
                "students table\", \"courses table\", or \"users table\"."
            )
        columns = SCHEMA[table]
        return f"The {table} table has {len(columns)} columns: {', '.join(columns)}."

    if "how many" in text:
        table = _find_table(text)
        # "how many students" is already handled above with a live query;
        # this only fires for the other tables (courses / users).
        if table and table != "students":
            count = db.count_rows(table)
            singular, plural = _ROW_LABELS[table]
            return f"There are currently {count} {_pluralize(count, singular, plural)}."

    if "highest gpa" in text or "best gpa" in text or "top student" in text:
        students = db.list_students()
        if not students:
            return "No students are registered yet."
        best_student, best_value = None, -1.0
        for s in students:
            courses = db.list_courses(s["id"])
            if not courses:
                continue
            value, _ = gpa.calculate_gpa(courses)
            if value > best_value:
                best_student, best_value = s, value
        if best_student is None:
            return "No student has any courses recorded yet, so I can't rank GPAs."
        return f"{best_student['full_name']} ({best_student['student_number']}) has the highest GPA: {best_value:.2f}."

    if "average gpa" in text:
        students = db.list_students()
        values = []
        for s in students:
            courses = db.list_courses(s["id"])
            if courses:
                value, _ = gpa.calculate_gpa(courses)
                values.append(value)
        if not values:
            return "No GPA data is available yet."
        return f"The average GPA across {len(values)} student(s) is {sum(values) / len(values):.2f}."

    if "gpa" in text:
        number = _extract_student_number(original, "gpa")
        if not number:
            return "Tell me a student number too, e.g. \"gpa S1001\"."
        student = db.get_student_by_number(number)
        if not student:
            return f"I couldn't find a student with number '{number}'."
        return _student_gpa_line(student)

    if "info" in text or "about" in text or "show" in text:
        keyword = "info" if "info" in text else ("about" if "about" in text else "show")
        number = _extract_student_number(original, keyword)
        if not number:
            return "Tell me a student number too, e.g. \"info S1001\"."
        student = db.get_student_by_number(number)
        if not student:
            return f"I couldn't find a student with number '{number}'."
        return (
            f"{student['full_name']} ({student['student_number']})\n"
            f"  Email: {student.get('email') or '—'}\n"
            f"  Major: {student.get('major') or '—'}\n"
            f"  Year: {student.get('year_level') or '—'}"
        )

    return (
        "Sorry, I didn't understand that. Type \"help\" to see what I can answer."
    )
