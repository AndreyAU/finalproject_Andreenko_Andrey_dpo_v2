"""
Currency hierarchy for ValutaTrade Hub.

Содержит:
- абстрактный базовый класс Currency;
- реализации FiatCurrency и CryptoCurrency;
- реестр валют и фабричный метод get_currency().
"""

from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактная базовая валюта.
    """

    def __init__(self, name: str, code: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Currency name must be a non-empty string")

        if (
            not isinstance(code, str)
            or not code.isupper()
            or not (2 <= len(code) <= 5)
            or " " in code
        ):
            raise ValueError("Currency code must be uppercase, 2–5 chars, no spaces")

        self.name: str = name
        self.code: str = code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Строковое представление валюты для UI и логов.
        """
        raise NotImplementedError


class FiatCurrency(Currency):
    """
    Фиатная валюта.
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("Issuing country must be a non-empty string")

        super().__init__(name=name, code=code)
        self.issuing_country: str = issuing_country

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    """
    Криптовалюта.
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Algorithm must be a non-empty string")

        if not isinstance(market_cap, (int, float)) or market_cap <= 0:
            raise ValueError("Market cap must be a positive number")

        super().__init__(name=name, code=code)
        self.algorithm: str = algorithm
        self.market_cap: float = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# --- Currency registry ---

_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency(
        name="US Dollar",
        code="USD",
        issuing_country="United States",
    ),
    "EUR": FiatCurrency(
        name="Euro",
        code="EUR",
        issuing_country="Eurozone",
    ),
    "BTC": CryptoCurrency(
        name="Bitcoin",
        code="BTC",
        algorithm="SHA-256",
        market_cap=1.12e12,
    ),
    "ETH": CryptoCurrency(
        name="Ethereum",
        code="ETH",
        algorithm="Ethash",
        market_cap=4.5e11,
    ),
}


def get_currency(code: str) -> Currency:
    """
    Фабричный метод получения валюты по коду.

    :param code: валютный код (например, USD, BTC)
    :raises CurrencyNotFoundError: если код неизвестен
    """
    if not isinstance(code, str):
        raise CurrencyNotFoundError(code)

    normalized_code = code.upper()

    currency = _CURRENCY_REGISTRY.get(normalized_code)
    if currency is None:
        raise CurrencyNotFoundError(normalized_code)

    return currency

