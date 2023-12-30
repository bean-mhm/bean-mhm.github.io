from enum import Enum


class LogLevel(Enum):
    Error = 0
    Warning = 1
    Info = 2
    Verbose = 3

    def __str__(self):
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
    global log_level
    log_level = level


def log(level: LogLevel, message, details={}):
    if level.value > max_log_level.value:
        return

    s_details = ''
    for key, value in details.items():
        s_details += f'[{key}={value}] '

    print(f'{level} {s_details}{message}')


def error(message, details={}):
    log(LogLevel.Error, message, details)


def warning(message, details={}):
    log(LogLevel.Warning, message, details)


def info(message, details={}):
    log(LogLevel.Info, message, details)


def verbose(message, details={}):
    log(LogLevel.Verbose, message, details)
