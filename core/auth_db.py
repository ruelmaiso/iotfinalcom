import hashlib
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional


class AuthDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    year_section TEXT NOT NULL,
                    student_number TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_ts REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pc_id TEXT NOT NULL,
                    student_number TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    year_section TEXT NOT NULL,
                    login_ts REAL NOT NULL,
                    logout_ts REAL,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_pc_login ON sessions(pc_id, login_ts DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_student_login ON sessions(student_number, login_ts DESC)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    pc_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_ts REAL NOT NULL,
                    end_ts REAL,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_recordings_session ON session_recordings(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_recordings_pc_start ON session_recordings(pc_id, start_ts DESC)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_number TEXT NOT NULL,
                    pc_id TEXT NOT NULL,
                    start_ts REAL NOT NULL,
                    end_ts REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_ts REAL NOT NULL,
                    FOREIGN KEY(student_number) REFERENCES students(student_number)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reservations_pc_time ON reservations(pc_id, start_ts, end_ts)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reservations_student_time ON reservations(student_number, start_ts DESC)")

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

    def _new_salt(self) -> str:
        return os.urandom(16).hex()

    def register_student(self, full_name: str, year_section: str, student_number: str, password: str) -> tuple[bool, str]:
        now = time.time()
        student_number = student_number.strip()
        if not student_number:
            return False, "missing_student_number"
        with self.lock:
            with self._connect() as conn:
                exists = conn.execute(
                    "SELECT student_number FROM students WHERE student_number=?",
                    (student_number,),
                ).fetchone()
                if exists:
                    return False, "student_number_exists"
                salt = self._new_salt()
                conn.execute(
                    """
                    INSERT INTO students(full_name, year_section, student_number, password_hash, password_salt, created_ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (full_name.strip(), year_section.strip(), student_number, self._hash_password(password, salt), salt, now),
                )
        return True, "registered"

    def list_students(self) -> list[dict]:
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, full_name, year_section, student_number, created_ts
                    FROM students
                    ORDER BY student_number ASC
                    """
                ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "full_name": str(row["full_name"]),
                "year_section": str(row["year_section"]),
                "student_number": str(row["student_number"]),
                "created_ts": float(row["created_ts"]),
            }
            for row in rows
        ]

    def add_student_admin(self, full_name: str, year_section: str, student_number: str, password: str) -> tuple[bool, str]:
        return self.register_student(full_name, year_section, student_number, password)

    def reset_student_password(self, student_number: str, new_password: str) -> tuple[bool, str]:
        cleaned = student_number.strip()
        if not cleaned:
            return False, "missing_student_number"
        if not str(new_password):
            return False, "missing_password"
        with self.lock:
            with self._connect() as conn:
                row = conn.execute("SELECT id FROM students WHERE student_number=?", (cleaned,)).fetchone()
                if not row:
                    return False, "student_not_found"
                salt = self._new_salt()
                conn.execute(
                    "UPDATE students SET password_hash=?, password_salt=? WHERE student_number=?",
                    (self._hash_password(new_password, salt), salt, cleaned),
                )
        return True, "password_reset"

    def delete_student(self, student_number: str) -> tuple[bool, str]:
        cleaned = student_number.strip()
        if not cleaned:
            return False, "missing_student_number"
        with self.lock:
            with self._connect() as conn:
                row = conn.execute("SELECT id FROM students WHERE student_number=?", (cleaned,)).fetchone()
                if not row:
                    return False, "student_not_found"
                active = conn.execute(
                    "SELECT 1 FROM sessions WHERE student_number=? AND status='active' AND logout_ts IS NULL LIMIT 1",
                    (cleaned,),
                ).fetchone()
                if active:
                    return False, "student_has_active_session"
                conn.execute("DELETE FROM students WHERE student_number=?", (cleaned,))
        return True, "deleted"

    def create_reservation(
        self,
        student_number: str,
        pc_id: str,
        start_ts: float,
        end_ts: float,
        created_by: str,
    ) -> tuple[bool, str, Optional[int]]:
        sn = student_number.strip()
        pc = pc_id.strip()
        if not sn or not pc:
            return False, "missing_fields", None
        if float(end_ts) <= float(start_ts):
            return False, "invalid_time_window", None
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                student = conn.execute("SELECT 1 FROM students WHERE student_number=?", (sn,)).fetchone()
                if not student:
                    return False, "student_not_found", None
                overlap = conn.execute(
                    """
                    SELECT 1
                    FROM reservations
                    WHERE pc_id = ?
                    AND status = 'scheduled'
                    AND NOT (end_ts <= ? OR start_ts >= ?)
                    LIMIT 1
                    """,
                    (pc, float(start_ts), float(end_ts)),
                ).fetchone()
                if overlap:
                    return False, "reservation_conflict", None
                cur = conn.execute(
                    """
                    INSERT INTO reservations(student_number, pc_id, start_ts, end_ts, status, created_by, created_ts)
                    VALUES (?, ?, ?, ?, 'scheduled', ?, ?)
                    """,
                    (sn, pc, float(start_ts), float(end_ts), created_by.strip() or "admin", now),
                )
                return True, "created", int(cur.lastrowid)

    def cancel_reservation(self, reservation_id: int) -> tuple[bool, str]:
        with self.lock:
            with self._connect() as conn:
                row = conn.execute("SELECT id, status FROM reservations WHERE id=?", (int(reservation_id),)).fetchone()
                if not row:
                    return False, "reservation_not_found"
                if str(row["status"]) != "scheduled":
                    return False, "reservation_not_schedulable"
                conn.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (int(reservation_id),))
        return True, "cancelled"

    def list_reservations(self, include_inactive: bool = True, limit: int = 500) -> list[dict]:
        limit = max(1, int(limit))
        where = "" if include_inactive else "WHERE status='scheduled'"
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    f"""
                    SELECT id, student_number, pc_id, start_ts, end_ts, status, created_by, created_ts
                    FROM reservations
                    {where}
                    ORDER BY start_ts DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "student_number": str(row["student_number"]),
                "pc_id": str(row["pc_id"]),
                "start_ts": float(row["start_ts"]),
                "end_ts": float(row["end_ts"]),
                "status": str(row["status"]),
                "created_by": str(row["created_by"]),
                "created_ts": float(row["created_ts"]),
            }
            for row in rows
        ]

    def get_active_reservation(self, pc_id: str, now_ts: Optional[float] = None) -> Optional[dict]:
        now = time.time() if now_ts is None else float(now_ts)
        cleaned_pc = pc_id.strip()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE reservations
                    SET status='completed'
                    WHERE status='scheduled' AND end_ts < ?
                    """,
                    (now,),
                )
                row = conn.execute(
                    """
                    SELECT id, student_number, pc_id, start_ts, end_ts, status, created_by, created_ts
                    FROM reservations
                    WHERE pc_id=?
                    AND status='scheduled'
                    AND ? BETWEEN start_ts AND end_ts
                    ORDER BY start_ts ASC
                    LIMIT 1
                    """,
                    (cleaned_pc, now),
                ).fetchone()
        if not row:
            return None
        return {
            "id": int(row["id"]),
            "student_number": str(row["student_number"]),
            "pc_id": str(row["pc_id"]),
            "start_ts": float(row["start_ts"]),
            "end_ts": float(row["end_ts"]),
            "status": str(row["status"]),
            "created_by": str(row["created_by"]),
            "created_ts": float(row["created_ts"]),
        }

    def verify_login(self, student_number: str, password: str) -> Optional[dict]:
        with self.lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT full_name, year_section, student_number, password_hash, password_salt FROM students WHERE student_number=?",
                    (student_number.strip(),),
                ).fetchone()
                if not row:
                    return None
                if self._hash_password(password, str(row["password_salt"])) != str(row["password_hash"]):
                    return None
                return {
                    "full_name": str(row["full_name"]),
                    "year_section": str(row["year_section"]),
                    "student_number": str(row["student_number"]),
                }

    def open_session(self, pc_id: str, user: dict) -> int:
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE sessions SET logout_ts=?, status='superseded' WHERE pc_id=? AND status='active'",
                    (now, pc_id),
                )
                cur = conn.execute(
                    """
                    INSERT INTO sessions(pc_id, student_number, full_name, year_section, login_ts, status)
                    VALUES (?, ?, ?, ?, ?, 'active')
                    """,
                    (pc_id, user["student_number"], user["full_name"], user["year_section"], now),
                )
                return int(cur.lastrowid)

    def close_active_session(self, pc_id: str, status: str = "closed") -> None:
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE sessions SET logout_ts=?, status=? WHERE pc_id=? AND status='active'",
                    (now, status, pc_id),
                )



    def get_active_sessions(self) -> list[dict]:
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, pc_id, student_number, full_name, year_section, login_ts, status
                    FROM sessions
                    WHERE logout_ts IS NULL AND status IN ('active', 'interrupted')
                    ORDER BY login_ts DESC
                    """
                ).fetchall()
        return [
            {
                "session_id": int(row["id"]),
                "pc_id": str(row["pc_id"]),
                "student_number": str(row["student_number"]),
                "full_name": str(row["full_name"]),
                "year_section": str(row["year_section"]),
                "login_ts": float(row["login_ts"]) if row["login_ts"] is not None else 0.0,
                "status": str(row["status"]),
            }
            for row in rows
        ]

    def close_all_active_recordings(self, status: str = "server_restart") -> None:
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE session_recordings SET end_ts=?, status=? WHERE status='active'",
                    (now, status),
                )

    def get_today_usage_seconds(self, student_number: str, now_ts: Optional[float] = None) -> int:
        now = time.time() if now_ts is None else float(now_ts)
        local = time.localtime(now)
        day_start = time.mktime((local.tm_year, local.tm_mon, local.tm_mday, 0, 0, 0, local.tm_wday, local.tm_yday, local.tm_isdst))
        total = 0.0
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT login_ts, logout_ts
                    FROM sessions
                    WHERE student_number=? AND login_ts>=?
                    ORDER BY login_ts ASC
                    """,
                    (student_number.strip(), day_start),
                ).fetchall()
        for row in rows:
            login_ts = float(row["login_ts"]) if row["login_ts"] is not None else now
            logout_ts = float(row["logout_ts"]) if row["logout_ts"] is not None else now
            total += max(0.0, logout_ts - login_ts)
        return int(total)

    def open_recording(self, session_id: int, pc_id: str, file_path: str) -> int:
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO session_recordings(session_id, pc_id, file_path, start_ts, status)
                    VALUES (?, ?, ?, ?, 'active')
                    """,
                    (session_id, pc_id, file_path, now),
                )
                return int(cur.lastrowid)

    def close_recording(self, recording_id: int, status: str = "closed") -> None:
        now = time.time()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE session_recordings SET end_ts=?, status=? WHERE id=? AND status='active'",
                    (now, status, recording_id),
                )

    def get_sessions_for_pc(self, pc_id: str, limit: int = 200) -> list[dict]:
        limit = max(1, int(limit))
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT s.login_ts, s.logout_ts, s.full_name, s.student_number, s.year_section, s.status,
                           (
                               SELECT sr.file_path
                               FROM session_recordings sr
                               WHERE sr.session_id = s.id
                               ORDER BY sr.start_ts DESC
                               LIMIT 1
                           ) AS recording_path
                    FROM sessions s
                    WHERE s.pc_id=?
                    ORDER BY s.login_ts DESC
                    LIMIT ?
                    """,
                    (pc_id, limit),
                ).fetchall()
        return [
            {
                "login_ts": float(row["login_ts"]) if row["login_ts"] is not None else None,
                "logout_ts": float(row["logout_ts"]) if row["logout_ts"] is not None else None,
                "full_name": str(row["full_name"]),
                "student_number": str(row["student_number"]),
                "year_section": str(row["year_section"]),
                "status": str(row["status"]),
                "recording_path": str(row["recording_path"]) if row["recording_path"] is not None else "",
            }
            for row in rows
        ]

    def get_all_sessions(self, limit: int = 500) -> list[dict]:
        limit = max(1, int(limit))
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT s.pc_id, s.login_ts, s.logout_ts, s.full_name, s.student_number, s.year_section, s.status,
                           (
                               SELECT sr.file_path
                               FROM session_recordings sr
                               WHERE sr.session_id = s.id
                               ORDER BY sr.start_ts DESC
                               LIMIT 1
                           ) AS recording_path
                    FROM sessions s
                    ORDER BY s.login_ts DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "pc_id": str(row["pc_id"]),
                "login_ts": float(row["login_ts"]) if row["login_ts"] is not None else None,
                "logout_ts": float(row["logout_ts"]) if row["logout_ts"] is not None else None,
                "full_name": str(row["full_name"]),
                "student_number": str(row["student_number"]),
                "year_section": str(row["year_section"]),
                "status": str(row["status"]),
                "recording_path": str(row["recording_path"]) if row["recording_path"] is not None else "",
            }
            for row in rows
        ]