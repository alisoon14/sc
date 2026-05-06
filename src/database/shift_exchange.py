"""
Модуль для работы с обменами смен
Содержит логику создания, согласования и выполнения обменов
"""

import pymysql
from datetime import datetime
from src.database.db_operations import get_db_connection, get_shift_type_name
from src.config import FORBIDDEN_SHIFT_TYPES, SHIFT_EXCHANGE_ROLES
from src.utils.logger import log_shift_exchange


def create_shift_exchange(schedule_id, initiator_tguser, recipient_tguser):
    """Создает запрос на обмен смен"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ShiftExchange (schedule_id, initiator_tguser, recipient_tguser)
                    VALUES (%s, %s, %s)
                """, (schedule_id, initiator_tguser, recipient_tguser))
                conn.commit()
                return cursor.lastrowid
    except Exception as e:
        log_shift_exchange('error', 'Ошибка при создании обмена в БД', 
                          error=str(e), action='create_exchange_error')
        print(f"[ERROR] create_shift_exchange: {e}")
        return None


def get_shift_exchange(exchange_id):
    """Получает информацию об обмене по ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM ShiftExchange WHERE id = %s", (exchange_id,))
                return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] get_shift_exchange: {e}")
        return None


def update_exchange_approval(exchange_id, role, value=True):
    """Обновляет статус согласования обмена"""
    role_mapping = {
        'recipient': 'approved_by_recipient',
        'lead': 'approved_by_lead', 
        'manager': 'approved_by_manager'
    }
    
    if role not in role_mapping:
        return False
        
    field = role_mapping[role]
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE ShiftExchange SET {field} = %s WHERE id = %s", 
                             (1 if value else 0, exchange_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] update_exchange_approval: {e}")
        return False


def reject_shift_exchange(exchange_id):
    """Отклоняет обмен смен"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE ShiftExchange SET status = 'rejected' WHERE id = %s", 
                             (exchange_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] reject_shift_exchange: {e}")
        return False


def is_shift_exchangeable(shift_type_id):
    """Проверяет, можно ли обменять смену данного типа"""
    return shift_type_id not in FORBIDDEN_SHIFT_TYPES


def calculate_final_shift_type(transfer_shift_type, existing_shift_type=None):
    """
    Вычисляет итоговый тип смены при обмене
    Учитывает комбинации различных типов смен
    """
    if not existing_shift_type:
        return transfer_shift_type
    
    # Комбинация 8-17 и 21-09 = 08-17 21-09 (тип 102)
    if (existing_shift_type == 3 and transfer_shift_type == 2) or \
       (existing_shift_type == 2 and transfer_shift_type == 3):
        return 102
    
    # Комбинация дневной и ночной = тип "С" (тип 11)
    if (existing_shift_type == 2 and transfer_shift_type in [3, 1]) or \
       (existing_shift_type in [3, 1] and transfer_shift_type == 2):
        return 11
    
    return transfer_shift_type


def execute_shift_transfer(exchange_id):
    """
    Выполняет перенос смены после всех согласований
    Возвращает результат операции и сообщение об изменениях
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Получаем данные обмена
                cursor.execute("SELECT * FROM ShiftExchange WHERE id = %s", (exchange_id,))
                exchange = cursor.fetchone()
                
                if not exchange:
                    return False, "Обмен не найден"
                
                # Получаем ID сотрудников
                cursor.execute("SELECT id FROM Employees WHERE tguser = %s", 
                             (exchange['recipient_tguser'],))
                recipient = cursor.fetchone()
                
                cursor.execute("SELECT id FROM Employees WHERE tguser = %s", 
                             (exchange['initiator_tguser'],))
                initiator = cursor.fetchone()
                
                if not recipient or not initiator:
                    return False, "Один из сотрудников не найден"
                
                # Получаем информацию о передаваемой смене
                cursor.execute("SELECT date, shift_type_id FROM Schedule WHERE id = %s", 
                             (exchange['schedule_id'],))
                transfer_shift = cursor.fetchone()
                
                if not transfer_shift:
                    return False, "Смена для передачи не найдена"
                
                # Проверяем запрет на обмен
                if not is_shift_exchangeable(transfer_shift['shift_type_id']):
                    shift_type_name = get_shift_type_name(transfer_shift['shift_type_id'])
                    return False, f"Смены типа '{shift_type_name}' не подлежат обмену"
                
                # Проверяем существующую смену у принимающего
                cursor.execute("""
                    SELECT id, shift_type_id FROM Schedule 
                    WHERE employee_id = %s AND date = %s AND id != %s
                """, (recipient['id'], transfer_shift['date'], exchange['schedule_id']))
                existing_shift = cursor.fetchone()
                
                # Проверяем запрет на обмен существующей смены принимающего
                if existing_shift and not is_shift_exchangeable(existing_shift['shift_type_id']):
                    shift_type_name = get_shift_type_name(existing_shift['shift_type_id'])
                    return False, f"У принимающего смена типа '{shift_type_name}', которая не подлежит обмену"
                
                # Вычисляем финальный тип смены
                existing_type = existing_shift['shift_type_id'] if existing_shift else None
                final_shift_type = calculate_final_shift_type(transfer_shift['shift_type_id'], existing_type)
                
                # Очищаем смену у инициатора
                cursor.execute("""
                    UPDATE Schedule
                    SET employee_id = NULL
                    WHERE employee_id = %s AND date = %s
                """, (initiator['id'], transfer_shift['date']))
                
                # Удаляем существующую смену принимающего, если есть
                if existing_shift:
                    cursor.execute("DELETE FROM Schedule WHERE id = %s", (existing_shift['id'],))
                
                # Назначаем смену принимающему
                cursor.execute("""
                    UPDATE Schedule
                    SET employee_id = %s, shift_type_id = %s
                    WHERE id = %s
                """, (recipient['id'], final_shift_type, exchange['schedule_id']))
                
                # Обновляем статус обмена
                cursor.execute("UPDATE ShiftExchange SET status = 'approved' WHERE id = %s", 
                             (exchange_id,))
                conn.commit()
                
                # Формируем сообщение об изменениях
                changes_message = ""
                if existing_shift and final_shift_type != transfer_shift['shift_type_id']:
                    if final_shift_type == 102:
                        changes_message = "⚠️ Тип смены изменен на комбинированную (08-17 21-09) из-за пересечения смен."
                    elif final_shift_type == 11:
                        changes_message = "⚠️ Тип смены изменен на 'С' из-за пересечения ночной и дневной смен."
                
                log_shift_exchange('info', 'Обмен смен успешно выполнен', 
                                  exchange_id=exchange_id, 
                                  final_shift_type=final_shift_type,
                                  date=transfer_shift['date'].strftime('%Y-%m-%d'),
                                  action='exchange_executed')
                
                return True, changes_message
                
    except Exception as e:
        log_shift_exchange('error', 'Ошибка при выполнении обмена смен', 
                          exchange_id=exchange_id, error=str(e), action='execute_exchange_error')
        print(f"[ERROR] execute_shift_transfer: {e}")
        return False, f"Ошибка при выполнении обмена: {str(e)}"


def is_exchange_fully_approved(exchange):
    """Проверяет, полностью ли согласован обмен"""
    return (exchange['approved_by_recipient'] and 
            (exchange['approved_by_lead'] or exchange['approved_by_manager']))


def get_user_role_for_exchange(tguser):
    """Определяет роль пользователя в процессе согласования"""
    if tguser == SHIFT_EXCHANGE_ROLES['lead_engineer']:
        return 'lead'
    elif tguser == SHIFT_EXCHANGE_ROLES['manager']:
        return 'manager'
    else:
        return 'employee'


def get_shift_exchange_details(exchange_id):
    """Получает детальную информацию об обмене с именами участников"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        se.*,
                        s.date as shift_date,
                        s.shift_type_id,
                        e1.name as requester_name,
                        e2.name as recipient_name
                    FROM ShiftExchange se
                    JOIN Schedule s ON se.schedule_id = s.id
                    LEFT JOIN Employees e1 ON se.initiator_tguser = e1.tguser
                    LEFT JOIN Employees e2 ON se.recipient_tguser = e2.tguser
                    WHERE se.id = %s
                """, (exchange_id,))
                
                result = cursor.fetchone()
                if result:
                    # Добавляем название типа смены
                    result['shift_type_name'] = get_shift_type_name(result['shift_type_id'])
                    # Добавляем псевдонимы для удобства использования
                    result['requester_tguser'] = result['initiator_tguser']
                return result
    except Exception as e:
        print(f"[ERROR] get_shift_exchange_details: {e}")
        return None
