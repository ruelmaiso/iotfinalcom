import json
import struct
from typing import Any, Optional


# Additive protocol contracts for optional per-session messaging.
# Existing message/command contracts remain unchanged.
MESSAGE_TYPES = {
    "student_session_message",
    "teacher_session_message",
    "student_extension_request",
    "teacher_extension_offer",
    "extension_offer_response",
}

MESSAGE_ACK_COMMANDS = {
    "SESSION_MESSAGE",
    "EXTENSION_REQUEST",
    "EXTENSION_OFFER",
    "PAUSE_TIMER",
    "RESUME_TIMER",
}


def send_json(sock, payload: dict[str, Any]) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def recv_json_line(file_obj) -> Optional[dict[str, Any]]:
    line = file_obj.readline()
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def send_frame(sock, frame_bytes: bytes) -> None:
    sock.sendall(struct.pack(">I", len(frame_bytes)) + frame_bytes)


def recv_frame(sock) -> Optional[bytes]:
    header = _recv_exact(sock, 4)
    if header is None:
        return None
    (size,) = struct.unpack(">I", header)
    if size <= 0 or size > 10_000_000:
        return None
    return _recv_exact(sock, size)


def _recv_exact(sock, size: int) -> Optional[bytes]:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)