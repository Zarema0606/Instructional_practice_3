"""
Модуль с классами-моделями для представления данных.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class RepairRequest:
    """
    Модель заявки на ремонт.
    """
    id: Optional[int] = None
    created_date: Optional[datetime] = None
    device_type: str = ""
    device_model: str = ""
    problem_description: str = ""
    client_name: str = ""
    client_phone: str = ""
    status: str = "Новая"
    master_name: Optional[str] = None
    completion_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """
        Преобразование объекта в словарь.
        
        Returns:
            dict: Словарь с данными заявки
        """
        return {
            'id': self.id,
            'created_date': self.created_date.strftime("%Y-%m-%d %H:%M:%S") 
                          if self.created_date else None,
            'device_type': self.device_type,
            'device_model': self.device_model,
            'problem_description': self.problem_description,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'status': self.status,
            'master_name': self.master_name,
            'completion_date': self.completion_date.strftime("%Y-%m-%d %H:%M:%S") 
                              if self.completion_date else None,
            'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M:%S") 
                           if self.updated_date else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RepairRequest':
        """
        Создание объекта из словаря.
        
        Args:
            data (dict): Словарь с данными
        
        Returns:
            RepairRequest: Объект заявки
        """
        request = cls()
        request.id = data.get('id')
        
        # Преобразование строк в datetime
        if data.get('created_date'):
            request.created_date = datetime.strptime(
                data['created_date'], "%Y-%m-%d %H:%M:%S"
            )
        
        request.device_type = data.get('device_type', '')
        request.device_model = data.get('device_model', '')
        request.problem_description = data.get('problem_description', '')
        request.client_name = data.get('client_name', '')
        request.client_phone = data.get('client_phone', '')
        request.status = data.get('status', 'Новая')
        request.master_name = data.get('master_name')
        
        if data.get('completion_date'):
            request.completion_date = datetime.strptime(
                data['completion_date'], "%Y-%m-%d %H:%M:%S"
            )
        
        if data.get('updated_date'):
            request.updated_date = datetime.strptime(
                data['updated_date'], "%Y-%m-%d %H:%M:%S"
            )
        
        return request

@dataclass
class Comment:
    """
    Модель комментария к заявке.
    """
    id: Optional[int] = None
    request_id: Optional[int] = None
    comment_text: str = ""
    parts_ordered: str = ""
    added_date: Optional[datetime] = None
    author: str = ""

STATUS_CHOICES = [
    ("Новая", "Новая"),
    ("В процессе", "В процессе ремонта"),
    ("Ожидание запчастей", "Ожидание запчастей"),
    ("Готова к выдаче", "Готова к выдаче"),
    ("Завершена", "Завершена")
]

DEVICE_TYPES = [
    "Холодильник",
    "Стиральная машина",
    "Плита",
    "Микроволновая печь",
    "Посудомоечная машина",
    "Телевизор",
    "Кондиционер",
    "Другое"
]