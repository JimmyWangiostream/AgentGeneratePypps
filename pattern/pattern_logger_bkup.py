from datetime import datetime
import logging
from os import makedirs, path
from typing import Any, Self
from Script import api

FLOW = 35
ERROR_LAST_BEHAVIOR = 41
ERROR_FAIL_PHENOMENON = 42
PRINT_BUFFER = 31

class CustomFormatter(logging.Formatter):
    grey = "\x1b[90m"
    green = "\x1b[92m"
    yellow = "\x1b[93m"
    red = "\x1b[91m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    cyan = "\x1b[96m"

    def __init__(self, fmt: str) -> None:
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.reset + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.reset + self.fmt + self.reset)
        formatter = logging.Formatter(
            log_fmt,
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

class PyppsLogger(logging.Logger):
    def __init__(self, name: str):
        super().__init__(name, logging.NOTSET)

    def flow(self, flow_id: int | str, msg: object, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(FLOW):
            self._log(FLOW, f"[{flow_id}] {msg}", args, **kwargs)

    def error_lb(self, msg: object, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(ERROR_LAST_BEHAVIOR):
            self._log(ERROR_LAST_BEHAVIOR, msg, args, **kwargs)

    def error_fp(self, msg: object, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(ERROR_FAIL_PHENOMENON):
            self._log(ERROR_FAIL_PHENOMENON, msg, args, **kwargs)

    def print_buffer(self, buffer: bytearray, block: int = 512) -> None:
        if not self.isEnabledFor(PRINT_BUFFER):
            return
        head = '      |  00  01  02  03  04  05  06  07  08  09  0A  0B  0C  0D  0E  0F         ASCII'
        segment = '-------------------------------------------------------------------------------------------'
        line_pattern = '%03X0  |'
        item_pattern = '  %02X'
        index = 0
        line = ''
        ascii = ''

        for item in buffer:
            if index % block == 0:  # Start of a new block
                if index != 0:  # If not the first block, log the previous line
                    if ascii:
                        line += '    ' + ascii
                        self._log(PRINT_BUFFER, line, ())
                # Log the block header and separator
                self._log(PRINT_BUFFER, head, ())
                self._log(PRINT_BUFFER, segment, ())
                ascii = ''
                line = ''

            if index % 16 == 0:  # Start of a new line
                if ascii:
                    line += '    ' + ascii
                    self._log(PRINT_BUFFER, line, ())  # Log the completed line
                ascii = ''
                line = line_pattern % (int(index / 16))

            line += item_pattern % (int(item))

            if 32 < item < 127:  # Printable ASCII range
                ascii += chr(item)
            else:
                ascii += '.'

            index += 1

        # Log the final line
        if line:
            line += '    ' + ascii
            self._log(PRINT_BUFFER, line, ())
        return None

def set_logger(src_logger: logging.Logger) -> None:
    logger.setLevel(src_logger.level)
    logging.addLevelName(FLOW, 'FLOW')
    logging.addLevelName(ERROR_LAST_BEHAVIOR, 'ERROR_LAST_BEHAVIOR')
    logging.addLevelName(ERROR_FAIL_PHENOMENON, 'ERROR_FAIL_PHENOMENON')
    logging.addLevelName(PRINT_BUFFER, 'BUFFER')

    logger.handlers.clear()

    for h in src_logger.handlers:
        logger.addHandler(h)

def set_to_debug_mode_logger(ptn_name: str, log_path: str) -> None:
    # Change to logging.DEBUG if you need debugging info
    level = logging.INFO

    makedirs(log_path, exist_ok=True)

    debug_logger = logging.Logger('DEBUG_MODE', level)
    log_fmt = "{asctime} - {levelname} - {message}"
    formatter = logging.Formatter(
        log_fmt,
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter(log_fmt))
    console_handler.setLevel(level)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = path.join(log_path, f'{ptn_name}_{timestamp}.log')
    file_handler = logging.FileHandler(file_path, encoding="utf-8", mode="w")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    debug_logger.addHandler(console_handler)
    debug_logger.addHandler(file_handler)

    set_logger(debug_logger)


logger: PyppsLogger = PyppsLogger(__name__) # Lazy Initialization