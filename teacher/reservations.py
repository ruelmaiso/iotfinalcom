import time
from typing import Optional

from core.auth_db import AuthDatabase


class ReservationManager:
    def __init__(self, auth_db: AuthDatabase) -> None:
        self.auth_db = auth_db

    def create_reservation(
        self,
        student_number: str,
        pc_id: str,
        start_ts: float,
        end_ts: float,
        created_by: str,
    ) -> tuple[bool, str, Optional[int]]:
        return self.auth_db.create_reservation(
            student_number=student_number,
            pc_id=pc_id,
            start_ts=start_ts,
            end_ts=end_ts,
            created_by=created_by,
        )

    def cancel_reservation(self, reservation_id: int) -> tuple[bool, str]:
        return self.auth_db.cancel_reservation(reservation_id)

    def list_reservations(self, include_inactive: bool = True, limit: int = 500) -> list[dict]:
        return self.auth_db.list_reservations(include_inactive=include_inactive, limit=limit)

    def get_active_reservation(self, pc_id: str, now_ts: Optional[float] = None) -> Optional[dict]:
        ts = time.time() if now_ts is None else float(now_ts)
        return self.auth_db.get_active_reservation(pc_id=pc_id, now_ts=ts)