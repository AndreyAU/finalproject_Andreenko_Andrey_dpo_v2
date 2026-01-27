"""
Domain-specific exceptions for ValutaTrade Hub.

Все исключения проекта, которые должны:
- иметь понятные сообщения для пользователя;
- использоваться в бизнес-логике и CLI;
- не зависеть от инфраструктуры (CLI, JSON, API).
"""


class ValutaTradeError(Exception):
    """
    Базовое исключение проекта.
    Нужно для группового перехвата ошибок домена.
    """
    pass


class CurrencyNotFoundError(ValutaTradeError):
    """
    Выбрасывается, если валюта с указанным кодом не поддерживается.
    """

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class InsufficientFundsError(ValutaTradeError):
    """
    Выбрасывается при попытке продать/списать больше средств,
    чем доступно в кошельке.
    """

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(message)


class ApiRequestError(ValutaTradeError):
    """
    Ошибка при обращении к внешнему API (курсы валют).
    Используется в слое получения курсов.
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")

