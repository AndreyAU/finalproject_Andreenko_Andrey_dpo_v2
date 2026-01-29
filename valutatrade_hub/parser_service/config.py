import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ParserConfig:
    """
    Конфигурация Parser Service.

    Содержит только параметры и константы.
    Не выполняет валидаций, IO или бизнес-логики.
    """

    # =========================
    # API keys (env only)
    # =========================

    EXCHANGERATE_API_KEY: str | None = os.getenv("EXCHANGERATE_API_KEY")

    # =========================
    # API endpoints
    # =========================

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # =========================
    # Currency settings
    # =========================

    # Вариант A: сохраняем ТОЛЬКО X -> USD
    BASE_CURRENCY: str = "USD"

    FIAT_CURRENCIES: tuple[str, ...] = (
        "EUR",
        "GBP",
        "RUB",
    )

    CRYPTO_CURRENCIES: tuple[str, ...] = (
        "BTC",
        "ETH",
        "SOL",
    )

    # CoinGecko использует ID, а не тикеры
    CRYPTO_ID_MAP: dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # =========================
    # File paths
    # =========================

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # =========================
    # Network settings
    # =========================

    REQUEST_TIMEOUT: int = 10

