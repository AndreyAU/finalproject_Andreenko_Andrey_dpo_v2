import json
from datetime import datetime, timedelta

from valutatrade_hub.core.models import User
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ValutaTradeError,
    InsufficientFundsError,
    ApiRequestError,
)
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action


# =========================
# settings
# =========================

settings = SettingsLoader()

USERS_FILE = settings.get("USERS_FILE")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE")
CURRENT_USER_FILE = settings.get("CURRENT_USER_FILE")
RATES_FILE = settings.get("RATES_FILE")

RATES_TTL_SECONDS = settings.get("RATES_TTL_SECONDS")
DEFAULT_BASE_CURRENCY = settings.get("DEFAULT_BASE_CURRENCY")


# =========================
# helpers (JSON safe ops)
# =========================

def _load_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _get_current_user():
    data = _load_json(CURRENT_USER_FILE)
    if not data:
        raise ValutaTradeError("Сначала выполните login")
    return data


def _is_fresh(ts: str) -> bool:
    updated = datetime.fromisoformat(ts)
    return datetime.now() - updated <= timedelta(seconds=RATES_TTL_SECONDS)


def _load_rates() -> dict:
    data = _load_json(RATES_FILE)
    return data or {}


# =========================
# Parser Service STUB
# =========================

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
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


# =========================
# portfolio helpers
# =========================

def _get_user_portfolio(user_id: int):
    portfolios = _load_json(PORTFOLIOS_FILE) or []
    for p in portfolios:
        if p["user_id"] == user_id:
            return p, portfolios
    raise ValutaTradeError("Портфель пользователя не найден")


# =========================
# register / login
# =========================

def register_user(username: str, password: str) -> dict:
    if not username or not username.strip():
        raise ValutaTradeError("Имя пользователя не может быть пустым")
    if not isinstance(password, str) or len(password) < 4:
        raise ValutaTradeError("Пароль должен быть не короче 4 символов")

    users = _load_json(USERS_FILE) or []

    if any(u["username"] == username for u in users):
        raise ValutaTradeError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    salt = User.generate_salt()
    hashed_password = User.hash_password(password, salt)

    users.append({
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat(),
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
        raise ValutaTradeError(f"Пользователь '{username}' не найден")

    user = User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        hashed_password=user_data["hashed_password"],
        salt=user_data["salt"],
        registration_date=datetime.fromisoformat(user_data["registration_date"]),
    )

    if not user.verify_password(password):
        raise ValutaTradeError("Неверный пароль")

    current_user = {"user_id": user.user_id, "username": user.username}
    _save_json(CURRENT_USER_FILE, current_user)
    return current_user


# =========================
# get-rate (3.5) — FIXED
# =========================

def get_rate(from_currency: str, to_currency: str) -> dict:
    from_cur = get_currency(from_currency)
    to_cur = get_currency(to_currency)

    rates = _load_rates()
    direct_key = f"{from_cur.code}_{to_cur.code}"
    reverse_key = f"{to_cur.code}_{from_cur.code}"

    # 1) Прямой курс в кэше и свежий
    if direct_key in rates and _is_fresh(rates[direct_key]["updated_at"]):
        rate = rates[direct_key]["rate"]
        updated = rates[direct_key]["updated_at"]

    else:
        # 2) Пробуем STUB для прямого курса
        stub = _parser_stub(from_cur.code, to_cur.code)
        if stub:
            rates[direct_key] = stub
            rates["last_refresh"] = stub["updated_at"]
            _save_json(RATES_FILE, rates)
            rate = stub["rate"]
            updated = stub["updated_at"]

        # 3) Пробуем обратный курс (из кэша или STUB)
        elif reverse_key in rates and _is_fresh(rates[reverse_key]["updated_at"]):
            reverse_rate = rates[reverse_key]["rate"]
            rate = round(1 / reverse_rate, 8)
            updated = rates[reverse_key]["updated_at"]

            rates[direct_key] = {
                "rate": rate,
                "updated_at": updated,
            }
            _save_json(RATES_FILE, rates)

        else:
            reverse_stub = _parser_stub(to_cur.code, from_cur.code)
            if not reverse_stub:
                raise ApiRequestError(
                    f"курс {from_cur.code}→{to_cur.code} недоступен"
                )

            reverse_rate = reverse_stub["rate"]
            rate = round(1 / reverse_rate, 8)
            updated = reverse_stub["updated_at"]

            rates[reverse_key] = reverse_stub
            rates[direct_key] = {
                "rate": rate,
                "updated_at": updated,
            }
            rates["last_refresh"] = updated
            _save_json(RATES_FILE, rates)

    reverse_rate = rates.get(reverse_key, {}).get("rate")

    return {
        "from": from_cur.code,
        "to": to_cur.code,
        "rate": rate,
        "reverse_rate": reverse_rate,
        "updated_at": updated,
    }


# =========================
# buy / sell (3.5)
# =========================

@log_action("BUY", verbose=True)
def buy_currency(currency: str, amount: float, base_currency: str = None) -> dict:
    user_id = _get_current_user()["user_id"]

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValutaTradeError("'amount' должен быть положительным числом")

    base_currency = base_currency or DEFAULT_BASE_CURRENCY

    cur = get_currency(currency)
    base = get_currency(base_currency)

    rate = get_rate(cur.code, base.code)["rate"]

    portfolio, portfolios = _get_user_portfolio(user_id)
    wallets = portfolio.setdefault("wallets", {})

    wallet = wallets.setdefault(cur.code, {"balance": 0.0})

    before = wallet["balance"]
    wallet["balance"] = round(before + amount, 4)

    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "user_id": user_id,
        "currency": cur.code,
        "amount": amount,
        "rate": rate,
        "base": base.code,
        "before": before,
        "after": wallet["balance"],
        "cost": round(amount * rate, 2),
    }


@log_action("SELL", verbose=True)
def sell_currency(currency: str, amount: float, base_currency: str = None) -> dict:
    user_id = _get_current_user()["user_id"]

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValutaTradeError("'amount' должен быть положительным числом")

    base_currency = base_currency or DEFAULT_BASE_CURRENCY

    cur = get_currency(currency)
    base = get_currency(base_currency)

    portfolio, portfolios = _get_user_portfolio(user_id)
    wallets = portfolio.get("wallets", {})

    if cur.code not in wallets:
        raise ValutaTradeError(f"У вас нет кошелька '{cur.code}'")

    wallet = wallets[cur.code]
    before = wallet["balance"]

    if amount > before:
        raise InsufficientFundsError(
            available=round(before, 4),
            required=round(amount, 4),
            code=cur.code,
        )

    rate = get_rate(cur.code, base.code)["rate"]
    wallet["balance"] = round(before - amount, 4)

    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "user_id": user_id,
        "currency": cur.code,
        "amount": amount,
        "rate": rate,
        "base": base.code,
        "before": before,
        "after": wallet["balance"],
        "proceeds": round(amount * rate, 2),
    }


# =========================
# show portfolio
# =========================

def show_portfolio(base_currency: str = None) -> dict:
    user = _get_current_user()
    base_currency = base_currency or DEFAULT_BASE_CURRENCY
    base = get_currency(base_currency)

    portfolio, _ = _get_user_portfolio(user["user_id"])
    wallets = portfolio.get("wallets", {})

    result = []
    total = 0.0

    for code, info in wallets.items():
        rate = get_rate(code, base.code)["rate"]
        value = round(info["balance"] * rate, 2)
        total += value

        result.append({
            "currency": code,
            "balance": info["balance"],
            "value_in_base": value,
        })

    return {
        "username": user["username"],
        "base": base.code,
        "wallets": result,
        "total": round(total, 2),
    }

