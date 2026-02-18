import os
import json
import logging
import logging.handlers
from datetime import datetime, timedelta


class JsonFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        dt = datetime.fromtimestamp(record.created)
        microseconds = int(record.msecs * 1000)

        if datefmt:
            if ".%" in datefmt:
                parts = datefmt.split(".%")
                return (
                    dt.strftime(parts[0])
                    + f".{microseconds:06d}"
                    + dt.strftime(parts[1])
                )
            return dt.strftime(datefmt)

        date_part = dt.strftime("%d %b %Y %A")
        time_part = (
            dt.strftime("%I:%M:%S") + f".{microseconds:06d} " + dt.strftime("%p")
        )
        return f"{date_part} {time_part}"

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "msg": record.getMessage(),
        }

        standard_attrs = set(
            logging.LogRecord(None, None, "", 0, "", (), None).__dict__.keys()
        )
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in standard_attrs
        }
        log_record.update(extra_fields)

        return json.dumps(log_record, ensure_ascii=False)


class CustomTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, *args, **kwargs):
        self._log_directory = kwargs.pop("log_directory", "./logs")
        super().__init__(*args, **kwargs)

    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None

        yesterday = datetime.now() - timedelta(days=1)
        new_filename = os.path.join(
            self._log_directory, f"{yesterday.strftime('%Y-%m-%d')}.log"
        )

        if os.path.exists(new_filename):
            os.remove(new_filename)

        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, new_filename)

        self.stream = self._open()

        self.rolloverAt = self.rolloverAt + self.interval
