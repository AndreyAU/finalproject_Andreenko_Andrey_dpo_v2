from pathlib import Path

from valutatrade_hub.logging_config import setup_logging

from valutatrade_hub.core.usecases import (
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    get_rate,
    CURRENT_USER_FILE,
    _get_current_user
)
from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
    ApiRequestError,
    ValutaTradeError,
)

# инициализация логирования (ОДИН РАЗ при старте CLI)
setup_logging()

# сброс сессии при старте
if Path(CURRENT_USER_FILE).exists():
    Path(CURRENT_USER_FILE).unlink()


def print_menu():
    print("\nДобро пожаловать в ValutaTrade Hub!")
    print("---------------------------------")
    print("1. Регистрация")
    print("2. Вход")
    print("3. Показать портфель")
    print("4. Купить валюту")
    print("5. Продать валюту")
    print("6. Получить курс валют")
    print("0. Выход")
    print("---------------------------------")


def _require_login() -> bool:
    try:
        _get_current_user()
        return True
    except ValutaTradeError as e:
        print(f"\n❌ Требуется вход: {e}")
        return False


def handle_register():
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        user = register_user(username, password)
        print(f"\n✅ Пользователь '{user['username']}' зарегистрирован (id={user['user_id']})")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка регистрации: {e}")


def handle_login():
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        user = login_user(username, password)
        print(f"\n✅ Вы вошли как '{user['username']}'")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка входа: {e}")


def handle_show_portfolio():
    if not _require_login():
        return

    base = input("Базовая валюта (по умолчанию USD): ").strip() or "USD"

    try:
        r = show_portfolio(base)
        print(f"\n📊 Портфель пользователя '{r['username']}' (база: {r['base']}):")

        if not r["wallets"]:
            print("Портфель пуст")
            return

        for w in r["wallets"]:
            print(
                f"- {w['currency']}: {w['balance']:.4f} "
                f"→ {w['value_in_base']:.2f} {r['base']}"
            )

        print("---------------------------------")
        print(f"ИТОГО: {r['total']:.2f} {r['base']}")

    except CurrencyNotFoundError as e:
        print(f"\n❌ Неизвестная валюта: {e}")
    except ApiRequestError as e:
        print(f"\n❌ Не удалось рассчитать портфель: {e}")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка: {e}")


def handle_buy():
    if not _require_login():
        return

    currency = input("Код валюты (например BTC): ").strip()
    amount_raw = input("Количество: ").strip()

    try:
        amount = float(amount_raw)
        r = buy_currency(currency, amount)

        print(f"\n✅ Покупка выполнена")
        print(
            f"- Куплено: {r['amount']:.4f} {r['currency']} "
            f"по курсу {r['rate']} {r['base']}/{r['currency']}"
        )
        print(f"- Баланс: {r['before']:.4f} → {r['after']:.4f}")
        print(f"- Стоимость: {r['cost']:.2f} {r['base']}")

    except ValueError:
        print("\n❌ Некорректная сумма: amount должен быть числом")
    except CurrencyNotFoundError as e:
        print(f"\n❌ Неизвестная валюта: {e}")
    except ApiRequestError as e:
        print(f"\n❌ Курс недоступен: {e}")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка покупки: {e}")


def handle_sell():
    if not _require_login():
        return

    currency = input("Код валюты (например BTC): ").strip()
    amount_raw = input("Количество: ").strip()

    try:
        amount = float(amount_raw)
        r = sell_currency(currency, amount)

        print(f"\n✅ Продажа выполнена")
        print(
            f"- Продано: {r['amount']:.4f} {r['currency']} "
            f"по курсу {r['rate']} {r['base']}/{r['currency']}"
        )
        print(f"- Баланс: {r['before']:.4f} → {r['after']:.4f}")
        print(f"- Выручка: {r['proceeds']:.2f} {r['base']}")

    except ValueError:
        print("\n❌ Некорректная сумма: amount должен быть числом")
    except CurrencyNotFoundError as e:
        print(f"\n❌ Неизвестная валюта: {e}")
    except InsufficientFundsError as e:
        print(f"\n❌ Недостаточно средств: {e}")
    except ApiRequestError as e:
        print(f"\n❌ Курс недоступен: {e}")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка продажи: {e}")


def handle_get_rate():
    print("\nПолучение курса валют")
    from_cur = input("Из валюты (например USD): ").strip()
    to_cur = input("В валюту (например BTC): ").strip()

    try:
        r = get_rate(from_cur, to_cur)
        print(
            f"\n📈 Курс {r['from']} → {r['to']}: {r['rate']} "
            f"(обновлено: {r['updated_at']})"
        )

        if r["reverse_rate"] is not None:
            print(
                f"Обратный курс {r['to']} → {r['from']}: {r['reverse_rate']}"
            )

    except CurrencyNotFoundError as e:
        print(f"\n❌ Неизвестная валюта: {e}")
    except ApiRequestError as e:
        print(f"\n❌ Курс недоступен: {e}")
    except ValutaTradeError as e:
        print(f"\n❌ Ошибка: {e}")


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
        elif choice == "6":
            handle_get_rate()
        elif choice == "0":
            print("\nДо свидания!")
            break
        else:
            print("\n❌ Неизвестная команда")


if __name__ == "__main__":
    main_menu()

