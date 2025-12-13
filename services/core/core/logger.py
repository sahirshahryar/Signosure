import os
from datetime import datetime
from enum import IntEnum, auto
from typing import Any, Callable

PROGRAM_START = datetime.now()


class LogLevel(IntEnum):
    ERROR = auto()
    WARN = auto()
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()

    @classmethod
    def match(cls, level: str) -> "LogLevel":
        for lev in cls:
            if lev.name.lower() == level.lower():
                return lev

        raise ValueError(f"Unknown logging level '{level}'")


LOGGER_FUNCTION = print
LOG_LEVEL = LogLevel.INFO

use_colors = os.getenv("USE_COLORS")
USE_COLORS = True if use_colors is None else use_colors
LOG_INDENT = " " * 12


class Color(IntEnum):
    # Reset
    RESET = 0

    # Styles
    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4

    # Foreground colors
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    # Bright foreground colors
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97

    # Background colors
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_WHITE = 47

    def __str__(self) -> str:
        if USE_COLORS:
            return f"\033[{self.value}m"
        return ""


def set_logging_level(level: LogLevel) -> None:
    global LOG_LEVEL
    LOG_LEVEL = level
    info(f"Logging level set to {level.name}.")


def set_logger_function(function: Callable[[Any], Any]) -> None:
    global LOGGER_FUNCTION
    LOGGER_FUNCTION = function


def log_at_level(level: LogLevel, msg: str) -> None:
    if level > LOG_LEVEL:
        return

    program_time = (datetime.now() - PROGRAM_START).total_seconds()
    time_color = Color.RED if os.getuid() == 0 else Color.CYAN
    msg = msg.replace("\n", f"\n{LOG_INDENT}")

    LOGGER_FUNCTION(f"{time_color}{program_time:9.3f} {Color.RESET}{msg}")


def error(msg: str) -> None:
    log_at_level(
        LogLevel.ERROR,
        f"{Color.BOLD}{Color.BG_RED}{Color.BLACK}E{Color.RESET} {Color.RED}{msg}",
    )


def warn(msg: str) -> None:
    log_at_level(
        LogLevel.WARN,
        f"{Color.BOLD}{Color.BG_YELLOW}{Color.BLACK}W{Color.RESET} {Color.YELLOW}{msg}",
    )


def info(msg: str) -> None:
    log_at_level(
        LogLevel.INFO,
        f"{Color.BOLD}{Color.BG_WHITE}{Color.BLACK}I{Color.RESET} {msg}",
    )


def debug(msg: str) -> None:
    log_at_level(
        LogLevel.DEBUG,
        f"{Color.BOLD}{Color.BG_CYAN}{Color.BLACK}D{Color.RESET} {Color.CYAN}{msg}",
    )


def trace(msg: str) -> None:
    log_at_level(
        LogLevel.TRACE,
        f"{Color.BOLD}{Color.BG_GREEN}{Color.BLACK}T{Color.RESET} {Color.GREEN}{msg}",
    )


if os.getuid() == 0:
    warn(
        f"signosure-core has been started with root permissions. "
        f"As long as the timestamps are printed in {Color.RED}red"
        f"{Color.YELLOW}, the process has root permissions. For security, "
        f"avoid running as root, or drop root permissions by running"
        f"os.setgid(1000), os.setuid(1000)."
    )
