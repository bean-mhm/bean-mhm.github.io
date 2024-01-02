from enum import Enum


class LogLevel(Enum):
    Error = 0
    Warning = 1
    Info = 2
    Verbose = 3

    def __str__(self) -> str:
        if self == LogLevel.Error:
            return '[E]'
        if self == LogLevel.Warning:
            return '[W]'
        if self == LogLevel.Info:
            return '[I]'
        if self == LogLevel.Verbose:
            return '[V]'
        return ''


max_log_level = LogLevel.Verbose


def set_max_log_level(level: LogLevel):
    global max_log_level
    max_log_level = level


def log(level: LogLevel, message, extra: list = []):
    if level.value > max_log_level.value:
        return

    s_details = ''
    for item in extra:
        s_details += f'[{item}] '

    print(f'{level} {s_details}{message}')


def error(message, extra: list = []):
    log(LogLevel.Error, message, extra)


def warning(message, extra: list = []):
    log(LogLevel.Warning, message, extra)


def info(message, extra: list = []):
    log(LogLevel.Info, message, extra)


def verbose(message, extra: list = []):
    log(LogLevel.Verbose, message, extra)
