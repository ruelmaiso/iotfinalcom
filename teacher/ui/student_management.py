import customtkinter as ctk
from tkinter import messagebox


class StudentManagementPanel:
    def __init__(self, parent, auth_db, theme_palette_provider, font_family: str = "Arial") -> None:
        self.parent = parent
        self.auth_db = auth_db
        self.theme_palette_provider = theme_palette_provider
        self.font_family = font_family
        self.window = None
        self.rows_frame = None

    def open(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
        colors = self.theme_palette_provider()
        # UI POLISH ONLY
        primary_button = {"fg_color": "#2E8B57", "hover_color": "#277A4C", "text_color": "#FFFFFF", "height": 34}
        secondary_button = {"fg_color": "#DDE5DE", "hover_color": "#CFD8D0", "text_color": "#1F1F1F", "height": 34}
        danger_button = {"fg_color": "#B22222", "hover_color": "#8F1B1B", "text_color": "#FFFFFF", "height": 34}
        self.window = ctk.CTkToplevel(self.parent)
        self.window.transient(self.parent)
        self.window.lift()
        self.window.focus_force()
        self.window.grab_set()
        self.window.title("Student Management")
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        width = min(760, max(320, screen_w - 80))
        height = min(620, max(300, screen_h - 80))
        self.window.geometry(f"{width}x{height}")
        self.window.configure(fg_color=colors["card_bg"])

        toolbar = ctk.CTkFrame(self.window, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkButton(toolbar, text="Add Student", command=self._add_student_dialog, width=132, **primary_button).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Reset Password", command=self._reset_password_dialog, width=142, **secondary_button).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Delete Student", command=self._delete_student_dialog, width=138, **danger_button).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Refresh List", command=self._render_rows, width=116, **secondary_button).pack(side="right")

        # UI POLISH ONLY
        ctk.CTkLabel(
            self.window,
            text="Manage student records and account access from one place.",
            font=(self.font_family, 12),
            text_color=colors["text_secondary"],
        ).pack(fill="x", padx=18, pady=(0, 8))

        head = ctk.CTkFrame(self.window, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(0, 6))
        ctk.CTkLabel(head, text="Student Number", font=(self.font_family, 12, "bold")).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(head, text="Full Name", font=(self.font_family, 12, "bold")).grid(row=0, column=1, sticky="w", padx=6)
        ctk.CTkLabel(head, text="Year / Section", font=(self.font_family, 12, "bold")).grid(row=0, column=2, sticky="w", padx=6)
        head.grid_columnconfigure(0, weight=1)
        head.grid_columnconfigure(1, weight=2)
        head.grid_columnconfigure(2, weight=1)

        self.rows_frame = ctk.CTkScrollableFrame(self.window, fg_color=colors["card_bg"])
        self.rows_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._render_rows()

    def _render_rows(self) -> None:
        if self.rows_frame is None or not self.rows_frame.winfo_exists():
            return
        for child in self.rows_frame.winfo_children():
            child.destroy()

        colors = self.theme_palette_provider()
        rows = self.auth_db.list_students()
        if not rows:
            ctk.CTkLabel(
                self.rows_frame,
                text="No students found. Add a student to get started.",
                font=(self.font_family, 12),
                text_color=colors["text_secondary"],
            ).pack(anchor="w", padx=12, pady=12)
            return

        for row in rows:
            line = ctk.CTkFrame(self.rows_frame, fg_color=colors["root_bg"], corner_radius=8, border_width=1, border_color=colors["border"])
            line.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(line, text=str(row.get("student_number", "")), font=(self.font_family, 12), text_color=colors["text_primary"]).grid(row=0, column=0, sticky="w", padx=10, pady=8)
            ctk.CTkLabel(line, text=str(row.get("full_name", "")), font=(self.font_family, 12), text_color=colors["text_primary"]).grid(row=0, column=1, sticky="w", padx=10, pady=8)
            ctk.CTkLabel(line, text=str(row.get("year_section", "")), font=(self.font_family, 12), text_color=colors["text_primary"]).grid(row=0, column=2, sticky="w", padx=10, pady=8)
            line.grid_columnconfigure(0, weight=1)
            line.grid_columnconfigure(1, weight=2)
            line.grid_columnconfigure(2, weight=1)

    def _add_student_dialog(self) -> None:
        colors = self.theme_palette_provider()
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Add Student")
        win.geometry("420x320")
        win.configure(fg_color=colors["card_bg"])

        # UI POLISH ONLY
        ctk.CTkLabel(
            win,
            text="Create a student account and set the initial login details.",
            font=(self.font_family, 12),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        entries = {}
        for label, key, show, placeholder in [
            ("Full Name", "full_name", None, "e.g. Juan Dela Cruz"),
            ("Year / Section", "year_section", None, "e.g. BSIT 2A"),
            ("Student Number", "student_number", None, "00-00000"),
            ("Password", "password", "*", "Enter temporary password"),
        ]:
            ctk.CTkLabel(win, text=label, text_color=colors["text_primary"]).pack(anchor="w", padx=16, pady=(10, 4))
            e = ctk.CTkEntry(win, show=show, placeholder_text=placeholder)
            e.pack(fill="x", padx=16)
            entries[key] = e

        feedback_label = ctk.CTkLabel(
            win,
            text="Use the student number format 00-00000.",
            font=(self.font_family, 11),
            text_color=colors["text_secondary"],
        )
        feedback_label.pack(anchor="w", padx=16, pady=(8, 0))

        def submit() -> None:
            payload = {k: v.get().strip() for k, v in entries.items()}
            ok, reason = self.auth_db.add_student_admin(
                payload["full_name"],
                payload["year_section"],
                payload["student_number"],
                payload["password"],
            )
            if not ok:
                feedback_label.configure(text=f"Failed: {reason}", text_color="#B22222")
                messagebox.showerror("Add Student", f"Failed: {reason}")
                return
            win.destroy()
            self._render_rows()

        ctk.CTkButton(
            win,
            text="Create Student",
            command=submit,
            width=150,
            height=34,
            fg_color="#2E8B57",
            hover_color="#277A4C",
            text_color="#FFFFFF",
        ).pack(pady=16)

    def _reset_password_dialog(self) -> None:
        colors = self.theme_palette_provider()
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Reset Password")
        win.geometry("420x220")
        win.configure(fg_color=colors["card_bg"])

        # UI POLISH ONLY
        ctk.CTkLabel(
            win,
            text="Enter the student number and set a new password.",
            font=(self.font_family, 12),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(win, text="Student Number", text_color=colors["text_primary"]).pack(anchor="w", padx=16, pady=(10, 4))
        student_number = ctk.CTkEntry(win, placeholder_text="00-00000")
        student_number.pack(fill="x", padx=16)

        ctk.CTkLabel(win, text="New Password", text_color=colors["text_primary"]).pack(anchor="w", padx=16, pady=(10, 4))
        new_password = ctk.CTkEntry(win, show="*", placeholder_text="Enter new password")
        new_password.pack(fill="x", padx=16)

        feedback_label = ctk.CTkLabel(
            win,
            text="Use the student number format 00-00000.",
            font=(self.font_family, 11),
            text_color=colors["text_secondary"],
        )
        feedback_label.pack(anchor="w", padx=16, pady=(8, 0))

        def submit() -> None:
            ok, reason = self.auth_db.reset_student_password(student_number.get().strip(), new_password.get())
            if not ok:
                feedback_label.configure(text=f"Failed: {reason}", text_color="#B22222")
                messagebox.showerror("Reset Password", f"Failed: {reason}")
                return
            messagebox.showinfo("Reset Password", "Password reset successful.")
            win.destroy()

        ctk.CTkButton(
            win,
            text="Reset Password",
            command=submit,
            width=150,
            height=34,
            fg_color="#C99700",
            hover_color="#B08200",
            text_color="#FFFFFF",
        ).pack(pady=16)

    def _delete_student_dialog(self) -> None:
        colors = self.theme_palette_provider()
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Delete Student")
        win.geometry("420x180")
        win.configure(fg_color=colors["card_bg"])

        # UI POLISH ONLY
        ctk.CTkLabel(
            win,
            text="Enter the student number you want to remove.",
            font=(self.font_family, 12),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(win, text="Student Number", text_color=colors["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))
        student_number = ctk.CTkEntry(win, placeholder_text="00-00000")
        student_number.pack(fill="x", padx=16)

        feedback_label = ctk.CTkLabel(
            win,
            text="A confirmation prompt will appear before deletion.",
            font=(self.font_family, 11),
            text_color=colors["text_secondary"],
        )
        feedback_label.pack(anchor="w", padx=16, pady=(8, 0))

        def submit() -> None:
            value = student_number.get().strip()
            if not value:
                return
            if not messagebox.askyesno("Delete Student", f"Delete student {value}?"):
                return
            ok, reason = self.auth_db.delete_student(value)
            if not ok:
                feedback_label.configure(text=f"Failed: {reason}", text_color="#B22222")
                messagebox.showerror("Delete Student", f"Failed: {reason}")
                return
            win.destroy()
            self._render_rows()

        ctk.CTkButton(
            win,
            text="Delete Student",
            command=submit,
            width=150,
            height=34,
            fg_color="#B22222",
            hover_color="#8F1B1B",
            text_color="#FFFFFF",
        ).pack(pady=18)
