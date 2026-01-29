"""
Модуль для работы с базой данных SQLite.
Реализует CRUD-операции и статистику для системы учета заявок.
"""
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """
    Класс управления базой данных заявок на ремонт.
    """

    def __init__(self, db_path: str = "data/service_center.db"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._initialize_database()

    # =========================
    # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
    # =========================

    def _initialize_database(self) -> None:
        """
        Создание структуры БД при первом запуске.
        """
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()

            self.cursor.execute("PRAGMA foreign_keys = ON")

            # ---------- ЗАЯВКИ ----------
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_date TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    device_model TEXT NOT NULL,
                    problem_description TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    client_phone TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Новая',
                    master_name TEXT,
                    deadline TEXT,
                    completion_date TEXT,
                    updated_date TEXT
                )
            """)

            # ---------- КОММЕНТАРИИ ----------
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    comment_text TEXT NOT NULL,
                    parts_ordered TEXT,
                    added_date TEXT NOT NULL,
                    author TEXT NOT NULL,
                    FOREIGN KEY (request_id)
                        REFERENCES requests(id)
                        ON DELETE CASCADE
                )
            """)

            # ---------- ПОЛЬЗОВАТЕЛИ ----------
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT NOT NULL
                )
            """)

            # ---------- ИНДЕКСЫ ----------
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)"
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_client ON requests(client_name)"
            )

            self.connection.commit()
            logger.info("База данных успешно инициализирована")

        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    # =========================
    # CRUD ЗАЯВОК
    # =========================

    def add_request(
        self,
        device_type: str,
        device_model: str,
        problem_description: str,
        client_name: str,
        client_phone: str,
        deadline: Optional[str] = None
    ) -> int:
        """
        Добавление новой заявки.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute("""
                INSERT INTO requests (
                    created_date,
                    device_type,
                    device_model,
                    problem_description,
                    client_name,
                    client_phone,
                    status,
                    deadline,
                    updated_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                current_time,
                device_type,
                device_model,
                problem_description,
                client_name,
                client_phone,
                "Новая",
                deadline,
                current_time
            ))

            self.connection.commit()
            request_id = self.cursor.lastrowid
            logger.info(f"Создана заявка №{request_id}")
            return request_id

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Ошибка добавления заявки: {e}")
            raise

    def get_all_requests(self, status_filter: Optional[str] = None) -> List[Dict]:
        """
        Получение списка заявок.
        """
        query = "SELECT * FROM requests"
        params = []

        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)

        query += " ORDER BY created_date DESC"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def update_request_status(
        self,
        request_id: int,
        new_status: str,
        master_name: Optional[str] = None
    ) -> bool:
        """
        Изменение статуса заявки.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = ["status = ?", "updated_date = ?"]
        params = [new_status, current_time]

        if new_status in ("Готова к выдаче", "Завершена"):
            fields.append("completion_date = ?")
            params.append(current_time)

        if master_name:
            fields.append("master_name = ?")
            params.append(master_name)

        params.append(request_id)

        query = f"UPDATE requests SET {', '.join(fields)} WHERE id = ?"

        self.cursor.execute(query, params)
        self.connection.commit()

        return self.cursor.rowcount > 0

    def extend_deadline(self, request_id: int, new_deadline: str) -> bool:
        """
        Продление срока выполнения заявки (роль менеджера).
        """
        try:
            self.cursor.execute("""
                UPDATE requests
                SET deadline = ?, updated_date = ?
                WHERE id = ?
            """, (
                new_deadline,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request_id
            ))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(e)
            return False

    # =========================
    # КОММЕНТАРИИ
    # =========================

    def add_comment(
        self,
        request_id: int,
        comment_text: str,
        parts_ordered: str,
        author: str
    ) -> bool:
        """
        Добавление комментария к заявке.
        """
        try:
            self.cursor.execute("""
                INSERT INTO comments (
                    request_id,
                    comment_text,
                    parts_ordered,
                    added_date,
                    author
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                request_id,
                comment_text,
                parts_ordered,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                author
            ))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(e)
            return False

    # =========================
    # ПОИСК
    # =========================

    def search_requests(self, search_term: str) -> List[Dict]:
        """
        Поиск заявок по ID, клиенту, телефону или модели.
        """
        pattern = f"%{search_term}%"
        self.cursor.execute("""
            SELECT * FROM requests
            WHERE
                CAST(id AS TEXT) LIKE ?
                OR client_name LIKE ?
                OR client_phone LIKE ?
                OR device_model LIKE ?
            ORDER BY created_date DESC
        """, (pattern, pattern, pattern, pattern))

        return [dict(row) for row in self.cursor.fetchall()]

    # =========================
    # СТАТИСТИКА
    # =========================

    def get_request_statistics(self) -> Dict:
        """
        Получение сводной статистики.
        """
        stats = {}

        self.cursor.execute("SELECT COUNT(*) FROM requests")
        stats["total_requests"] = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT status, COUNT(*) FROM requests GROUP BY status
        """)
        stats["status_counts"] = dict(self.cursor.fetchall())

        self.cursor.execute("""
            SELECT AVG(
                (julianday(completion_date) - julianday(created_date)) * 24
            )
            FROM requests
            WHERE completion_date IS NOT NULL
        """)
        avg = self.cursor.fetchone()[0]
        stats["average_completion_hours"] = round(avg, 2) if avg else 0

        self.cursor.execute("""
            SELECT device_type, COUNT(*) FROM requests GROUP BY device_type
        """)
        stats["device_statistics"] = dict(self.cursor.fetchall())

        return stats

    # =========================
    # ЗАКРЫТИЕ
    # =========================

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            logger.info("Соединение с БД закрыто")


# =========================
# СИНГЛТОН
# =========================

_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Получение экземпляра БД (singleton).
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
