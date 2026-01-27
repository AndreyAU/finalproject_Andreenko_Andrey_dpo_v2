"""
Logging configuration for ValutaTrade Hub.

Назначение:
- централизованная настройка логирования доменных операций
- человекочитаемый формат
- ротация логов
- уровни INFO / DEBUG

Используется логгер: "valutatrade"
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> None:
    """
    Инициализация логгера проекта.

    - файл: logs/actions.log
    - ротация по размеру
    - формат: строковый (человекочитаемый)
    """
    settings = SettingsLoader()

    log_dir: Path = settings.get("LOG_DIR")
    log_level_str: str = settings.get("LOG_LEVEL", "INFO")
    log_format_type: str = settings.get("LOG_FORMAT", "plain")

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "actions.log"

    level = getattr(logging, log_level_str.upper(), logging.INFO)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(level)
    logger.propagate = False  # чтобы не дублировалось в root

    if logger.handlers:
        # защита от повторной инициализации
        return

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,   # ~1 MB
        backupCount=5,
        encoding="utf-8",
    )

    if log_format_type == "plain":
        formatter = logging.Formatter(
            fmt="%(levelname)s %(asctime)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # задел под JSON, если понадобится
        formatter = logging.Formatter(
            fmt="%(levelname)s %(asctime)s %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

