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
        toolbar.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkButton(toolbar, text="Add Student", command=self._add_student_dialog, width=120).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Reset Password", command=self._reset_password_dialog, width=130).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Delete Student", command=self._delete_student_dialog, width=130).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Refresh", command=self._render_rows, width=100).pack(side="right")

        head = ctk.CTkFrame(self.window, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(head, text="Student Number", font=(self.font_family, 12, "bold")).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(head, text="Full Name", font=(self.font_family, 12, "bold")).grid(row=0, column=1, sticky="w", padx=6)
        ctk.CTkLabel(head, text="Year / Section", font=(self.font_family, 12, "bold")).grid(row=0, column=2, sticky="w", padx=6)
        head.grid_columnconfigure(0, weight=1)
        head.grid_columnconfigure(1, weight=2)
        head.grid_columnconfigure(2, weight=1)

        self.rows_frame = ctk.CTkScrollableFrame(self.window, fg_color=colors["card_bg"])
        self.rows_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._render_rows()

    def _render_rows(self) -> None:
        if self.rows_frame is None or not self.rows_frame.winfo_exists():
            return
        for child in self.rows_frame.winfo_children():
            child.destroy()

        rows = self.auth_db.list_students()
        if not rows:
            ctk.CTkLabel(self.rows_frame, text="No students found.").pack(anchor="w", padx=10, pady=10)
            return

        for row in rows:
            line = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
            line.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(line, text=str(row.get("student_number", ""))).grid(row=0, column=0, sticky="w", padx=6)
            ctk.CTkLabel(line, text=str(row.get("full_name", ""))).grid(row=0, column=1, sticky="w", padx=6)
            ctk.CTkLabel(line, text=str(row.get("year_section", ""))).grid(row=0, column=2, sticky="w", padx=6)
            line.grid_columnconfigure(0, weight=1)
            line.grid_columnconfigure(1, weight=2)
            line.grid_columnconfigure(2, weight=1)

    def _add_student_dialog(self) -> None:
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Add Student")
        win.geometry("420x320")

        entries = {}
        for label, key, show in [
            ("Full Name", "full_name", None),
            ("Year / Section", "year_section", None),
            ("Student Number", "student_number", None),
            ("Password", "password", "*"),
        ]:
            ctk.CTkLabel(win, text=label).pack(anchor="w", padx=16, pady=(10, 4))
            e = ctk.CTkEntry(win, show=show)
            e.pack(fill="x", padx=16)
            entries[key] = e

        def submit() -> None:
            payload = {k: v.get().strip() for k, v in entries.items()}
            ok, reason = self.auth_db.add_student_admin(
                payload["full_name"],
                payload["year_section"],
                payload["student_number"],
                payload["password"],
            )
            if not ok:
                messagebox.showerror("Add Student", f"Failed: {reason}")
                return
            win.destroy()
            self._render_rows()

        ctk.CTkButton(win, text="Create", command=submit).pack(pady=16)

    def _reset_password_dialog(self) -> None:
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Reset Password")
        win.geometry("420x220")

        ctk.CTkLabel(win, text="Student Number").pack(anchor="w", padx=16, pady=(10, 4))
        student_number = ctk.CTkEntry(win)
        student_number.pack(fill="x", padx=16)

        ctk.CTkLabel(win, text="New Password").pack(anchor="w", padx=16, pady=(10, 4))
        new_password = ctk.CTkEntry(win, show="*")
        new_password.pack(fill="x", padx=16)

        def submit() -> None:
            ok, reason = self.auth_db.reset_student_password(student_number.get().strip(), new_password.get())
            if not ok:
                messagebox.showerror("Reset Password", f"Failed: {reason}")
                return
            messagebox.showinfo("Reset Password", "Password reset successful.")
            win.destroy()

        ctk.CTkButton(win, text="Reset", command=submit).pack(pady=16)

    def _delete_student_dialog(self) -> None:
        win = ctk.CTkToplevel(self.window)
        win.transient(self.window)
        win.lift()
        win.focus_force()
        win.grab_set()
        win.title("Delete Student")
        win.geometry("420x180")

        ctk.CTkLabel(win, text="Student Number").pack(anchor="w", padx=16, pady=(14, 4))
        student_number = ctk.CTkEntry(win)
        student_number.pack(fill="x", padx=16)

        def submit() -> None:
            value = student_number.get().strip()
            if not value:
                return
            if not messagebox.askyesno("Delete Student", f"Delete student {value}?"):
                return
            ok, reason = self.auth_db.delete_student(value)
            if not ok:
                messagebox.showerror("Delete Student", f"Failed: {reason}")
                return
            win.destroy()
            self._render_rows()

        ctk.CTkButton(win, text="Delete", command=submit).pack(pady=18)
