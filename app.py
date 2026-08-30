
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import customtkinter as ctk
from PIL import Image

import auth
import db
import gpa
import chatbot
import reports

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Background photo shown on the login screen.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_BACKGROUND_PATH = os.path.join(_APP_DIR, "AAUP.png")

MAJORS = [
    "Computer Science",
    "Software Engineering",
    "Information Technology",
    "Business Administration",
    "Accounting",
    "Economics",
    "Civil Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Architecture",
    "Law",
    "Medicine",
    "Pharmacy",
    "Nursing",
    "Psychology",
    "English Literature",
    "Graphic Design",
    "Mathematics",
    "Physics",
    "Other",
]


class CreateAccountDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create Account")
        self.resizable(False, False)
        self.grab_set()  # modal

        ctk.CTkLabel(self, text="Create a New Account", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(20, 15)
        )

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        ctk.CTkLabel(self, text="Username").pack(anchor="w", padx=30)
        ctk.CTkEntry(self, textvariable=self.username_var, width=260).pack(padx=30, pady=(0, 10))

        ctk.CTkLabel(self, text="Password").pack(anchor="w", padx=30)
        ctk.CTkEntry(self, textvariable=self.password_var, show="*", width=260).pack(
            padx=30, pady=(0, 10)
        )

        ctk.CTkLabel(self, text="Confirm Password").pack(anchor="w", padx=30)
        ctk.CTkEntry(self, textvariable=self.confirm_var, show="*", width=260).pack(
            padx=30, pady=(0, 15)
        )

        ctk.CTkButton(self, text="Create Account", command=self.submit).pack(pady=(5, 20))

        self.update_idletasks()

    def submit(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if password != confirm:
            messagebox.showerror("Passwords don't match", "Password and confirmation must match.")
            return

        try:
            auth.create_account(username, password)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        except Exception as exc:
            # Most likely a duplicate username (unique constraint violation).
            messagebox.showerror("Could not create account", f"That username may already be taken.\n\n{exc}")
            return

        messagebox.showinfo("Account created", "Account created! You can now log in.")
        self.destroy()


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success

        # Campus photo background. Loaded once here; resized to fill the
        # window every time it's resized (see _resize_background).
        self._bg_source_image = None
        self._bg_ctk_image = None
        if os.path.exists(LOGIN_BACKGROUND_PATH):
            self._bg_source_image = Image.open(LOGIN_BACKGROUND_PATH)
            self.bg_label = ctk.CTkLabel(self, text="")
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.bind("<Configure>", self._resize_background)

        # Card sits on top of the background (created after it, so it's
        # higher in the stacking order) with a solid color for readability.
        card = ctk.CTkFrame(self, width=360, height=320, fg_color=("gray90", "gray13"))
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card, text="Smart Records System", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 5))
        ctk.CTkLabel(card, text="Student Registration & GPA Manager", text_color="gray").pack(
            pady=(0, 20)
        )

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        ctk.CTkEntry(card, textvariable=self.username_var, placeholder_text="Username", width=260).pack(
            pady=6
        )
        password_entry = ctk.CTkEntry(
            card, textvariable=self.password_var, placeholder_text="Password", show="*", width=260
        )
        password_entry.pack(pady=6)
        password_entry.bind("<Return>", lambda _e: self.login())

        ctk.CTkButton(card, text="Log In", command=self.login, width=260).pack(pady=(16, 6))
        ctk.CTkButton(
            card,
            text="Create Account",
            command=self.open_create_account,
            width=260,
            fg_color="transparent",
            border_width=1,
        ).pack(pady=6)

        self.status_label = ctk.CTkLabel(card, text="", text_color="#e05555")
        self.status_label.pack(pady=(10, 20))

    def _resize_background(self, event):
        # Bound only on `self`, so this only fires for this frame's own
        # geometry changes -- no need to check event.widget (CustomTkinter's
        # internal widget wrapping means it doesn't reliably `is self` even
        # for genuine self-resize events).
        if self._bg_source_image is None:
            return
        width, height = max(event.width, 1), max(event.height, 1)

        # Scale to cover the whole window (like CSS background-size: cover),
        # then center-crop the overflow so the photo isn't distorted.
        src_w, src_h = self._bg_source_image.size
        scale = max(width / src_w, height / src_h)
        resized = self._bg_source_image.resize((int(src_w * scale), int(src_h * scale)))
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))

        self._bg_ctk_image = ctk.CTkImage(light_image=cropped, dark_image=cropped, size=(width, height))
        self.bg_label.configure(image=self._bg_ctk_image)

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.status_label.configure(text="Enter both a username and password.")
            return

        try:
            ok = auth.verify_login(username, password)
        except Exception as exc:
            self.status_label.configure(text=f"Login error: {exc}")
            return

        if not ok:
            self.status_label.configure(text="Incorrect username or password.")
            return

        self.status_label.configure(text="")
        self.on_login_success(username)

    def open_create_account(self):
        CreateAccountDialog(self)


MAJOR_PLACEHOLDER = "-- Select a major --"


class RegisterTab(ctk.CTkFrame):
    def __init__(self, parent, on_student_added):
        super().__init__(parent, fg_color="transparent")
        self.on_student_added = on_student_added

        ctk.CTkLabel(self, text="Register a New Student", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 15)
        )

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(anchor="w", padx=20)

        self.vars = {
            "student_number": tk.StringVar(),
            "full_name": tk.StringVar(),
            "email": tk.StringVar(),
            "major": tk.StringVar(value=MAJOR_PLACEHOLDER),
            "year_level": tk.StringVar(),
        }

        ctk.CTkLabel(form, text="Student Number", width=140, anchor="w").grid(
            row=0, column=0, sticky="w", pady=6
        )
        ctk.CTkEntry(
            form, textvariable=self.vars["student_number"], width=260, state="disabled"
        ).grid(row=0, column=1, sticky="w", pady=6, padx=(10, 0))
        ctk.CTkLabel(form, text="(auto-generated)", text_color="gray", anchor="w").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        self._generate_student_number()

        text_fields = [
            ("Full Name *", "full_name"),
            ("Email", "email"),
            ("Year Level (1-6)", "year_level"),
        ]
        for i, (label, key) in enumerate(text_fields, start=1):
            ctk.CTkLabel(form, text=label, width=140, anchor="w").grid(row=i, column=0, sticky="w", pady=6)
            ctk.CTkEntry(form, textvariable=self.vars[key], width=260).grid(
                row=i, column=1, sticky="w", pady=6, padx=(10, 0)
            )

        major_row = len(text_fields) + 1
        ctk.CTkLabel(form, text="Major", width=140, anchor="w").grid(row=major_row, column=0, sticky="w", pady=6)
        ctk.CTkOptionMenu(
            form, variable=self.vars["major"], values=[MAJOR_PLACEHOLDER] + MAJORS, width=260
        ).grid(row=major_row, column=1, sticky="w", pady=6, padx=(10, 0))

        ctk.CTkButton(self, text="Register Student", command=self.register).pack(anchor="w", padx=20, pady=15)

        self.status = ctk.CTkLabel(self, text="", text_color="#3ba55d")
        self.status.pack(anchor="w", padx=20)

    def _generate_student_number(self):
        try:
            self.vars["student_number"].set(db.generate_next_student_number())
        except Exception as exc:
            self.vars["student_number"].set("")
            messagebox.showerror("Could not generate student number", str(exc))

    def register(self):
        number = self.vars["student_number"].get().strip()
        name = self.vars["full_name"].get().strip()

        if not number:
            messagebox.showerror("No student number", "Couldn't auto-generate a student number. Try again.")
            return
        if not name:
            messagebox.showerror("Missing info", "Full Name is required.")
            return

        year_text = self.vars["year_level"].get().strip()
        if year_text and not year_text.isdigit():
            messagebox.showerror("Invalid year", "Year Level must be a whole number.")
            return

        major = self.vars["major"].get().strip()
        if major == MAJOR_PLACEHOLDER:
            major = ""

        try:
            db.add_student(
                number,
                name,
                self.vars["email"].get(),
                major,
                year_text or None,
            )
        except Exception as exc:
            messagebox.showerror("Could not register student", str(exc))
            return

        self.status.configure(text=f"Registered {name} ({number}) successfully.")
        self.vars["full_name"].set("")
        self.vars["email"].set("")
        self.vars["year_level"].set("")
        self.vars["major"].set(MAJOR_PLACEHOLDER)
        self._generate_student_number()
        self.on_student_added()


# ---------------------------------------------------------------------------
# Manage Students tab (view / edit / GPA)
# ---------------------------------------------------------------------------

class ManageTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.selected_student = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

       
        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, sticky="nsw", padx=(15, 10), pady=15)

        ctk.CTkLabel(left, text="Students", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )

        self.student_list = ttk.Treeview(
            left, columns=("number", "name"), show="headings", height=20, selectmode="browse"
        )
        self.student_list.heading("number", text="ID")
        self.student_list.heading("name", text="Name")
        self.student_list.column("number", width=90)
        self.student_list.column("name", width=160)
        self.student_list.pack(fill="y", expand=True, padx=10)
        self.student_list.bind("<<TreeviewSelect>>", self._on_select_student)

        ctk.CTkButton(left, text="Refresh List", command=self.refresh_students).pack(
            fill="x", padx=10, pady=10
        )

        right = ctk.CTkScrollableFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        right.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Student Details", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

        self.detail_vars = {
            "full_name": tk.StringVar(),
            "email": tk.StringVar(),
            "major": tk.StringVar(value=MAJOR_PLACEHOLDER),
            "year_level": tk.StringVar(),
        }

        detail_fields = [
            ("Full Name", "full_name"),
            ("Email", "email"),
            ("Year Level", "year_level"),
        ]
        for i, (label, key) in enumerate(detail_fields, start=1):
            ctk.CTkLabel(right, text=label, width=110, anchor="w").grid(row=i, column=0, sticky="w", pady=4)
            ctk.CTkEntry(right, textvariable=self.detail_vars[key], width=250).grid(
                row=i, column=1, sticky="w", pady=4, padx=(10, 0)
            )

        major_row = len(detail_fields) + 1
        ctk.CTkLabel(right, text="Major", width=110, anchor="w").grid(row=major_row, column=0, sticky="w", pady=4)
        ctk.CTkOptionMenu(
            right, variable=self.detail_vars["major"], values=[MAJOR_PLACEHOLDER] + MAJORS, width=250
        ).grid(row=major_row, column=1, sticky="w", pady=4, padx=(10, 0))

        btn_row = major_row + 1
        ctk.CTkButton(right, text="Save Changes", command=self.save_changes).grid(
            row=btn_row, column=0, sticky="w", pady=10
        )
        ctk.CTkButton(
            right, text="Delete Student", fg_color="#b23b3b", hover_color="#8f2f2f",
            command=self.delete_student,
        ).grid(row=btn_row, column=1, sticky="w", pady=10)

        ttk.Separator(right, orient="horizontal").grid(
            row=btn_row + 1, column=0, columnspan=2, sticky="ew", pady=10
        )

        self.gpa_label = ctk.CTkLabel(right, text="GPA: —", font=ctk.CTkFont(size=15, weight="bold"))
        self.gpa_label.grid(row=btn_row + 2, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.course_list = ttk.Treeview(
            right, columns=("course", "hours", "grade"), show="headings", height=6
        )
        self.course_list.heading("course", text="Course")
        self.course_list.heading("hours", text="Credit Hours")
        self.course_list.heading("grade", text="Grade")
        self.course_list.column("hours", width=90, anchor="center")
        self.course_list.column("grade", width=70, anchor="center")
        self.course_list.grid(row=btn_row + 3, column=0, columnspan=2, sticky="nsew")

        ctk.CTkButton(
            right, text="Delete Selected Course", fg_color="#b23b3b", hover_color="#8f2f2f",
            command=self.delete_course,
        ).grid(row=btn_row + 4, column=0, columnspan=2, sticky="w", pady=(6, 10))

        add_course_frame = ctk.CTkFrame(right)
        add_course_frame.grid(row=btn_row + 5, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.new_course_name = tk.StringVar()
        self.new_course_hours = tk.StringVar()
        self.new_course_grade = tk.StringVar(value=gpa.VALID_GRADES[0])

        ctk.CTkLabel(add_course_frame, text="Course").grid(row=0, column=0, padx=6, pady=8)
        ctk.CTkEntry(add_course_frame, textvariable=self.new_course_name, width=120).grid(
            row=0, column=1, padx=6
        )
        ctk.CTkLabel(add_course_frame, text="Credit Hrs").grid(row=0, column=2, padx=6)
        ctk.CTkEntry(add_course_frame, textvariable=self.new_course_hours, width=60).grid(
            row=0, column=3, padx=6
        )
        ctk.CTkLabel(add_course_frame, text="Grade").grid(row=0, column=4, padx=6)
        ctk.CTkOptionMenu(
            add_course_frame, variable=self.new_course_grade, values=gpa.VALID_GRADES, width=70
        ).grid(row=0, column=5, padx=6)
        ctk.CTkButton(add_course_frame, text="Add", command=self.add_course, width=70).grid(
            row=0, column=6, padx=(12, 6)
        )

        self.refresh_students()

    def refresh_students(self):
        for row in self.student_list.get_children():
            self.student_list.delete(row)
        self._students_cache = db.list_students()
        for student in self._students_cache:
            self.student_list.insert(
                "", "end", iid=student["id"], values=(student["student_number"], student["full_name"])
            )

    def _on_select_student(self, _event):
        selection = self.student_list.selection()
        if not selection:
            return
        student_id = selection[0]
        student = next((s for s in self._students_cache if s["id"] == student_id), None)
        if not student:
            return
        self.selected_student = student
        self.detail_vars["full_name"].set(student.get("full_name") or "")
        self.detail_vars["email"].set(student.get("email") or "")
        self.detail_vars["major"].set(student.get("major") or MAJOR_PLACEHOLDER)
        self.detail_vars["year_level"].set(
            str(student["year_level"]) if student.get("year_level") is not None else ""
        )
        self.refresh_courses()

    def refresh_courses(self):
        for row in self.course_list.get_children():
            self.course_list.delete(row)
        if not self.selected_student:
            self.gpa_label.configure(text="GPA: —")
            return
        courses = db.list_courses(self.selected_student["id"])
        for course in courses:
            self.course_list.insert(
                "",
                "end",
                iid=course["id"],
                values=(course["course_name"], course["credit_hours"], course["grade"]),
            )
        value, hours = gpa.calculate_gpa(courses)
        if courses:
            self.gpa_label.configure(text=f"GPA: {value:.2f}  ({hours:g} credit hours)")
        else:
            self.gpa_label.configure(text="GPA: — (no courses yet)")

    def save_changes(self):
        if not self.selected_student:
            messagebox.showinfo("No student selected", "Select a student from the list first.")
            return

        year_text = self.detail_vars["year_level"].get().strip()
        if year_text and not year_text.isdigit():
            messagebox.showerror("Invalid year", "Year Level must be a whole number.")
            return

        major = self.detail_vars["major"].get().strip()
        if major == MAJOR_PLACEHOLDER:
            major = ""

        try:
            db.update_student(
                self.selected_student["id"],
                full_name=self.detail_vars["full_name"].get().strip(),
                email=self.detail_vars["email"].get().strip(),
                major=major,
                year_level=int(year_text) if year_text else None,
            )
        except Exception as exc:
            messagebox.showerror("Could not save changes", str(exc))
            return

        messagebox.showinfo("Saved", "Student info updated.")
        self.refresh_students()

    def delete_student(self):
        if not self.selected_student:
            messagebox.showinfo("No student selected", "Select a student from the list first.")
            return
        name = self.selected_student["full_name"]
        if not messagebox.askyesno("Confirm delete", f"Delete {name} and all their course records?"):
            return
        db.delete_student(self.selected_student["id"])
        self.selected_student = None
        for key, var in self.detail_vars.items():
            var.set(MAJOR_PLACEHOLDER if key == "major" else "")
        self.refresh_students()
        self.refresh_courses()

    def add_course(self):
        if not self.selected_student:
            messagebox.showinfo("No student selected", "Select a student from the list first.")
            return

        name = self.new_course_name.get().strip()
        hours = self.new_course_hours.get().strip()
        grade = self.new_course_grade.get().strip()

        if not name or not hours or not grade:
            messagebox.showerror("Missing info", "Course, Credit Hours, and Grade are all required.")
            return

        try:
            hours_value = float(hours)
        except ValueError:
            messagebox.showerror("Invalid hours", "Credit Hours must be a number.")
            return

        try:
            db.add_course(self.selected_student["id"], name, hours_value, grade)
        except Exception as exc:
            messagebox.showerror("Could not add course", str(exc))
            return

        self.new_course_name.set("")
        self.new_course_hours.set("")
        self.refresh_courses()

    def delete_course(self):
        selection = self.course_list.selection()
        if not selection:
            messagebox.showinfo("No course selected", "Select a course from the table first.")
            return
        db.delete_course(selection[0])
        self.refresh_courses()


class ReportsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._rows = []

        ctk.CTkLabel(self, text="Roster & GPA Report", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(button_bar, text="Generate Preview", command=self.generate_preview).grid(
            row=0, column=0, padx=(0, 10)
        )
        ctk.CTkButton(button_bar, text="Export as PDF", command=self.export_pdf).grid(
            row=0, column=1, padx=(0, 10)
        )
        ctk.CTkButton(button_bar, text="Export as Text", command=self.export_text).grid(
            row=0, column=2
        )

        self.preview = ctk.CTkTextbox(self, width=740, height=380, font=("Consolas", 12))
        self.preview.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.preview.insert("1.0", "Click \"Generate Preview\" to build the report.")
        self.preview.configure(state="disabled")

    def generate_preview(self):
        self._rows = reports.build_report_rows()

        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")

        if not self._rows:
            self.preview.insert("1.0", "No students registered yet.")
        else:
            header = f"{'ID':<10}{'Name':<22}{'Major':<18}{'Yr':<5}{'GPA':<6}{'Hrs':<5}\n"
            self.preview.insert("end", header)
            self.preview.insert("end", "-" * 66 + "\n")
            for row in self._rows:
                self.preview.insert(
                    "end",
                    f"{row['student_number']:<10}{row['full_name']:<22}{row['major']:<18}"
                    f"{str(row['year_level']):<5}{row['gpa']:<6}{row['credit_hours']:<5}\n",
                )
            self.preview.insert("end", "-" * 66 + "\n")
            self.preview.insert("end", f"Total students: {len(self._rows)}")

        self.preview.configure(state="disabled")

    def export_pdf(self):
        if not self._rows:
            self.generate_preview()
        if not self._rows:
            messagebox.showinfo("Nothing to export", "No students registered yet.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")], initialfile="student_report.pdf"
        )
        if not file_path:
            return
        try:
            reports.export_pdf(self._rows, file_path)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Exported", f"Report saved to:\n{file_path}")

    def export_text(self):
        if not self._rows:
            self.generate_preview()
        if not self._rows:
            messagebox.showinfo("Nothing to export", "No students registered yet.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text file", "*.txt")], initialfile="student_report.txt"
        )
        if not file_path:
            return
        try:
            reports.export_text(self._rows, file_path)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Exported", f"Report saved to:\n{file_path}")


# ---------------------------------------------------------------------------
# Chatbot tab
# ---------------------------------------------------------------------------

class ChatbotTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.output = ctk.CTkTextbox(self, width=740, height=420)
        self.output.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        self.output.configure(state="disabled")

        entry_row = ctk.CTkFrame(self, fg_color="transparent")
        entry_row.pack(fill="x", padx=20, pady=(0, 20))
        entry_row.grid_columnconfigure(0, weight=1)

        self.entry_var = tk.StringVar()
        entry = ctk.CTkEntry(entry_row, textvariable=self.entry_var, placeholder_text="Ask me something...")
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        entry.bind("<Return>", lambda _e: self.send())

        ctk.CTkButton(entry_row, text="Send", command=self.send, width=80).grid(row=0, column=1)

        self._append("Bot", chatbot.get_response("help"))

    def send(self):
        text = self.entry_var.get().strip()
        if not text:
            return
        self._append("You", text)
        self.entry_var.set("")
        try:
            reply = chatbot.get_response(text)
        except Exception as exc:
            reply = f"Something went wrong answering that: {exc}"
        self._append("Bot", reply)

    def _append(self, speaker, message):
        self.output.configure(state="normal")
        self.output.insert("end", f"{speaker}: {message}\n\n")
        self.output.configure(state="disabled")
        self.output.see("end")


class MainAppFrame(ctk.CTkFrame):
    def __init__(self, parent, username, on_logout):
        super().__init__(parent, fg_color="transparent")

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(15, 0))

        ctk.CTkLabel(
            top_bar, text=f"Logged in as: {username}", font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(side="left")
        ctk.CTkButton(top_bar, text="Log Out", width=90, command=on_logout).pack(side="right")

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=15, pady=15)

        tabview.add("Register Student")
        tabview.add("Manage Students")
        tabview.add("Reports")
        tabview.add("Chatbot")

        manage_tab = ManageTab(tabview.tab("Manage Students"))
        manage_tab.pack(fill="both", expand=True)

        register_tab = RegisterTab(tabview.tab("Register Student"), on_student_added=manage_tab.refresh_students)
        register_tab.pack(fill="both", expand=True)

        reports_tab = ReportsTab(tabview.tab("Reports"))
        reports_tab.pack(fill="both", expand=True)

        chatbot_tab = ChatbotTab(tabview.tab("Chatbot"))
        chatbot_tab.pack(fill="both", expand=True)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Records System - Student Registration & GPA Manager")
        self.geometry("900x650")
        self.minsize(760, 560)

        self.current_view = None
        self.show_login()

    def _clear(self):
        if self.current_view is not None:
            self.current_view.destroy()

    def show_login(self):
        self._clear()
        self.current_view = LoginFrame(self, on_login_success=self.show_main)
        self.current_view.pack(fill="both", expand=True)

    def show_main(self, username):
        self._clear()
        self.current_view = MainAppFrame(self, username, on_logout=self.show_login)
        self.current_view.pack(fill="both", expand=True)


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as exc:
        import tkinter.messagebox as mb
        mb.showerror("Startup error", str(exc))
        raise
