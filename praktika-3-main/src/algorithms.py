"""
Модуль с алгоритмами расчета статистики.
"""

from datetime import datetime
from typing import List, Dict, Tuple
import statistics
from src.database import get_database

def calculate_average_repair_time() -> float:
    """
    Алгоритм расчета среднего времени ремонта.
    
    Returns:
        float: Среднее время в часах
    
    Алгоритм:
    1. Получить все завершенные заявки из БД
    2. Для каждой заявки вычислить время выполнения
    3. Вычислить среднее арифметическое
    4. Вернуть результат с округлением до 2 знаков
    """
    try:
        db = get_database()
        
        # Получаем завершенные заявки
        db.cursor.execute('''
            SELECT created_date, completion_date 
            FROM requests 
            WHERE completion_date IS NOT NULL
        ''')
        
        completed_requests = db.cursor.fetchall()
        
        if not completed_requests:
            return 0.0
        
        repair_times = []
        
        for created_str, completed_str in completed_requests:
            # Преобразование строк в datetime
            created_date = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
            completed_date = datetime.strptime(completed_str, "%Y-%m-%d %H:%M:%S")
            
            # Расчет разницы в часах
            time_difference = completed_date - created_date
            hours = time_difference.total_seconds() / 3600
            
            repair_times.append(hours)
        
        # Расчет среднего значения
        average_time = statistics.mean(repair_times)
        
        return round(average_time, 2)
        
    except Exception as e:
        print(f"Ошибка при расчете среднего времени: {e}")
        return 0.0

def calculate_request_statistics_by_device() -> Dict[str, Dict]:
    """
    Алгоритм расчета статистики по типам устройств.
    
    Returns:
        Dict: Статистика по устройствам
    
    Алгоритм:
    1. Сгруппировать заявки по типу устройства
    2. Для каждой группы посчитать:
       - Общее количество заявок
       - Количество завершенных заявок
       - Среднее время ремонта
       - Самую частую проблему
    """
    try:
        db = get_database()
        
        # Получаем все заявки с группировкой
        db.cursor.execute('''
            SELECT 
                device_type,
                status,
                problem_description,
                created_date,
                completion_date
            FROM requests
            ORDER BY device_type
        ''')
        
        all_requests = db.cursor.fetchall()
        
        # Структура для хранения статистики
        device_stats = {}
        
        for request in all_requests:
            device_type = request[0]
            status = request[1]
            problem = request[2]
            created_str = request[3]
            completed_str = request[4]
            
            if device_type not in device_stats:
                device_stats[device_type] = {
                    'total': 0,
                    'completed': 0,
                    'repair_times': [],
                    'problems': {}
                }
            
            # Общее количество
            device_stats[device_type]['total'] += 1
            
            # Подсчет проблем
            if problem in device_stats[device_type]['problems']:
                device_stats[device_type]['problems'][problem] += 1
            else:
                device_stats[device_type]['problems'][problem] = 1
            
            # Для завершенных заявок считаем время
            if status == 'Завершена' and completed_str:
                created_date = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
                completed_date = datetime.strptime(completed_str, "%Y-%m-%d %H:%M:%S")
                
                time_diff = completed_date - created_date
                hours = time_diff.total_seconds() / 3600
                
                device_stats[device_type]['completed'] += 1
                device_stats[device_type]['repair_times'].append(hours)
        
        # Расчет итоговой статистики
        result_stats = {}
        
        for device_type, stats in device_stats.items():
            # Самая частая проблема
            most_common_problem = max(
                stats['problems'].items(),
                key=lambda x: x[1]
            )[0] if stats['problems'] else "Нет данных"
            
            # Среднее время ремонта
            avg_time = 0.0
            if stats['repair_times']:
                avg_time = round(statistics.mean(stats['repair_times']), 2)
            
            result_stats[device_type] = {
                'total_requests': stats['total'],
                'completed_requests': stats['completed'],
                'average_repair_time_hours': avg_time,
                'most_common_problem': most_common_problem,
                'completion_rate': round(stats['completed'] / stats['total'] * 100, 2) 
                if stats['total'] > 0 else 0
            }
        
        return result_stats
        
    except Exception as e:
        print(f"Ошибка при расчете статистики по устройствам: {e}")
        return {}

def calculate_status_distribution() -> List[Tuple[str, int, float]]:
    """
    Алгоритм расчета распределения заявок по статусам.
    
    Returns:
        List[Tuple]: Список кортежей (статус, количество, процент)
    
    Алгоритм:
    1. Подсчитать общее количество заявок
    2. Сгруппировать заявки по статусам
    3. Для каждого статуса вычислить процент от общего числа
    4. Отсортировать по убыванию количества
    """
    try:
        db = get_database()
        
        # Общее количество заявок
        db.cursor.execute("SELECT COUNT(*) FROM requests")
        total = db.cursor.fetchone()[0]
        
        if total == 0:
            return []
        
        # Группировка по статусам
        db.cursor.execute('''
            SELECT status, COUNT(*) 
            FROM requests 
            GROUP BY status
            ORDER BY COUNT(*) DESC
        ''')
        
        status_counts = db.cursor.fetchall()
        
        # Расчет процентов
        result = []
        for status, count in status_counts:
            percentage = round(count / total * 100, 2)
            result.append((status, count, percentage))
        
        return result
        
    except Exception as e:
        print(f"Ошибка при расчете распределения статусов: {e}")
        return []

def get_performance_metrics(start_date: str = None, end_date: str = None) -> Dict:
    """
    Алгоритм расчета метрик производительности.
    
    Args:
        start_date (str): Начальная дата (YYYY-MM-DD)
        end_date (str): Конечная дата (YYYY-MM-DD)
    
    Returns:
        Dict: Метрики производительности
    
    Алгоритм:
    1. Фильтрация заявок по дате (если указаны)
    2. Расчет:
       - Заявок в день
       - Среднего времени обработки
       - Эффективности мастеров
       - Затрат на запчасти
    """
    try:
        db = get_database()
        
        # Базовый запрос
        query = "SELECT * FROM requests"
        params = []
        
        # Добавление фильтра по дате
        if start_date and end_date:
            query += " WHERE created_date BETWEEN ? AND ?"
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
        elif start_date:
            query += " WHERE created_date >= ?"
            params.append(f"{start_date} 00:00:00")
        elif end_date:
            query += " WHERE created_date <= ?"
            params.append(f"{end_date} 23:59:59")
        
        db.cursor.execute(query, params)
        requests = db.cursor.fetchall()
        
        if not requests:
            return {
                'total_requests': 0,
                'requests_per_day': 0,
                'average_processing_time': 0,
                'master_efficiency': {},
                'total_parts_cost': 0
            }
        
        # Расчет метрик
        total_requests = len(requests)
        
        # Заявок в день
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            days = (end - start).days + 1
            requests_per_day = round(total_requests / days, 2)
        else:
            requests_per_day = total_requests
        
        # Среднее время обработки
        processing_times = []
        for req in requests:
            if req[9]:  # completion_date
                created = datetime.strptime(req[1], "%Y-%m-%d %H:%M:%S")
                completed = datetime.strptime(req[9], "%Y-%m-%d %H:%M:%S")
                time_diff = completed - created
                processing_times.append(time_diff.total_seconds() / 3600)
        
        avg_processing_time = round(
            statistics.mean(processing_times), 2
        ) if processing_times else 0
        
        # Эффективность мастеров
        master_efficiency = {}
        for req in requests:
            master = req[8]  # master_name
            if master:
                if master not in master_efficiency:
                    master_efficiency[master] = {'completed': 0, 'total': 0}
                
                master_efficiency[master]['total'] += 1
                if req[5] == 'Завершена':  # status
                    master_efficiency[master]['completed'] += 1
        
        # Расчет процента завершенных
        for master, stats in master_efficiency.items():
            if stats['total'] > 0:
                stats['efficiency'] = round(
                    stats['completed'] / stats['total'] * 100, 2
                )
        
        # Затраты на запчасти (упрощенно)
        db.cursor.execute("SELECT SUM(LENGTH(parts_ordered)) FROM comments")
        total_parts_length = db.cursor.fetchone()[0] or 0
        # Предполагаем, что каждый символ = 10 условных единиц стоимости
        total_parts_cost = total_parts_length * 10
        
        return {
            'total_requests': total_requests,
            'requests_per_day': requests_per_day,
            'average_processing_time_hours': avg_processing_time,
            'master_efficiency': master_efficiency,
            'total_parts_cost': total_parts_cost
        }
        
    except Exception as e:
        print(f"Ошибка при расчете метрик производительности: {e}")
        return {}