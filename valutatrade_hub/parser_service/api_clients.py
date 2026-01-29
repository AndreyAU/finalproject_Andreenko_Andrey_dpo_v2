from abc import ABC, abstractmethod


class BaseApiClient(ABC):
    """
    Абстрактный клиент внешнего API курсов валют.
    Все конкретные клиенты (CoinGecko, ExchangeRate)
    обязаны реализовать единый интерфейс.
    """

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """
        Получить курсы валют.

        Возвращает:
            dict[str, float]: словарь вида {"BTC_USD": 59337.21, ...}
        """
        raise NotImplementedError

