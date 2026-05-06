"""
Модуль для работы со статистикой
Содержит функции для вычисления статистических данных
"""

from datetime import timedelta
from src.database.db_operations import get_request_ids_from_db
from src.services.servicedesk_api import get_worklog_for_request


def calculate_average_time(time_differences):
    """Вычисляет среднее время из списка временных интервалов"""
    if not time_differences:
        return timedelta(0)
    
    total_seconds = sum(time.total_seconds() for time in time_differences)
    average_seconds = total_seconds / len(time_differences)
    return timedelta(seconds=average_seconds)


def get_current_statistics():
    """
    Получает актуальную статистику при каждом вызове
    Возвращает кортеж (avg_time, total_worklogs_all_requests, total_time_spent_all_requests, total_resolved_worklogs)
    """
    try:
        request_ids, time_differences = get_request_ids_from_db()
        
        # Логируем информацию о заявках
        for request_id, time_difference in zip(request_ids, time_differences):
            print(f"Request ID: {request_id}, Time Difference: {str(time_difference)}")
        
        # Вычисляем среднее время
        avg_time = calculate_average_time(time_differences)
        print(f"Среднее время обработки заявки: {str(avg_time)}")
        
        # Собираем статистику по рабочим журналам
        total_time_spent_all_requests = 0
        total_worklogs_all_requests = 0
        total_resolved_worklogs = 0
        
        for request_id in request_ids:
            total_time_spent, total_worklogs, resolved_worklogs = get_worklog_for_request(request_id)
            total_time_spent_all_requests += total_time_spent
            total_worklogs_all_requests += total_worklogs
            total_resolved_worklogs += resolved_worklogs
        
        print(f"Total time spent across all requests: {total_time_spent_all_requests // 3600}h {(total_time_spent_all_requests % 3600) // 60}m")
        print(f"Total worklogs across all requests: {total_worklogs_all_requests}")
        print(f"Total 'Заявка. Решена' worklogs across all requests: {total_resolved_worklogs}")
        
        return avg_time, total_worklogs_all_requests, total_time_spent_all_requests, total_resolved_worklogs
        
    except Exception as e:
        print(f"[ERROR] get_current_statistics: {e}")
        return timedelta(0), 0, 0, 0
