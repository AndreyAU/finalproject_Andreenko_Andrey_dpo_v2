from pathlib import Path
from typing import Any


class SettingsLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self):
        self._settings = {
            "DATA_DIR": Path("data"),
            "RATES_TTL_SECONDS": 300,
            "DEFAULT_BASE_CURRENCY": "USD",
            "LOG_LEVEL": "INFO",
            "LOG_DIR": Path("logs"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def reload(self):
        self._init_settings()

