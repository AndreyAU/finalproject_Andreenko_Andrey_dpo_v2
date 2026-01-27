from pathlib import Path
from typing import Any
import tomllib


class SettingsLoader:
    """
    Singleton для загрузки и кеширования конфигурации проекта.

    Выбран способ через __new__, потому что:
    - он проще и читабельнее метаклассов;
    - гарантирует ровно один экземпляр при любых импортах;
    - не усложняет тестирование и отладку.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self) -> None:
        """
        Загружает конфигурацию из pyproject.toml (секция [tool.valutatrade])
        и формирует единый словарь настроек.
        """
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            raise RuntimeError("pyproject.toml не найден")

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        cfg = data.get("tool", {}).get("valutatrade", {})

        data_dir = Path(cfg.get("DATA_DIR", "data"))

        self._settings = {
            # paths
            "DATA_DIR": data_dir,
            "USERS_FILE": data_dir / cfg.get("USERS_FILE", "users.json"),
            "PORTFOLIOS_FILE": data_dir / cfg.get("PORTFOLIOS_FILE", "portfolios.json"),
            "CURRENT_USER_FILE": data_dir / cfg.get("CURRENT_USER_FILE", "current_user.json"),
            "RATES_FILE": data_dir / cfg.get("RATES_FILE", "rates.json"),

            # business rules
            "RATES_TTL_SECONDS": int(cfg.get("RATES_TTL_SECONDS", 300)),
            "DEFAULT_BASE_CURRENCY": cfg.get("DEFAULT_BASE_CURRENCY", "USD"),

            # logging
            "LOG_DIR": Path(cfg.get("LOG_DIR", "logs")),
            "LOG_LEVEL": cfg.get("LOG_LEVEL", "INFO"),
            "LOG_FORMAT": cfg.get("LOG_FORMAT", "plain"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение конфигурации по ключу.
        """
        return self._settings.get(key, default)

    def reload(self) -> None:
        """
        Принудительно перечитать конфигурацию из источника.
        """
        self._load_settings()

