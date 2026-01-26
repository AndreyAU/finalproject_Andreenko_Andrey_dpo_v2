from pathlib import Path

from valutatrade_hub.core.usecases import (
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    CURRENT_USER_FILE,
    _get_current_user
)

# =========================
# session reset on start
# =========================

if Path(CURRENT_USER_FILE).exists():
    Path(CURRENT_USER_FILE).unlink()


# =========================
# helpers
# =========================

def print_menu():
    print("\nДобро пожаловать в ValutaTrade Hub!")
    print("---------------------------------")
    print("1. Регистрация")
    print("2. Вход")
    print("3. Показать портфель")
    print("4. Купить валюту")
    print("5. Продать валюту")
    print("0. Выход")
    print("---------------------------------")


def _require_login() -> bool:
    try:
        _get_current_user()
        return True
    except Exception as e:
        print(f"\nОшибка: {e}")
        return False


def _read_amount() -> float | None:
    raw = input("Количество: ").strip()
    try:
        value = float(raw)
    except ValueError:
        print("\nОшибка: 'amount' должен быть числом")
        return None

    if value <= 0:
        print("\nОшибка: 'amount' должен быть положительным числом")
        return None

    return value


# =========================
# handlers
# =========================

def handle_register():
    print("\nРегистрация нового пользователя")
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        user = register_user(username, password)
        print(f"\nПользователь '{user['username']}' зарегистрирован (id={user['user_id']})")
    except Exception as e:
        print(f"\nОшибка регистрации: {e}")


def handle_login():
    print("\nВход в систему")
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        user = login_user(username, password)
        print(f"\nВы вошли как '{user['username']}'")
    except Exception as e:
        print(f"\nОшибка входа: {e}")


def handle_show_portfolio():
    if not _require_login():
        return

    base = input("Базовая валюта (по умолчанию USD): ").strip() or "USD"

    try:
        r = show_portfolio(base)

        print(f"\nПортфель пользователя '{r['username']}' (база: {r['base']}):")
        print("---------------------------------")

        if not r["wallets"]:
            print("Портфель пуст")
            return

        for w in r["wallets"]:
            print(
                f"- {w['currency']}: {w['balance']:.4f}  → "
                f"{w['value_in_base']:.2f} {r['base']}"
            )

        print("---------------------------------")
        print(f"ИТОГО: {r['total']:.2f} {r['base']}")

    except Exception as e:
        print(f"\nОшибка: {e}")


def handle_buy():
    if not _require_login():
        return

    print("\nПокупка валюты")
    currency = input("Код валюты (например BTC): ").strip()
    amount = _read_amount()
    if amount is None:
        return

    try:
        r = buy_currency(currency, amount)

        print(
            f"\nПокупка выполнена: {r['amount']:.4f} {r['currency']} "
            f"по курсу {r['rate']} {r['base']}/{r['currency']}"
        )
        print(f"- {r['currency']}: было {r['before']:.4f} → стало {r['after']:.4f}")
        print(f"Оценочная стоимость покупки: {r['cost']:.2f} {r['base']}")

    except Exception as e:
        print(f"\nОшибка покупки: {e}")


def handle_sell():
    if not _require_login():
        return

    print("\nПродажа валюты")
    currency = input("Код валюты (например BTC): ").strip()
    amount = _read_amount()
    if amount is None:
        return

    try:
        r = sell_currency(currency, amount)

        print(
            f"\nПродажа выполнена: {r['amount']:.4f} {r['currency']} "
            f"по курсу {r['rate']} {r['base']}/{r['currency']}"
        )
        print(f"- {r['currency']}: было {r['before']:.4f} → стало {r['after']:.4f}")
        print(f"Оценочная выручка: {r['proceeds']:.2f} {r['base']}")

    except Exception as e:
        print(f"\nОшибка продажи: {e}")


# =========================
# main loop
# =========================

def main_menu():
    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            handle_register()
        elif choice == "2":
            handle_login()
        elif choice == "3":
            handle_show_portfolio()
        elif choice == "4":
            handle_buy()
        elif choice == "5":
            handle_sell()
        elif choice == "0":
            print("\nДо свидания!")
            break
        else:
            print("\nНеизвестная команда")


if __name__ == "__main__":
    main_menu()

