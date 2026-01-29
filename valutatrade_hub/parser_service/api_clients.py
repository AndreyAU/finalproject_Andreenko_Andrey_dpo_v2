import time
import requests
from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """
    Абстрактный клиент внешнего API курсов валют.
    Все конкретные клиенты обязаны реализовать единый интерфейс.
    """

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """
        Получить курсы валют.

        Возвращает:
            dict[str, float]: словарь вида {"BTC_USD": 59337.21, ...}
        """
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    """
    Клиент CoinGecko для получения курсов криптовалют (X -> USD).

    Использует endpoint /simple/price.
    Возвращает курсы в формате: {"BTC_USD": 59337.21, ...}
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()

    def fetch_rates(self) -> dict[str, float]:
        ids = [
            self.config.CRYPTO_ID_MAP[code]
            for code in self.config.CRYPTO_CURRENCIES
            if code in self.config.CRYPTO_ID_MAP
        ]

        if not ids:
            return {}

        params = {
            "ids": ",".join(ids),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        try:
            start = time.monotonic()
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(
                f"CoinGecko request failed: {e}"
            ) from e

        if response.status_code != 200:
            raise ApiRequestError(
                f"CoinGecko API error: status={response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as e:
            raise ApiRequestError(
                "CoinGecko response is not valid JSON"
            ) from e

        result: dict[str, float] = {}

        for code, cg_id in self.config.CRYPTO_ID_MAP.items():
            if cg_id not in data:
                continue

            price = data[cg_id].get(self.config.BASE_CURRENCY.lower())
            if not isinstance(price, (int, float)):
                continue

            pair_key = f"{code}_{self.config.BASE_CURRENCY}"
            result[pair_key] = float(price)

        return result


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент ExchangeRate-API для получения курсов фиатных валют (X -> USD).

    Использует endpoint /v6/<API_KEY>/latest/USD
    Возвращает курсы в формате: {"EUR_USD": 0.927, ...}
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()

    def fetch_rates(self) -> dict[str, float]:
        # 🔒 Проверка ключа ТОЛЬКО в момент запроса (по ТЗ и архитектуре)
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("EXCHANGERATE_API_KEY is not set")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )

        try:
            start = time.monotonic()
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(
                f"ExchangeRate-API request failed: {e}"
            ) from e

        if response.status_code != 200:
            raise ApiRequestError(
                f"ExchangeRate-API error: status={response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as e:
            raise ApiRequestError(
                "ExchangeRate-API response is not valid JSON"
            ) from e

        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API returned error: {data}"
            )

        rates = data.get("conversion_rates")
        if not isinstance(rates, dict):
            raise ApiRequestError(
                "ExchangeRate-API response has no 'conversion_rates'"
            )

        result: dict[str, float] = {}

        for code in self.config.FIAT_CURRENCIES:
            rate = rates.get(code)
            if not isinstance(rate, (int, float)):
                continue

            pair_key = f"{code}_{self.config.BASE_CURRENCY}"
            result[pair_key] = float(rate)

        return result

