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


def _load_rates():
    data = _load_json(RATES_FILE)
    if not data:
        raise RuntimeError("Курсы валют недоступны")
    return data


def _get_rate(from_currency: str, to_currency: str) -> float:
    rates = _load_rates()
    key = f"{from_currency}_{to_currency}"
    if key not in rates:
        raise RuntimeError(f"Не удалось получить курс для {from_currency}→{to_currency}")
    return rates[key]["rate"]


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

    users.append({
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat()
    })

    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE) or []
    portfolios.append({
        "user_id": user_id,
        "wallets": {}
    })
    _save_json(PORTFOLIOS_FILE, portfolios)

    return {"user_id": user_id, "username": username}


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
# buy currency
# =========================

def buy_currency(currency: str, amount: float, base_currency: str = "USD") -> dict:
    current_user = _get_current_user()
    user_id = current_user["user_id"]

    if not currency or not isinstance(currency, str):
        raise ValueError("Некорректный код валюты")

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    base_currency = base_currency.upper()

    rate = _get_rate(currency, base_currency)

    # 🔴 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ
    portfolios = _load_json(PORTFOLIOS_FILE) or []

    portfolio = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None
    )
    if not portfolio:
        raise RuntimeError("Портфель пользователя не найден")

    wallets = portfolio.setdefault("wallets", {})

    if currency not in wallets:
        wallets[currency] = {"balance": 0.0}

    before = wallets[currency]["balance"]
    after = before + float(amount)
    wallets[currency]["balance"] = after

    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "currency": currency,
        "amount": amount,
        "rate": rate,
        "base": base_currency,
        "before": before,
        "after": after,
        "cost": round(amount * rate, 2)
    }


# =========================
# show portfolio
# =========================

def show_portfolio(base_currency: str = "USD") -> dict:
    base_currency = base_currency.upper()

    current_user = _get_current_user()
    user_id = current_user["user_id"]
    username = current_user["username"]

    portfolios = _load_json(PORTFOLIOS_FILE) or []
    portfolio = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None
    )
    if not portfolio:
        raise RuntimeError("Портфель пользователя не найден")

    wallets = portfolio.get("wallets", {})

    if not wallets:
        return {
            "username": username,
            "base": base_currency,
            "wallets": [],
            "total": 0.0
        }

    result_wallets = []
    total = 0.0

    for currency, info in wallets.items():
        balance = info["balance"]
        rate = _get_rate(currency, base_currency)
        value = balance * rate
        total += value

        result_wallets.append({
            "currency": currency,
            "balance": balance,
            "value_in_base": round(value, 2)
        })

    return {
        "username": username,
        "base": base_currency,
        "wallets": result_wallets,
        "total": round(total, 2)
    }

