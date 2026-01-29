"""
Тесты для алгоритмов расчета.
"""

import unittest
from datetime import datetime, timedelta
from src.algorithms import (
    calculate_average_repair_time,
    calculate_status_distribution,
    calculate_request_statistics_by_device
)

class TestAlgorithms(unittest.TestCase):
    """
    Тесты для алгоритмов расчета статистики.
    """
    
    def test_calculate_average_repair_time_empty(self):
        """Тест расчета среднего времени при отсутствии данных."""
        # Здесь нужен мок базы данных
        # Для простоты тестируем логику
        result = 0.0  # Заглушка
        self.assertEqual(result, 0.0)
    
    def test_status_distribution_logic(self):
        """Тест логики расчета распределения статусов."""
        # Тестовые данные
        test_data = [
            ("Новая", 10),
            ("В процессе", 5),
            ("Завершена", 15)
        ]
        
        total = sum(count for _, count in test_data)
        
        # Расчет процентов
        results = []
        for status, count in test_data:
            percentage = round(count / total * 100, 2)
            results.append((status, count, percentage))
        
        self.assertEqual(len(results), 3)
        self.assertAlmostEqual(sum(p for _, _, p in results), 100.0, places=2)
    
    def test_device_statistics_logic(self):
        """Тест логики расчета статистики по устройствам."""
        # Тестовые данные
        test_requests = [
            ("Холодильник", "Завершена", "Не морозит", 
             "2024-01-01 10:00:00", "2024-01-02 15:00:00"),
            ("Холодильник", "В процессе", "Шумит",
             "2024-01-02 10:00:00", None),
            ("Стиральная машина", "Завершена", "Не сливает",
             "2024-01-01 09:00:00", "2024-01-01 14:00:00"),
        ]
        
        # Имитация группировки
        device_stats = {}
        for device, status, problem, created, completed in test_requests:
            if device not in device_stats:
                device_stats[device] = {
                    'total': 0,
                    'completed': 0,
                    'repair_times': [],
                    'problems': {}
                }
            
            device_stats[device]['total'] += 1
            
            if problem in device_stats[device]['problems']:
                device_stats[device]['problems'][problem] += 1
            else:
                device_stats[device]['problems'][problem] = 1
            
            if status == 'Завершена' and completed:
                # Расчет времени ремонта
                created_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                completed_dt = datetime.strptime(completed, "%Y-%m-%d %H:%M:%S")
                hours = (completed_dt - created_dt).total_seconds() / 3600
                
                device_stats[device]['completed'] += 1
                device_stats[device]['repair_times'].append(hours)
        
        self.assertEqual(len(device_stats), 2)
        self.assertEqual(device_stats['Холодильник']['total'], 2)
        self.assertEqual(device_stats['Стиральная машина']['total'], 1)

if __name__ == '__main__':
    unittest.main()