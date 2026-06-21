from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Literal
import inspect


__all__ = [
    "LogEntry",
    "set_log_callback"
]


@dataclass
class LogEntry:
    class Level(Enum):
        DEBUG = auto()
        INFO = auto()
        WARN = auto()
        ERROR = auto()

    class Source(Enum):
        SDK = auto()
        LIB = auto()

    message: str = ""
    level: Level = Level.INFO
    source: Source = Source.LIB
    current_file: str = ""
    current_function: str = ""
    current_line: int = 0


def _default_log_callback(log: LogEntry):
    print(f"[{log.level.name}] - {log.message}")

def _null_log_callback(log: LogEntry):
    return

_log_callback: Callable[[LogEntry], None] = _default_log_callback

def set_log_callback(func: Callable[[LogEntry], None] | None | Literal["default"] = None):
    """
    A callback function for logging. 
    
    Parameter
    ---------
    func: Callable, "default", None. Default is None.  
        * If callable with argument `LogEntry`, it will be set as the logging callback function.  
        * If "default", it will use the defult logging which will simply print to stdout.  
        * If None, it will disable logging.

    Example
    -------
    >>> logger = logging.getLogger(__name__)
    >>> def my_logger(entry: LogEntry):
    ...     if entry.source == LogEntry.Source.SDK:  # let's skip SDK message
    ...         pass
    ...     f = {
    ...         LogEntry.Level.DEBUG: logger.debug,
    ...         LogEntry.Level.INFO: logger.info,
    ...         LogEntry.Level.WARN: logger.warn,
    ...         LogEntry.Level.ERROR: logger.error,
    ...     }.get(entry.level)
    ...     f(entry.message)
    >>> common_lib.set_log_callback(my_logger)
    """
    global _log_callback
    if func is None:
        _log_callback = _null_log_callback
    elif func == "default":
        _log_callback = _default_log_callback
    else:
        _log_callback = func


# ----------------------------------------------------
# --------------- Internal used in Lib ---------------
def print_log(log: LogEntry):
    _log_callback(log)

def prepare_log_entry(
        stack_caller_idx=2,
        *,
        message="",
        level=LogEntry.Level.INFO,
        source=LogEntry.Source.LIB):
    caller = inspect.stack()[stack_caller_idx]
    log = LogEntry(
        message=message,
        level=level,
        source=source,
        current_file=caller.filename,
        current_function=caller.function,
        current_line=caller.lineno
    )
    return log
    
def print_msg(message: str):
    log = prepare_log_entry(
        message=message,
        level=LogEntry.Level.INFO,
        source=LogEntry.Source.LIB
    )
    print_log(log)

def print_debug(message: str):
    log = prepare_log_entry(
        message=message,
        level=LogEntry.Level.DEBUG,
        source=LogEntry.Source.LIB
    )
    print_log(log)

def print_error(message: str):
    log = prepare_log_entry(
        message=message,
        level=LogEntry.Level.ERROR,
        source=LogEntry.Source.LIB
    )
    print_log(log)

def print_warn(message: str):
    log = prepare_log_entry(
        message=message,
        level=LogEntry.Level.WARN,
        source=LogEntry.Source.LIB
    )
    print_log(log)