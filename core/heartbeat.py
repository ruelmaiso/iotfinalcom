import time
from dataclasses import dataclass


@dataclass
class HeartbeatState:
    last_seen: float = 0.0

    def touch(self) -> None:
        self.last_seen = time.time()

    def is_online(self, timeout_s: int) -> bool:
        if self.last_seen <= 0:
            return False
        return (time.time() - self.last_seen) <= timeout_s
