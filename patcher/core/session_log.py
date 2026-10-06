import logging
import sys
from datetime import datetime
from pathlib import Path

from patcher.core.command_executor import OUTPUT_LOGGER

logger = logging.getLogger(__name__)

KEPT_FILES = 10
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
TIME_FORMAT = "%H:%M:%S"


class SessionLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.name == OUTPUT_LOGGER:
            return record.getMessage()
        return super().format(record)


class SessionLog:
    _path: Path | None = None

    @staticmethod
    def folder() -> Path:
        return Path.home() / "Library" / "Application Support" / "HLPatcher" / "logs"

    @classmethod
    def start(cls, debug: bool) -> Path | None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG if debug else logging.INFO)
        logging.captureWarnings(True)

        messages = logging.StreamHandler(sys.stderr)
        messages.setFormatter(logging.Formatter(LOG_FORMAT, TIME_FORMAT))
        messages.addFilter(lambda record: record.name != OUTPUT_LOGGER)
        output = logging.StreamHandler(sys.stdout)
        output.addFilter(lambda record: record.name == OUTPUT_LOGGER)
        root.addHandler(messages)
        root.addHandler(output)

        path = cls.folder() / f"session-{datetime.now():%Y-%m-%d_%H-%M-%S}.log"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            file = logging.FileHandler(path, encoding="utf-8")
        except OSError as e:
            logger.warning(f"Couldn't save this session's log to {path}: {e}")
            return None
        file.setFormatter(SessionLogFormatter(LOG_FORMAT, TIME_FORMAT))
        root.addHandler(file)
        cls._path = path
        cls.prune("session-*.log")
        logger.info(f"Saving this session's log to {path}")
        return path

    @classmethod
    def current(cls) -> Path | None:
        return cls._path

    @classmethod
    def prune(cls, pattern: str):
        for old in sorted(cls.folder().glob(pattern))[:-KEPT_FILES]:
            old.unlink(missing_ok=True)
