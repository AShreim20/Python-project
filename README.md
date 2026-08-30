# Smart Records System — Student Registration & GPA Manager

A desktop app (CustomTkinter UI) for registering students, editing their
info, calculating GPA from course grades, generating exportable reports,
and asking a small chatbot questions about the data. Data is stored in a
Supabase (cloud Postgres) project.

Built to match the "Smart Records System" assignment brief: GUI, database,
login/authentication, CRUD, and report generation/export.

## Project structure

```
StudentGPAManager/
├── app.py         # CustomTkinter UI (Login → tabs: Register, Manage, Reports, Chatbot) — run this
├── auth.py        # Login / create-account logic (password hashing, `users` table)
├── db.py          # All Supabase read/write calls for students + courses
├── gpa.py         # GPA math (grade → points, weighted average)
├── reports.py     # Builds the roster/GPA report, exports to PDF (reportlab) or .txt
├── chatbot.py     # Rule-based chatbot that answers questions using the data
├── requirements.txt
├── .env           # Supabase URL + key (already filled in, keep this private)
└── README.md
```

## Setup

1. Install Python 3.10+.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. The `.env` file already contains the Supabase project URL and API key
   for this project's database, so there's nothing else to configure.

## Run

```bash
python app.py
```

## How it works

- **Login screen** — log in with a username/password, or click "Create
  Account" to register a new login. Passwords are hashed (PBKDF2-HMAC-SHA256
  with a random per-user salt, via Python's `hashlib`/`secrets`) before
  being stored — the plain password is never saved. See `auth.py`.
- **Register Student tab** — fill in a student number, name, and optional
  email/major/year, and click "Register Student". This inserts a new row
  into the `students` table in Supabase.
- **Manage Students tab** — pick a student from the list on the left to
  load their info on the right. Edit any field and click "Save Changes",
  or "Delete Student" to remove them entirely. Below that you can add
  course + credit hours + letter grade entries for the selected student;
  the GPA at the top of that panel recalculates automatically from those
  courses using the standard 4.0 grade-point scale (defined in `gpa.py`).
- **Reports tab** — click "Generate Preview" to see a roster of every
  student with their computed GPA, then "Export as PDF" (via `reportlab`)
  or "Export as Text" to save it to a file you choose.
- **Chatbot tab** — a small rule-based bot (no AI API/internet call
  needed) that answers questions like:
  - `how many students`
  - `list students`
  - `gpa S1001`
  - `info S1001`
  - `highest gpa`
  - `average gpa`
  - `help`

## Database schema (Supabase)

```sql
users    (id, username, password_hash, password_salt, created_at)
students (id, student_number, full_name, email, major, year_level, created_at)
courses  (id, student_id -> students.id, course_name, credit_hours, grade, created_at)
```

GPA for a student = sum(credit_hours × grade_points) / sum(credit_hours),
computed in `gpa.py`.

## Notes for your writeup / presentation

- **Login & Authentication**: `users` table + PBKDF2 password hashing in
  `auth.py`. No plaintext passwords are ever stored or transmitted.
- **Database Integration**: Supabase (managed Postgres), 3 related tables
  (`users`, `students`, `courses` — `courses.student_id` is a foreign key
  to `students.id` with `ON DELETE CASCADE`).
  > Note: the assignment brief says "SQLite or MySQL" specifically —
  > Supabase is Postgres-based, so if the grading is strict about that
  > wording, mention that you substituted a managed cloud Postgres
  > database for the same relational-database requirement, and be ready
  > to explain the trade-off (extra reliability/features vs. not being
  > the literally-named engine). This was a deliberate choice made for
  > this project.
- **CRUD Operations**: full create/read/update/delete on students and
  courses (`db.py`), plus create/read on user accounts (`auth.py`).
  There is currently no "delete/edit account" UI — everything else is
  editable.
- **Report Generation**: `reports.py` builds a roster+GPA summary and
  exports it as PDF (`reportlab`, a table with headers/styling) or plain
  text (`.txt`, via file I/O) — both explicitly suggested in the brief.
- **GUI**: CustomTkinter (a themed wrapper around Tkinter) for the modern
  look; a couple of internal widgets (the sortable tables/treeviews) use
  plain `ttk.Treeview` since CustomTkinter doesn't provide its own table
  widget — this is normal practice and they render fine inside CTk frames.
- **Security caveat worth mentioning**: the Supabase tables use permissive
  Row Level Security policies (any request with the API key can read/write)
  because building a full server-side auth/authorization layer was out of
  scope for this project — the app's own login screen gates entry into the
  UI, but doesn't restrict direct API access. Worth a sentence in a
  "limitations" section of your writeup.
- The chatbot is intentionally rule-based (keyword matching in
  `chatbot.py`) rather than calling an external AI API, so the whole app
  runs without an internet-dependent AI service, an API key for that
  service, or any per-message cost — only the Supabase database calls
  need internet.
