from valutatrade_hub.core.usecases import (
    register_user,
    login_user,
    show_portfolio
)


def print_menu():
    print("\nДобро пожаловать в ValutaTrade Hub!")
    print("---------------------------------")
    print("1. Регистрация")
    print("2. Вход")
    print("3. Показать портфель")
    print("0. Выход")
    print("---------------------------------")


def handle_register():
    print("\nРегистрация нового пользователя")
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()

    try:
        user = register_user(username, password)
        print(f"\nПользователь '{user['username']}' зарегистрирован (id={user['user_id']})")
        print("Теперь выполните вход.")
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
    print("\nПоказ портфеля")

    base = input("Базовая валюта (по умолчанию USD): ").strip().upper()
    if not base:
        base = "USD"

    try:
        result = show_portfolio(base)

        print(f"\nПортфель пользователя '{result['username']}' (база: {result['base']}):")
        print("---------------------------------")

        if not result["wallets"]:
            print("Портфель пуст")
            return

        for w in result["wallets"]:
            print(
                f"- {w['currency']}: {w['balance']:.4f}  → {w['value_in_base']:.2f} {result['base']}"
            )

        print("---------------------------------")
        print(f"ИТОГО: {result['total']:.2f} {result['base']}")

    except Exception as e:
        print(f"\nОшибка: {e}")


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
        elif choice == "0":
            print("\nДо свидания!")
            break
        else:
            print("\nНеизвестная команда. Попробуйте ещё раз.")


if __name__ == "__main__":
    main_menu()

