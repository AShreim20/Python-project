

import os
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL / SUPABASE_KEY. Make sure you have a .env "
        "file next to this script (see .env.example)."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_next_student_number(year=None):
    """
    Build the next student number for `year` (defaults to the current year),
    formatted as <year><4-digit sequence>, e.g. "20260001", "20260002", ...

    Looks at existing student numbers that start with that year and picks
    one higher than the highest sequence found, so it stays correct even if
    students were deleted in between.
    """
    year = year or datetime.now().year
    prefix = str(year)

    result = (
        supabase.table("students")
        .select("student_number")
        .like("student_number", f"{prefix}%")
        .execute()
    )

    highest_seq = 0
    for row in result.data:
        suffix = row["student_number"][len(prefix):]
        if suffix.isdigit():
            highest_seq = max(highest_seq, int(suffix))

    return f"{prefix}{highest_seq + 1:04d}"


def add_student(student_number, full_name, email, major, year_level):
    """Insert a new student. Raises an exception if student_number already exists."""
    data = {
        "student_number": student_number.strip(),
        "full_name": full_name.strip(),
        "email": email.strip() if email else None,
        "major": major.strip() if major else None,
        "year_level": int(year_level) if year_level not in (None, "") else None,
    }
    result = supabase.table("students").insert(data).execute()
    return result.data[0]


def list_students():
    """Return every student, sorted by name."""
    result = supabase.table("students").select("*").order("full_name").execute()
    return result.data


def get_student_by_number(student_number):
    """Return a single student dict, or None if not found. Case-insensitive."""
    result = (
        supabase.table("students")
        .select("*")
        .ilike("student_number", student_number.strip())
        .execute()
    )
    return result.data[0] if result.data else None


def update_student(student_id, **fields):
    """Update one or more fields on a student, e.g. update_student(id, major='CS')."""
    clean = {k: v for k, v in fields.items() if v is not None}
    result = supabase.table("students").update(clean).eq("id", student_id).execute()
    return result.data[0] if result.data else None


def delete_student(student_id):
    """Delete a student (their courses are removed automatically via ON DELETE CASCADE)."""
    supabase.table("students").delete().eq("id", student_id).execute()



def add_course(student_id, course_name, credit_hours, grade):
    data = {
        "student_id": student_id,
        "course_name": course_name.strip(),
        "credit_hours": float(credit_hours),
        "grade": grade.strip().upper(),
    }
    result = supabase.table("courses").insert(data).execute()
    return result.data[0]


def list_courses(student_id):
    result = (
        supabase.table("courses")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at")
        .execute()
    )
    return result.data


def delete_course(course_id):
    supabase.table("courses").delete().eq("id", course_id).execute()


def count_rows(table_name):
    """Return the number of rows currently in `table_name`."""
    result = supabase.table(table_name).select("id").execute()
    return len(result.data)
