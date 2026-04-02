from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkConfig:
    teacher_host: str = "192.168.1.127"
    control_port: int = 9201
    video_port: int = 9200
    sensor_port: int = 9202
    command_fallback_port: int = 9203


@dataclass(frozen=True)
class RuntimeConfig:
    max_fps: int = 5
    heartbeat_interval_s: int = 5
    heartbeat_timeout_s: int = 10
    reconnect_interval_s: int = 3
    # frame_width: int = 640
    # frame_height: int = 360
    frame_width: int = 1280
    frame_height: int = 720
    frame_queue_max: int = 5
    sensor_timeout_s: int = 10
    timer_tick_s: float = 0.5
    session_disconnect_grace_s: int = 30


NETWORK = NetworkConfig()
RUNTIME = RuntimeConfig()

# from dataclasses import dataclass


# @dataclass(frozen=True)
# class NetworkConfig:
#     teacher_host: str = "0.0.0.0"
#     control_port: int = 9201
#     video_port: int = 9200
#     sensor_port: int = 9202


# @dataclass(frozen=True)
# class RuntimeConfig:
#     max_fps: int = 10
#     heartbeat_interval_s: int = 5
#     heartbeat_timeout_s: int = 10
#     reconnect_interval_s: int = 3
#     frame_width: int = 1280
#     frame_height: int = 720
#     frame_queue_max: int = 5
#     sensor_timeout_s: int = 10
#     timer_tick_s: float = 0.5


# STREAM_PROFILES: dict[str, tuple[int, int]] = {
#     "360p": (640, 360),
#     "720p": (1280, 720),
#     "1080p": (1920, 1080),
# }

# DEFAULT_STREAM_PROFILE = "720p"


# NETWORK = NetworkConfig()
# RUNTIME = RuntimeConfig()