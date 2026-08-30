from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

import db
import gpa


def build_report_rows():
    """
    Returns a list of dicts, one per student, each with:
    student_number, full_name, major, year_level, gpa, credit_hours
    """
    rows = []
    for student in db.list_students():
        courses = db.list_courses(student["id"])
        gpa_value, hours = gpa.calculate_gpa(courses)
        rows.append(
            {
                "student_number": student["student_number"],
                "full_name": student["full_name"],
                "major": student.get("major") or "-",
                "year_level": student.get("year_level") or "-",
                "gpa": gpa_value,
                "credit_hours": hours,
            }
        )
    return rows


def export_text(rows, file_path):
    """Write the report as a simple, readable plain-text table."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "Student Roster & GPA Report",
        f"Generated: {generated_at}",
        "-" * 70,
        f"{'ID':<10}{'Name':<22}{'Major':<18}{'Yr':<5}{'GPA':<6}{'Hrs':<5}",
        "-" * 70,
    ]
    for row in rows:
        lines.append(
            f"{row['student_number']:<10}{row['full_name']:<22}{row['major']:<18}"
            f"{str(row['year_level']):<5}{row['gpa']:<6}{row['credit_hours']:<5}"
        )
    lines.append("-" * 70)
    lines.append(f"Total students: {len(rows)}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_pdf(rows, file_path):
    """Write the report as a formatted PDF table using reportlab."""
    doc = SimpleDocTemplate(file_path, pagesize=letter, title="Student Roster & GPA Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Student Roster &amp; GPA Report", styles["Title"]))
    story.append(
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"])
    )
    story.append(Spacer(1, 16))

    table_data = [["ID", "Name", "Major", "Year", "GPA", "Credit Hrs"]]
    for row in rows:
        table_data.append(
            [
                row["student_number"],
                row["full_name"],
                row["major"],
                str(row["year_level"]),
                f"{row['gpa']:.2f}",
                str(row["credit_hours"]),
            ]
        )

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (3, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total students: {len(rows)}", styles["Normal"]))

    doc.build(story)
