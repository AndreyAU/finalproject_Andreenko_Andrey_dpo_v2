import json
from pathlib import Path
from datetime import datetime, timedelta

from valutatrade_hub.core.models import User
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError, ApiRequestError

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
CURRENT_USER_FILE = DATA_DIR / "current_user.json"
RATES_FILE = DATA_DIR / "rates.json"

TTL_MINUTES = 5


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
    return data


def _validate_currency(code: str) -> str:
    if not code or not isinstance(code, str):
        raise ValueError("Некорректный код валюты")
    code = code.strip().upper()
    if not code.isascii() or not code.isalpha():
        raise ValueError("Некорректный код валюты")
    return code


def _is_fresh(ts: str) -> bool:
    updated = datetime.fromisoformat(ts)
    return datetime.now() - updated <= timedelta(minutes=TTL_MINUTES)


def _load_rates():
    data = _load_json(RATES_FILE)
    if not data:
        raise RuntimeError("Курсы валют недоступны")
    return data


# ====== Parser Service STUB (по ТЗ) ======

def _parser_stub(from_currency: str, to_currency: str):
    STUB = {
        "BTC_USD": 59337.21,
        "EUR_USD": 1.0786,
        "USD_EUR": 0.9271,
    }

    key = f"{from_currency}_{to_currency}"
    if key not in STUB:
        return None

    return {
        "rate": STUB[key],
        "updated_at": datetime.now().isoformat(timespec="seconds")
    }


def _get_user_portfolio(user_id: int):
    portfolios = _load_json(PORTFOLIOS_FILE) or []
    for p in portfolios:
        if p["user_id"] == user_id:
            return p, portfolios
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

    users.append({
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat()
    })

    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE) or []
    portfolios.append({"user_id": user_id, "wallets": {}})
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

    current_user = {"user_id": user.user_id, "username": user.username}
    _save_json(CURRENT_USER_FILE, current_user)
    return current_user


# =========================
# get-rate (ИЗМЕНЁН)
# =========================

def get_rate(from_currency: str, to_currency: str) -> dict:
    from_cur = get_currency(from_currency)
    to_cur = get_currency(to_currency)

    from_code = from_cur.code
    to_code = to_cur.code

    rates = _load_rates()
    key = f"{from_code}_{to_code}"

    if key in rates and _is_fresh(rates[key]["updated_at"]):
        rate = rates[key]["rate"]
        updated = rates[key]["updated_at"]
    else:
        stub = _parser_stub(from_code, to_code)
        if not stub:
            raise ApiRequestError(
                f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже."
            )

        rates[key] = stub
        rates["last_refresh"] = stub["updated_at"]
        _save_json(RATES_FILE, rates)

        rate = stub["rate"]
        updated = stub["updated_at"]

    reverse_key = f"{to_code}_{from_code}"
    reverse_rate = rates[reverse_key]["rate"] if reverse_key in rates else None

    return {
        "from": from_code,
        "to": to_code,
        "rate": rate,
        "reverse_rate": reverse_rate,
        "updated_at": updated
    }


# =========================
# buy / sell
# =========================

def buy_currency(currency: str, amount: float, base_currency: str = "USD") -> dict:
    user_id = _get_current_user()["user_id"]

    currency = _validate_currency(currency)
    base_currency = _validate_currency(base_currency)

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    rate = get_rate(currency, base_currency)["rate"]

    portfolio, portfolios = _get_user_portfolio(user_id)
    wallets = portfolio.setdefault("wallets", {})

    before = wallets.get(currency, {}).get("balance", 0.0)
    after = round(before + amount, 4)
    wallets[currency] = {"balance": after}

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


def sell_currency(currency: str, amount: float, base_currency: str = "USD") -> dict:
    user_id = _get_current_user()["user_id"]

    currency = _validate_currency(currency)
    base_currency = _validate_currency(base_currency)

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio, portfolios = _get_user_portfolio(user_id)
    wallets = portfolio.get("wallets", {})

    if currency not in wallets:
        raise RuntimeError(f"У вас нет кошелька '{currency}'")

    before = wallets[currency]["balance"]
    if amount > before:
        raise RuntimeError(
            f"Недостаточно средств: доступно {before:.4f} {currency}, требуется {amount:.4f} {currency}"
        )

    rate = get_rate(currency, base_currency)["rate"]
    after = round(before - amount, 4)
    wallets[currency]["balance"] = after

    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "currency": currency,
        "amount": amount,
        "rate": rate,
        "base": base_currency,
        "before": before,
        "after": after,
        "proceeds": round(amount * rate, 2)
    }


# =========================
# show portfolio
# =========================

def show_portfolio(base_currency: str = "USD") -> dict:
    user = _get_current_user()
    user_id = user["user_id"]

    base_currency = _validate_currency(base_currency)

    portfolio, _ = _get_user_portfolio(user_id)
    wallets = portfolio.get("wallets", {})

    result = []
    total = 0.0

    for currency, info in wallets.items():
        balance = info["balance"]
        rate = get_rate(currency, base_currency)["rate"]
        value = round(balance * rate, 2)
        total += value

        result.append({
            "currency": currency,
            "balance": balance,
            "value_in_base": value
        })

    return {
        "username": user["username"],
        "base": base_currency,
        "wallets": result,
        "total": round(total, 2)
    }

