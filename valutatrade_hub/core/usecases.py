import json
from pathlib import Path
from datetime import datetime

from valutatrade_hub.core.models import User


DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
CURRENT_USER_FILE = DATA_DIR / "current_user.json"
RATES_FILE = DATA_DIR / "rates.json"


# =========================
# helpers
# =========================

def _load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _get_current_user():
    data = _load_json(CURRENT_USER_FILE)
    if not data:
        raise RuntimeError("Сначала выполните login")
    return data  # {user_id, username}


def _get_user_portfolio(user_id: int):
    portfolios = _load_json(PORTFOLIOS_FILE) or []
    for p in portfolios:
        if p["user_id"] == user_id:
            return p
    raise RuntimeError("Портфель пользователя не найден")


# =========================
# register / login
# =========================

def register_user(username: str, password: str) -> dict:
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if not isinstance(password, str) or len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = _load_json(USERS_FILE) or []

    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    salt = User.generate_salt()
    hashed_password = User.hash_password(password, salt)

    new_user = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat()
    }

    users.append(new_user)
    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE) or []
    portfolios.append({
        "user_id": user_id,
        "wallets": {}
    })
    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "user_id": user_id,
        "username": username
    }


def login_user(username: str, password: str) -> dict:
    users = _load_json(USERS_FILE) or []

    user_data = next((u for u in users if u["username"] == username), None)
    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        hashed_password=user_data["hashed_password"],
        salt=user_data["salt"],
        registration_date=datetime.fromisoformat(user_data["registration_date"])
    )

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    current_user = {
        "user_id": user.user_id,
        "username": user.username
    }
    _save_json(CURRENT_USER_FILE, current_user)

    return current_user


# =========================
# show portfolio
# =========================

def show_portfolio(base_currency: str = "USD") -> dict:
    """
    Возвращает структуру данных для отображения портфеля пользователя
    """

    base_currency = base_currency.upper()

    # 1. Проверка логина
    current_user = _get_current_user()
    user_id = current_user["user_id"]
    username = current_user["username"]

    # 2. Загрузка портфеля
    portfolio_data = _get_user_portfolio(user_id)
    wallets_data = portfolio_data.get("wallets", {})

    # 3. Курсы (заглушка по ТЗ)
    exchange_rates = {
        "USD_USD": 1.0,
        "BTC_USD": 59300.0,
        "EUR_USD": 1.07
    }

    result_wallets = []
    total_value = 0.0

    # 4. Пустой портфель
    if not wallets_data:
        return {
            "username": username,
            "base": base_currency,
            "wallets": [],
            "total": 0.0
        }

    # 5. Подсчёт стоимости
    for currency, info in wallets_data.items():
        balance = info.get("balance", 0.0)

        rate_key = f"{currency}_{base_currency}"
        if rate_key not in exchange_rates:
            raise RuntimeError(f"Неизвестная валюта '{currency}'")

        value_in_base = balance * exchange_rates[rate_key]
        total_value += value_in_base

        result_wallets.append({
            "currency": currency,
            "balance": balance,
            "value_in_base": value_in_base
        })

    return {
        "username": username,
        "base": base_currency,
        "wallets": result_wallets,
        "total": total_value
    }

