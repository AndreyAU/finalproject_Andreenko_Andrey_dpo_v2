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


# -------------------------
# Вспомогательные проверки
# -------------------------

def _validate_code(code: str) -> str:
    """
    Проверка кода валюты.

    Инварианты:
    - строка
    - 2–5 символов
    - верхний регистр
    - без пробелов
    """
    if not isinstance(code, str):
        raise ValueError

    if not code or " " in code or not (2 <= len(code) <= 5):
        raise ValueError

    if code != code.upper():
        raise ValueError

    return code


def _validate_non_empty_str(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError


# -------------------------
# Базовый класс
# -------------------------

class Currency(ABC):
    """
    Абстрактная базовая валюта.
    """

    def __init__(self, name: str, code: str):
        _validate_non_empty_str(name)
        validated_code = _validate_code(code)

        self.name: str = name
        self.code: str = validated_code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Строковое представление валюты для UI и логов.
        """
        raise NotImplementedError


# -------------------------
# Наследники
# -------------------------

class FiatCurrency(Currency):
    """
    Фиатная валюта.
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        _validate_non_empty_str(issuing_country)
        super().__init__(name=name, code=code)

        self.issuing_country: str = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Криптовалюта.
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        _validate_non_empty_str(algorithm)
        if not isinstance(market_cap, (int, float)):
            raise ValueError

        super().__init__(name=name, code=code)

        self.algorithm: str = algorithm
        self.market_cap: float = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# -------------------------
# Реестр валют
# -------------------------

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
    :raises CurrencyNotFoundError: если код неизвестен или некорректен
    """
    try:
        validated_code = _validate_code(code)
    except Exception:
        raise CurrencyNotFoundError(code)

    currency = _CURRENCY_REGISTRY.get(validated_code)
    if currency is None:
        raise CurrencyNotFoundError(validated_code)

    return currency

