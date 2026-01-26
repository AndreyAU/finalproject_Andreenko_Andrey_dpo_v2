import hashlib
import secrets
from datetime import datetime


# =========================
# User
# =========================

class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime | None = None
    ):
        if not username or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым")

        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date or datetime.now()

    @staticmethod
    def generate_salt() -> str:
        return secrets.token_hex(16)

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        if not isinstance(password, str) or len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self._hashed_password == self.hash_password(password, self._salt)

    def change_password(self, new_password: str) -> None:
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self.hash_password(new_password, self._salt)

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date


# =========================
# Wallet
# =========================

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        if not currency_code or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        self.currency_code = currency_code.upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным числом")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом")
        if amount > self._balance:
            raise ValueError(
                f"Недостаточно средств: доступно {self._balance}, требуется {amount}"
            )
        self._balance -= float(amount)

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self._balance:.4f}"


# =========================
# Portfolio
# =========================

class Portfolio:
    # Заглушка курсов (разрешено ТЗ)
    EXCHANGE_RATES = {
        "USD": 1.0,
        "EUR": 1.08,
        "BTC": 59000.0,
        "ETH": 3700.0
    }

    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = wallets or {}

    # ---------- getters ----------

    @property
    def user(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        # возвращаем КОПИЮ
        return dict(self._wallets)

    # ---------- business methods ----------

    def add_currency(self, currency_code: str) -> Wallet:
        if not currency_code or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        code = currency_code.upper()

        if code in self._wallets:
            raise ValueError(f"Кошелёк {code} уже существует")

        wallet = Wallet(code)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        return self._wallets.get(currency_code.upper())

    def get_total_value(self, base_currency: str = "USD") -> float:
        base = base_currency.upper()

        if base not in self.EXCHANGE_RATES:
            raise ValueError(f"Неизвестная базовая валюта {base}")

        total = 0.0

        for code, wallet in self._wallets.items():
            if code not in self.EXCHANGE_RATES:
                continue

            value_in_usd = wallet.balance * self.EXCHANGE_RATES[code]
            total += value_in_usd

        # если база не USD — пересчитываем
        if base != "USD":
            total /= self.EXCHANGE_RATES[base]

        return round(total, 2)

