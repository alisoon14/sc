"""
Сервис для работы с напоминаниями
Полнофункциональный сервис для проверки и отправки напоминаний
"""

import asyncio
import requests
from datetime import datetime
from src.database.db_operations import get_pending_reminders, mark_reminder_sent
from src.config import TELEGRAM_API_BASE
from src.utils.logger import log_shift_exchange


async def send_reminder_to_chat(message):
    """Отправляет напоминание в основной чат"""
    from src.config import TELEGRAM_CHAT_ID
    
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.ok
    except Exception as e:
        print(f"[ERROR] send_reminder_to_chat: {e}")
        return False


async def process_reminder(reminder):
    """Обрабатывает одно напоминание"""
    try:
        # Формируем сообщение для чата
        message = f"""🔔 <b>Напоминание</b>

📅 <b>Время:</b> {reminder['reminder_time'].strftime('%d.%m.%Y %H:%M')}
👤 <b>Создано:</b> {reminder['name']} (@{reminder['tguser']})

📝 <b>Текст:</b>
{reminder['reminder_text']}"""
        
        # Отправляем напоминание в чат
        success = await send_reminder_to_chat(message)
        
        if success:
            # Помечаем напоминание как отправленное
            mark_reminder_sent(reminder['id'])
            log_shift_exchange('info', 'Напоминание успешно отправлено в чат', 
                             user=reminder['tguser'], 
                             reminder_id=reminder['id'],
                             action='reminder_sent')
            print(f"[INFO] Напоминание {reminder['id']} отправлено в чат от пользователя {reminder['tguser']}")
            return True
        else:
            print(f"[ERROR] Не удалось отправить напоминание {reminder['id']} от пользователя {reminder['tguser']}")
            log_shift_exchange('error', 'Ошибка отправки напоминания в чат', 
                             user=reminder['tguser'], 
                             reminder_id=reminder['id'],
                             action='reminder_send_failed')
            return False
            
    except Exception as e:
        print(f"[ERROR] Ошибка обработки напоминания {reminder['id']}: {e}")
        log_shift_exchange('error', f'Ошибка обработки напоминания: {e}', 
                         user=reminder.get('tguser', 'unknown'), 
                         reminder_id=reminder['id'],
                         action='reminder_processing_error')
        return False


async def reminder_checker():
    """
    Фоновая задача проверки напоминаний
    Проверяет напоминания в БД и отправляет их пользователям
    """
    print("[INFO] Reminder checker started")
    
    while True:
        try:
            # Получаем напоминания, которые нужно отправить
            pending_reminders = get_pending_reminders()
            
            if pending_reminders:
                print(f"[INFO] Найдено {len(pending_reminders)} напоминаний для отправки")
                
                # Обрабатываем каждое напоминание
                for reminder in pending_reminders:
                    await process_reminder(reminder)
                    # Небольшая пауза между отправками, чтобы не нагружать Telegram API
                    await asyncio.sleep(1)
            
            # Проверяем каждые 30 секунд
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"[ERROR] Reminder checker error: {e}")
            log_shift_exchange('error', f'Ошибка в reminder_checker: {e}', 
                             action='reminder_checker_error')
            await asyncio.sleep(60)  # Увеличиваем интервал при ошибке


async def get_reminder_statistics():
    """Получает статистику по напоминаниям"""
    try:
        from src.database.db_operations import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Общее количество напоминаний
                cursor.execute("SELECT COUNT(*) as total FROM Reminders")
                total = cursor.fetchone()['total']
                
                # Отправленные напоминания
                cursor.execute("SELECT COUNT(*) as sent FROM Reminders WHERE is_sent = TRUE")
                sent = cursor.fetchone()['sent']
                
                # Ожидающие напоминания
                cursor.execute("SELECT COUNT(*) as pending FROM Reminders WHERE is_sent = FALSE AND reminder_time > NOW()")
                pending = cursor.fetchone()['pending']
                
                # Просроченные напоминания
                cursor.execute("SELECT COUNT(*) as overdue FROM Reminders WHERE is_sent = FALSE AND reminder_time <= NOW()")
                overdue = cursor.fetchone()['overdue']
                
                return {
                    'total': total,
                    'sent': sent,
                    'pending': pending,
                    'overdue': overdue
                }
                
    except Exception as e:
        print(f"[ERROR] get_reminder_statistics: {e}")
        return None
