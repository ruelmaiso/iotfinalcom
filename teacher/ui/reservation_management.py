from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk


class ReservationManagementPanel:
    def __init__(self, parent, reservation_manager, auth_db, pc_ids_provider, theme_palette_provider, font_family: str = "Arial") -> None:
        self.parent = parent
        self.reservation_manager = reservation_manager
        self.auth_db = auth_db
        self.pc_ids_provider = pc_ids_provider
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
        self.window.title("Reservation Management")
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        width = min(920, max(360, screen_w - 80))
        height = min(700, max(320, screen_h - 80))
        self.window.geometry(f"{width}x{height}")
        self.window.configure(fg_color=colors["card_bg"])

        form = ctk.CTkFrame(self.window, fg_color="transparent")
        form.pack(fill="x", padx=12, pady=(12, 10))

        students = [row["student_number"] for row in self.auth_db.list_students()]
        if not students:
            students = [""]
        pc_ids = self.pc_ids_provider()
        if not pc_ids:
            pc_ids = [""]

        student_var = ctk.StringVar(value=students[0])
        pc_var = ctk.StringVar(value=pc_ids[0])

        ctk.CTkLabel(form, text="Student Number").grid(row=0, column=0, sticky="w", padx=6, pady=(0, 4))
        ctk.CTkOptionMenu(form, variable=student_var, values=students).grid(row=1, column=0, sticky="ew", padx=6)

        ctk.CTkLabel(form, text="PC ID").grid(row=0, column=1, sticky="w", padx=6, pady=(0, 4))
        ctk.CTkOptionMenu(form, variable=pc_var, values=pc_ids).grid(row=1, column=1, sticky="ew", padx=6)

        ctk.CTkLabel(form, text="Start (YYYY-MM-DD HH:MM)").grid(row=0, column=2, sticky="w", padx=6, pady=(0, 4))
        start_entry = ctk.CTkEntry(form)
        start_entry.grid(row=1, column=2, sticky="ew", padx=6)

        ctk.CTkLabel(form, text="End (YYYY-MM-DD HH:MM)").grid(row=0, column=3, sticky="w", padx=6, pady=(0, 4))
        end_entry = ctk.CTkEntry(form)
        end_entry.grid(row=1, column=3, sticky="ew", padx=6)

        ctk.CTkLabel(form, text="Created By").grid(row=0, column=4, sticky="w", padx=6, pady=(0, 4))
        created_by_entry = ctk.CTkEntry(form)
        created_by_entry.insert(0, "admin")
        created_by_entry.grid(row=1, column=4, sticky="ew", padx=6)

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)
        form.grid_columnconfigure(3, weight=1)
        form.grid_columnconfigure(4, weight=1)

        actions = ctk.CTkFrame(self.window, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(0, 8))

        def parse_ts(raw: str) -> float:
            return datetime.strptime(raw.strip(), "%Y-%m-%d %H:%M").timestamp()

        def fill_now_plus_1h() -> None:
            now = datetime.now().replace(second=0, microsecond=0)
            start_entry.delete(0, "end")
            start_entry.insert(0, now.strftime("%Y-%m-%d %H:%M"))
            end_entry.delete(0, "end")
            end_entry.insert(0, (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))

        def create_reservation() -> None:
            try:
                start_ts = parse_ts(start_entry.get())
                end_ts = parse_ts(end_entry.get())
            except ValueError:
                messagebox.showerror("Reservation", "Invalid datetime format. Use YYYY-MM-DD HH:MM")
                return
            ok, reason, _reservation_id = self.reservation_manager.create_reservation(
                student_number=student_var.get().strip(),
                pc_id=pc_var.get().strip(),
                start_ts=start_ts,
                end_ts=end_ts,
                created_by=created_by_entry.get().strip() or "admin",
            )
            if not ok:
                messagebox.showerror("Reservation", f"Failed: {reason}")
                return
            self._render_rows()

        def cancel_selected() -> None:
            reservation_id = id_entry.get().strip()
            if not reservation_id.isdigit():
                messagebox.showerror("Reservation", "Enter a numeric reservation ID to cancel.")
                return
            ok, reason = self.reservation_manager.cancel_reservation(int(reservation_id))
            if not ok:
                messagebox.showerror("Reservation", f"Failed: {reason}")
                return
            self._render_rows()

        ctk.CTkButton(actions, text="Now / +1h", command=fill_now_plus_1h, width=120).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Create Reservation", command=create_reservation, width=150).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Refresh", command=self._render_rows, width=100).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(actions, text="Reservation ID").pack(side="left", padx=(8, 4))
        id_entry = ctk.CTkEntry(actions, width=120)
        id_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Cancel Reservation", command=cancel_selected, width=150).pack(side="left")

        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(4, 4))
        labels = ["ID", "Student #", "PC", "Start", "End", "Status", "Created By"]
        for idx, label in enumerate(labels):
            ctk.CTkLabel(header, text=label, font=(self.font_family, 12, "bold")).grid(row=0, column=idx, sticky="w", padx=4)
            header.grid_columnconfigure(idx, weight=1)

        self.rows_frame = ctk.CTkScrollableFrame(self.window, fg_color=colors["card_bg"])
        self.rows_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._render_rows()

    def _render_rows(self) -> None:
        if self.rows_frame is None or not self.rows_frame.winfo_exists():
            return
        for child in self.rows_frame.winfo_children():
            child.destroy()
        rows = self.reservation_manager.list_reservations(include_inactive=True, limit=1000)
        if not rows:
            ctk.CTkLabel(self.rows_frame, text="No reservations found.").pack(anchor="w", padx=10, pady=10)
            return
        for row in rows:
            line = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
            line.pack(fill="x", padx=4, pady=3)
            values = [
                str(row.get("id", "")),
                str(row.get("student_number", "")),
                str(row.get("pc_id", "")),
                self._fmt_ts(row.get("start_ts")),
                self._fmt_ts(row.get("end_ts")),
                str(row.get("status", "")),
                str(row.get("created_by", "")),
            ]
            for idx, value in enumerate(values):
                ctk.CTkLabel(line, text=value).grid(row=0, column=idx, sticky="w", padx=4)
                line.grid_columnconfigure(idx, weight=1)

    def _fmt_ts(self, value) -> str:
        if value is None:
            return "--"
        try:
            return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "--"
