"""
Вспомогательные функции и утилиты.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib

def validate_phone_number(phone: str) -> bool:
    """
    Валидация номера телефона.
    
    Args:
        phone (str): Номер телефона
    
    Returns:
        bool: True если номер валиден
    """
    # Удаление всех нецифровых символов кроме плюса
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Проверка формата
    # Российские номера: +7XXXXXXXXXX, 8XXXXXXXXXX, 7XXXXXXXXXX
    pattern = r'^(\+7|7|8)\d{10}$'
    
    return bool(re.match(pattern, cleaned))

def format_phone_number(phone: str) -> str:
    """
    Форматирование номера телефона в стандартный вид.
    
    Args:
        phone (str): Номер телефона
    
    Returns:
        str: Отформатированный номер
    """
    cleaned = re.sub(r'[^\d]', '', phone)
    
    if cleaned.startswith('8'):
        cleaned = '7' + cleaned[1:]
    elif cleaned.startswith('+7'):
        cleaned = '7' + cleaned[2:]
    
    if len(cleaned) == 11 and cleaned.startswith('7'):
        return f"+7 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:9]}-{cleaned[9:]}"
    
    return phone

def calculate_due_date(created_date: str, device_type: str) -> str:
    """
    Расчет предполагаемой даты завершения ремонта.
    
    Args:
        created_date (str): Дата создания заявки
        device_type (str): Тип устройства
    
    Returns:
        str: Предполагаемая дата завершения
    """
    # Стандартные сроки ремонта по типам устройств (в днях)
    repair_times = {
        'Холодильник': 3,
        'Стиральная машина': 2,
        'Плита': 1,
        'Микроволновая печь': 1,
        'Посудомоечная машина': 2,
        'Телевизор': 2,
        'Кондиционер': 3,
        'Другое': 2
    }
    
    days_to_add = repair_times.get(device_type, 2)
    
    try:
        created = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
        due_date = created + timedelta(days=days_to_add)
        return due_date.strftime("%Y-%m-%d")
    except:
        return "Не определено"

def generate_report_filename(report_type: str) -> str:
    """
    Генерация имени файла для отчета.
    
    Args:
        report_type (str): Тип отчета
    
    Returns:
        str: Имя файла
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_type = re.sub(r'[^\w]', '_', report_type.lower())
    
    return f"отчет_{safe_type}_{timestamp}.txt"

def hash_password(password: str) -> str:
    """
    Хеширование пароля.
    
    Args:
        password (str): Пароль
    
    Returns:
        str: Хеш пароля
    """
    salt = "service_center_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def validate_email(email: str) -> bool:
    """
    Валидация email адреса.
    
    Args:
        email (str): Email адрес
    
    Returns:
        bool: True если email валиден
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def split_name(full_name: str) -> tuple:
    """
    Разделение ФИО на составляющие.
    
    Args:
        full_name (str): Полное ФИО
    
    Returns:
        tuple: (Фамилия, Имя, Отчество)
    """
    parts = full_name.strip().split()
    
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    elif len(parts) == 1:
        return parts[0], "", ""
    else:
        return "", "", ""