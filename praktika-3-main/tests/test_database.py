"""
Тесты для модуля базы данных.
"""

import unittest
import tempfile
import os
from src.database import Database

class TestDatabase(unittest.TestCase):
    """
    Тесты для класса Database.
    """
    
    def setUp(self):
        """Создание временной базы данных для тестов."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.database = Database(self.db_path)
    
    def tearDown(self):
        """Удаление временной базы данных."""
        self.database.close()
        os.unlink(self.db_path)
    
    def test_add_request(self):
        """Тест добавления заявки."""
        request_id = self.database.add_request(
            device_type="Холодильник",
            device_model="Samsung RB-100",
            problem_description="Не морозит",
            client_name="Иванов Иван Иванович",
            client_phone="+79991234567"
        )
        
        self.assertIsNotNone(request_id)
        self.assertGreater(request_id, 0)
    
    def test_get_all_requests(self):
        """Тест получения всех заявок."""
        # Добавляем тестовые данные
        self.database.add_request(
            "Стиральная машина", "LG F-100",
            "Не сливает воду", "Петров Петр", "89991234567"
        )
        
        requests = self.database.get_all_requests()
        
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['device_type'], "Стиральная машина")
    
    def test_update_status(self):
        """Тест обновления статуса заявки."""
        request_id = self.database.add_request(
            "Телевизор", "Sony Bravia",
            "Нет изображения", "Сидоров Сидор", "89991234568"
        )
        
        success = self.database.update_request_status(
            request_id, "В процессе", "Мастер Иванов"
        )
        
        self.assertTrue(success)
        
        # Проверяем обновление
        requests = self.database.get_all_requests()
        updated_request = next(
            (r for r in requests if r['id'] == request_id), 
            None
        )
        
        self.assertIsNotNone(updated_request)
        self.assertEqual(updated_request['status'], "В процессе")
        self.assertEqual(updated_request['master_name'], "Мастер Иванов")
    
    def test_search_requests(self):
        """Тест поиска заявок."""
        # Добавляем несколько заявок
        self.database.add_request(
            "Холодильник", "Atlant", "Шумит",
            "Кузнецов Алексей", "89991234569"
        )
        self.database.add_request(
            "Стиральная машина", "Indesit", "Не отжимает",
            "Алексеева Анна", "89991234570"
        )
        
        # Поиск по имени
        results = self.database.search_requests("Алекс")
        self.assertEqual(len(results), 2)  # Должны найти обе заявки
        
        # Поиск по модели
        results = self.database.search_requests("Atlant")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['device_model'], "Atlant")
    
    def test_get_statistics(self):
        """Тест расчета статистики."""
        # Добавляем тестовые данные
        for i in range(5):
            self.database.add_request(
                f"Устройство {i % 3}", f"Модель {i}",
                f"Проблема {i}", f"Клиент {i}", f"8999123457{i}"
            )
        
        stats = self.database.get_request_statistics()
        
        self.assertEqual(stats['total_requests'], 5)
        self.assertIn('status_counts', stats)
        self.assertIn('device_statistics', stats)

if __name__ == '__main__':
    unittest.main()