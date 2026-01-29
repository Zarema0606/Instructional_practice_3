import csv
from datetime import datetime

from src.database import get_database
from src.utils import hash_password


# ======================================================
# ИМПОРТ ПОЛЬЗОВАТЕЛЕЙ
# CSV: userID;fio;phone;login;password;type
# ======================================================

def import_users(path: str):
    db = get_database()

    role_map = {
        "менеджер": "manager",
        "мастер": "master",
        "оператор": "operator",
        "администратор": "admin",
        "заказчик": "client",
    }

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            username = row["login"].strip()
            password = row["password"].strip()
            full_name = row["fio"].strip()
            role_raw = row["type"].strip().lower()

            role = role_map.get(role_raw, "client")

            db.cursor.execute("""
                INSERT OR IGNORE INTO users
                (username, password_hash, role, full_name)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                hash_password(password),
                role,
                full_name
            ))

    db.connection.commit()


# ======================================================
# ИМПОРТ ЗАЯВОК
# CSV:
# requestID;startDate;homeTechType;homeTechModel;
# problemDescryption;requestStatus;completionDate;
# repairParts;masterID;clientID
# ======================================================

def import_requests(path: str):
    db = get_database()

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            # получаем имя клиента по clientID
            db.cursor.execute(
                "SELECT full_name FROM users WHERE id = ?",
                (row["clientID"],)
            )
            client = db.cursor.fetchone()

            client_name = client[0] if client else "Неизвестный клиент"
            client_phone = "+7 (000) 000-00-00"

            db.cursor.execute("""
                INSERT OR IGNORE INTO requests (
                    id,
                    created_date,
                    device_type,
                    device_model,
                    problem_description,
                    client_name,
                    client_phone,
                    status,
                    completion_date,
                    updated_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["requestID"],
                f"{row['startDate']} 00:00:00",
                row["homeTechType"],
                row["homeTechModel"],
                row["problemDescryption"],
                client_name,
                client_phone,
                row["requestStatus"],
                None if row["completionDate"] == "null"
                else row["completionDate"] + " 00:00:00",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

    db.connection.commit()


# ======================================================
# ИМПОРТ КОММЕНТАРИЕВ
# CSV:
# commentID;message;masterID;requestID
# ======================================================

def import_comments(path: str):
    db = get_database()

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            # Проверяем, существует ли заявка
            db.cursor.execute(
                "SELECT id FROM requests WHERE id = ?",
                (row["requestID"],)
            )
            if not db.cursor.fetchone():
                # Пропускаем комментарий без заявки
                continue

            db.cursor.execute("""
                INSERT OR IGNORE INTO comments (
                    id,
                    request_id,
                    comment_text,
                    added_date,
                    author
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["commentID"],
                row["requestID"],
                row["message"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"master_{row['masterID']}"
            ))

    db.connection.commit()
