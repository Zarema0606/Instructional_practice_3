"""
Точка входа в приложение учета заявок на ремонт бытовой техники.
Содержит:
- инициализацию БД
- импорт CSV-данных
- генерацию QR-кода
- авторизацию пользователей
"""

import sys
import os
import traceback

# ------------------------------------------------------------------
# Добавляем корень проекта в PYTHONPATH
# ------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ------------------------------------------------------------------
# Импорты внутренних модулей
# ------------------------------------------------------------------

from src.database import get_database
from src.gui import ServiceCenterApp
from src.login import LoginWindow
from src.qr_generator import generate_qr
from src.import_csv import (
    import_users,
    import_requests,
    import_comments
)

# ------------------------------------------------------------------
# Пути к данным
# ------------------------------------------------------------------

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
USERS_CSV = os.path.join(DATA_DIR, "inputDataUsers.csv")
REQUESTS_CSV = os.path.join(DATA_DIR, "inputDataRequests.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "inputDataComments.csv")


# ------------------------------------------------------------------
# Импорт начальных данных
# ------------------------------------------------------------------

def import_initial_data():
    """
    Импорт исходных данных из CSV-файлов.
    Выполняется безопасно (без дублирования данных).
    """
    try:
        if os.path.exists(USERS_CSV):
            import_users(USERS_CSV)

        if os.path.exists(REQUESTS_CSV):
            import_requests(REQUESTS_CSV)

        if os.path.exists(COMMENTS_CSV):
            import_comments(COMMENTS_CSV)

    except Exception as e:
        print("Ошибка при импорте CSV-данных:")
        print(e)
        traceback.print_exc()


# ------------------------------------------------------------------
# Инициализация приложения
# ------------------------------------------------------------------

def initialize_application():
    """
    Первичная инициализация:
    - база данных
    - импорт данных
    - QR-код
    """
    # Инициализация БД (создание таблиц)
    get_database()

    # Импорт CSV
    import_initial_data()

    # Генерация QR-кода для оценки качества
    try:
        qr_path = os.path.join(PROJECT_ROOT, "quality_qr.png")
        if not os.path.exists(qr_path):
            generate_qr(qr_path)
    except Exception as e:
        print("Не удалось сгенерировать QR-код:", e)


# ------------------------------------------------------------------
# Главная функция
# ------------------------------------------------------------------

def main():
    """
    Главная функция запуска приложения.
    """
    try:
        # Инициализация
        initialize_application()

        # Создаем главное окно (пока скрыто)
        app = ServiceCenterApp()
        app.withdraw()

        # Окно авторизации
        login_window = LoginWindow(app)
        app.wait_window(login_window)

        # Если пользователь закрыл окно авторизации — выходим
        if not login_window.result:
            sys.exit(0)

        # Передаем данные пользователя в GUI
        app.set_current_user(login_window.result)

        # Показываем главное окно
        app.deiconify()
        app.mainloop()

    except Exception as e:
        print("Критическая ошибка при запуске приложения:")
        print(e)
        traceback.print_exc()
        sys.exit(1)


# ------------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------------

if __name__ == "__main__":
    main()

