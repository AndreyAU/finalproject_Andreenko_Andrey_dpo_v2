import json
import os
import tempfile
from pathlib import Path
from typing import Any

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """
    Хранилище курсов валют Parser Service.

    Отвечает за:
    - snapshot текущих курсов (rates.json)
    - append-only журнал истории (exchange_rates.json)

    НЕ содержит бизнес-логики:
    - не проверяет TTL
    - не делает reverse-rate
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()

        self.rates_path = Path(self.config.RATES_FILE_PATH)
        self.history_path = Path(self.config.HISTORY_FILE_PATH)

        # гарантируем, что каталог data/ существует
        self.rates_path.parent.mkdir(parents=True, exist_ok=True)

        # exchange_rates.json всегда существует и всегда список
        if not self.history_path.exists():
            self._atomic_write(self.history_path, [])

    # =========================
    # public API
    # =========================

    def save_snapshot(self, rates: dict[str, float], updated_at: str) -> None:
        """
        Сохраняет snapshot текущих курсов в rates.json
        и добавляет записи в exchange_rates.json (append-only).

        rates: {"BTC_USD": 59337.21, ...}
        updated_at: ISO-UTC timestamp
        """
        snapshot = {
            "pairs": {},
            "last_refresh": updated_at,
        }

        for pair, rate in rates.items():
            source = self._detect_source(pair)

            snapshot["pairs"][pair] = {
                "rate": rate,
                "updated_at": updated_at,
                "source": source,
            }

            self._append_history(
                pair=pair,
                rate=rate,
                timestamp=updated_at,
                source=source,
            )

        self._atomic_write(self.rates_path, snapshot)

    # =========================
    # history helpers
    # =========================

    def _append_history(
        self,
        pair: str,
        rate: float,
        timestamp: str,
        source: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """
        Добавляет запись в exchange_rates.json (append-only).
        """
        from_currency, to_currency = pair.split("_", 1)

        record = {
            "id": f"{pair}_{timestamp}",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "timestamp": timestamp,
            "source": source,
            "meta": meta or {},
        }

        history = self._load_history()
        history.append(record)

        self._atomic_write(self.history_path, history)

    # =========================
    # internal helpers
    # =========================

    def _load_history(self) -> list[dict[str, Any]]:
        """
        Загружает историю курсов.

        Гарантии:
        - всегда возвращает list
        - пустой файл → []
        - битый формат → []
        """
        if not self.history_path.exists():
            return []

        if self.history_path.stat().st_size == 0:
            return []

        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        return data

    def _atomic_write(self, path: Path, data: Any) -> None:
        """
        Атомарная запись JSON:
        временный файл → rename
        """
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
        ) as tmp:
            json.dump(data, tmp, indent=4, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_name = tmp.name

        os.replace(temp_name, path)

    def _detect_source(self, pair: str) -> str:
        """
        Определяет источник курса по валютной паре.
        """
        if pair.startswith(("BTC_", "ETH_", "SOL_")):
            return "CoinGecko"
        return "ExchangeRate-API"

