"""
Модуль для работы с базой данных
Содержит все функции для взаимодействия с MySQL
"""

import pymysql
from datetime import datetime
from src.config import DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_HOST_2, DB_USER_2, DB_PASS_2, DB_NAME_2


def get_db_connection():
    """Создает подключение к основной базе данных"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def get_db_connection_2():
    """Создает подключение ко второй базе данных"""
    return pymysql.connect(
        host=DB_HOST_2,
        user=DB_USER_2,
        port=7849,
        password=DB_PASS_2,
        database=DB_NAME_2,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def get_user_data(tguser):
    """Получает данные пользователя по telegram username"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, phone, grade FROM Employees WHERE tguser = %s", (tguser,))
                result = cursor.fetchone()
                return (result['name'], result['phone'], result['grade']) if result else None
    except pymysql.MySQLError as e:
        print(f"[ERROR] get_user_data: {e}")
        return None


def get_telegram_id_by_tguser(tguser):
    """Получает Telegram ID по username"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT telegram_id FROM Employees WHERE tguser = %s", (tguser,))
                result = cursor.fetchone()
                return result['telegram_id'] if result else None
    except Exception as e:
        print(f"[ERROR] get_telegram_id_by_tguser: {e}")
        return None


def update_telegram_id(tguser, telegram_id):
    """Обновляет Telegram ID пользователя"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Employees SET telegram_id = %s WHERE tguser = %s", 
                             (telegram_id, tguser))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] update_telegram_id: {e}")
        return False


def set_onshift(tguser):
    """Устанавливает пользователя как дежурного"""
    try:
        # Основная база данных
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Employees SET onshift = 0")
                cursor.execute("UPDATE Employees SET onshift = 1 WHERE tguser = %s", (tguser,))
                conn.commit()

        # Вторая база данных
        with get_db_connection_2() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Employees SET onshift = 0")
                cursor.execute("UPDATE Employees SET onshift = 1 WHERE tguser = %s", (tguser,))
                conn.commit()
        
        return True
    except pymysql.MySQLError as e:
        print(f"[ERROR] set_onshift: {e}")
        return False


def update_start_shift_time(tguser):
    """Обновляет время начала смены"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Основная база данных
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Employees SET LastLoginTime = %s WHERE tguser = %s", 
                             (current_time, tguser))
                conn.commit()

        # Вторая база данных
        with get_db_connection_2() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Employees SET LastLoginTime = %s WHERE tguser = %s", 
                             (current_time, tguser))
                conn.commit()
        
        return True
    except Exception as e:
        print(f"[ERROR] update_start_shift_time: {e}")
        return False


def get_static_user_from_db(tguser):
    """Получает username пользователя по tguser"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username FROM Employees WHERE tguser = %s", (tguser,))
                result = cursor.fetchone()
                return result['username'] if result else None
    except Exception as e:
        print(f"[ERROR] get_static_user_from_db: {e}")
        return None


def get_sdid_name_from_db(username):
    """Получает ServiceDesk ID техника по username"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT TechnitianIdSd FROM Employees WHERE username = %s", (username,))
                result = cursor.fetchone()
                return result['TechnitianIdSd'] if result else None
    except Exception as e:
        print(f"[ERROR] get_sdid_name_from_db: {e}")
        return None


def get_technician_ids_from_db():
    """Получает все ID техников из базы данных"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT TechnitianIdSd FROM Employees")
                return [str(row['TechnitianIdSd']) for row in cursor.fetchall()]
    except pymysql.MySQLError as e:
        print(f"[ERROR] get_technician_ids_from_db: {e}")
        return []


def get_today_shifts():
    """Получает смены на сегодняшний день"""
    try:
        from datetime import date
        today = date.today()
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        e.name,
                        st.name as shift_type_name,
                        st.start_time,
                        st.end_time,
                        st.id as shift_type_id
                    FROM Schedule s
                    JOIN Employees e ON s.employee_id = e.id
                    JOIN ShiftTypes st ON s.shift_type_id = st.id
                    WHERE s.date = %s AND e.active = 1
                    ORDER BY st.start_time
                """, (today,))
                return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] get_today_shifts: {e}")
        return []


def get_shift_type_name(shift_type_id):
    """Получает название типа смены по ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM ShiftTypes WHERE id = %s", (shift_type_id,))
                result = cursor.fetchone()
                return result['name'] if result else f"Тип {shift_type_id}"
    except Exception as e:
        print(f"[ERROR] get_shift_type_name: {e}")
        return f"Тип {shift_type_id}"


def record_actual_shift_start(tguser, actual_start_time, shift_date=None):
    """Записывает фактическое время заступления на смену"""
    try:
        # Получаем имя пользователя
        user_data = get_user_data(tguser)
        if not user_data:
            print(f"[ERROR] record_actual_shift_start: User not found for tguser {tguser}")
            return False
            
        user_name = user_data[0]  # name из кортежа (name, phone, grade)
        
        # Если дата смены не указана, используем текущую дату
        if not shift_date:
            shift_date = datetime.now().date()
            
        # Форматируем время если это строка
        if isinstance(actual_start_time, str):
            try:
                actual_start_time = datetime.strptime(actual_start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    actual_start_time = datetime.strptime(actual_start_time, "%H:%M:%S")
                    # Если указано только время, добавляем текущую дату
                    actual_start_time = actual_start_time.replace(
                        year=shift_date.year, 
                        month=shift_date.month, 
                        day=shift_date.day
                    )
                except ValueError:
                    print(f"[ERROR] record_actual_shift_start: Invalid time format {actual_start_time}")
                    return False
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Проверяем, есть ли уже запись для этого пользователя и даты
                cursor.execute("""
                    SELECT id FROM ActualShiftTimes 
                    WHERE tguser = %s AND shift_date = %s
                """, (tguser, shift_date))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Обновляем существующую запись
                    cursor.execute("""
                        UPDATE ActualShiftTimes 
                        SET actual_start_time = %s, user_name = %s
                        WHERE id = %s
                    """, (actual_start_time, user_name, existing_record['id']))
                    print(f"[INFO] Updated actual shift start time for {user_name} on {shift_date}")
                else:
                    # Создаем новую запись
                    cursor.execute("""
                        INSERT INTO ActualShiftTimes (user_name, tguser, actual_start_time, shift_date)
                        VALUES (%s, %s, %s, %s)
                    """, (user_name, tguser, actual_start_time, shift_date))
                    print(f"[INFO] Recorded actual shift start time for {user_name} on {shift_date} at {actual_start_time}")
                
                conn.commit()
                return True
                
    except Exception as e:
        print(f"[ERROR] record_actual_shift_start: {e}")
        return False





def get_shift_by_user_and_date(tguser, date_obj):
    """Получает смену пользователя на определенную дату"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Получаем employee_id по tguser
                cursor.execute("SELECT id FROM Employees WHERE tguser = %s", (tguser,))
                user_row = cursor.fetchone()
                if not user_row:
                    return None
                employee_id = user_row['id']

                # Ищем смену
                cursor.execute("""
                    SELECT id, date, shift_type_id
                    FROM Schedule
                    WHERE employee_id = %s AND date = %s
                """, (employee_id, date_obj))
                return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] get_shift_by_user_and_date: {e}")
        return None


def save_shift_note(tguser, note_text):
    """Сохраняет заметку в протокол смены"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO ShiftNotes (tguser, note_text) VALUES (%s, %s)", 
                             (tguser, note_text))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] save_shift_note: {e}")
        return False


def get_shift_notes():
    """Получает заметки смены за последние 24 часа"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT ShiftNotes.note_text, ShiftNotes.timestamp, Employees.name
                    FROM ShiftNotes
                    JOIN Employees ON ShiftNotes.tguser = Employees.tguser
                    WHERE ShiftNotes.timestamp >= NOW() - INTERVAL 24 HOUR
                    ORDER BY ShiftNotes.timestamp ASC
                """)
                return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] get_shift_notes: {e}")
        return []


def save_reminder(tguser, reminder_text, reminder_time):
    """Сохраняет напоминание в базе данных"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Reminders (tguser, reminder_text, reminder_time) 
                    VALUES (%s, %s, %s)
                """, (tguser, reminder_text, reminder_time))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] save_reminder: {e}")
        return False


def get_pending_reminders():
    """Получает напоминания, которые нужно отправить"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT r.id, r.tguser, r.reminder_text, r.reminder_time, e.name
                    FROM Reminders r
                    JOIN Employees e ON r.tguser = e.tguser
                    WHERE r.is_sent = FALSE AND r.reminder_time <= NOW()
                """)
                return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] get_pending_reminders: {e}")
        return []


def mark_reminder_sent(reminder_id):
    """Помечает напоминание как отправленное"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Reminders SET is_sent = TRUE WHERE id = %s", (reminder_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] mark_reminder_sent: {e}")
        return False


def get_request_ids_from_db():
    """Получает ID заявок из базы для статистики"""
    request_ids = []
    time_differences = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT request_id, created_time, last_updated_time
                    FROM TimeToCompReq
                    WHERE created_time >= NOW() - INTERVAL 12 HOUR
                """)
                rows = cursor.fetchall()
                for row in rows:
                    request_ids.append(row['request_id'])
                    created_time = row['created_time']
                    last_updated_time = row['last_updated_time']
                    if created_time and last_updated_time:
                        time_difference = last_updated_time - created_time
                        time_differences.append(time_difference)
        
        return request_ids, time_differences
    except Exception as e:
        print(f"[ERROR] get_request_ids_from_db: {e}")
        return [], []


def create_remote_request(tguser, shift_date, reason):
    """Создает запрос на удаленку"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO RemoteWorkRequests (tguser, shift_date, reason, status, created_at)
                    VALUES (%s, %s, %s, 'pending', NOW())
                """, (tguser, shift_date, reason))
                conn.commit()
                return cursor.lastrowid
    except Exception as e:
        print(f"[ERROR] create_remote_request: {e}")
        return None


def get_remote_request(request_id):
    """Получает информацию о запросе на удаленку"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM RemoteWorkRequests WHERE id = %s", (request_id,))
                return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] get_remote_request: {e}")
        return None


def update_remote_request_approval(request_id, role, value=True):
    """Обновляет статус согласования запроса на удаленку"""
    role_mapping = {
        'lead': 'approved_by_lead',
        'manager': 'approved_by_manager'
    }
    
    if role not in role_mapping:
        return False
        
    field = role_mapping[role]
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Обновляем поле согласования
                cursor.execute(f"UPDATE RemoteWorkRequests SET {field} = %s WHERE id = %s", 
                             (1 if value else 0, request_id))
                
                # Если отклонение - сразу отклоняем весь запрос
                if not value:
                    cursor.execute("UPDATE RemoteWorkRequests SET status = 'rejected' WHERE id = %s", 
                                 (request_id,))
                else:
                    # Если одобрение - проверяем, одобрен ли хотя бы одной стороной (логика ИЛИ)
                    cursor.execute("""
                        SELECT approved_by_lead, approved_by_manager 
                        FROM RemoteWorkRequests WHERE id = %s
                    """, (request_id,))
                    result = cursor.fetchone()
                    
                    if result and (result['approved_by_lead'] == 1 or result['approved_by_manager'] == 1):
                        cursor.execute("UPDATE RemoteWorkRequests SET status = 'approved' WHERE id = %s", 
                                     (request_id,))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] update_remote_request_approval: {e}")
        return False


def approve_remote_request(request_id):
    """Одобряет запрос на удаленку"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE RemoteWorkRequests SET status = 'approved' WHERE id = %s", 
                             (request_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] approve_remote_request: {e}")
        return False


def reject_remote_request(request_id):
    """Отклоняет запрос на удаленку"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE RemoteWorkRequests SET status = 'rejected' WHERE id = %s", 
                             (request_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] reject_remote_request: {e}")
        return False


def get_monthly_remote_count(tguser, year, month):
    """Получает количество одобренных запросов на удаленку за месяц"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM RemoteWorkRequests
                    WHERE tguser = %s 
                    AND status = 'approved'
                    AND YEAR(shift_date) = %s 
                    AND MONTH(shift_date) = %s
                """, (tguser, year, month))
                result = cursor.fetchone()
                return result['count'] if result else 0
    except Exception as e:
        print(f"[ERROR] get_monthly_remote_count: {e}")
        return 0


def get_user_base_remote_limit(tguser):
    """Получает базовый лимит удаленки для пользователя в зависимости от грейда"""
    from src.config import REMOTE_MONTHLY_LIMITS_BY_GRADE, REMOTE_MONTHLY_LIMIT
    
    user_data = get_user_data(tguser)
    if not user_data:
        return REMOTE_MONTHLY_LIMIT  # Лимит по умолчанию
    
    _, _, grade = user_data
    if not grade:
        return REMOTE_MONTHLY_LIMIT  # Лимит по умолчанию
    
    # Возвращаем лимит в зависимости от грейда
    return REMOTE_MONTHLY_LIMITS_BY_GRADE.get(grade, REMOTE_MONTHLY_LIMIT)


def get_user_available_remote_limit(tguser, year, month):
    """Получает доступный лимит удаленки для пользователя с учетом расширений"""
    
    base_limit = get_user_base_remote_limit(tguser)
    extensions = get_user_remote_limit_extensions(tguser, year, month)
    return base_limit + extensions


def is_shift_remote_approved(tguser, shift_date):
    """Проверяет, одобрена ли удаленка для конкретной смены"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM RemoteWorkRequests
                    WHERE tguser = %s AND shift_date = %s AND status = 'approved'
                """, (tguser, shift_date))
                result = cursor.fetchone()
                return result is not None
    except Exception as e:
        print(f"[ERROR] is_shift_remote_approved: {e}")
        return False


def add_remote_limit_extension(tguser, added_by, reason="Административное увеличение"):
    """Добавляет дополнительный лимит удаленки пользователю"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO RemoteLimitExtensions (tguser, month, year, added_by, reason, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (tguser, datetime.now().month, datetime.now().year, added_by, reason))
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERROR] add_remote_limit_extension: {e}")
        return False


def get_user_remote_limit_extensions(tguser, year, month):
    """Получает количество дополнительных лимитов для пользователя в конкретном месяце"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM RemoteLimitExtensions
                    WHERE tguser = %s AND year = %s AND month = %s
                """, (tguser, year, month))
                result = cursor.fetchone()
                return result['count'] if result else 0
    except Exception as e:
        print(f"[ERROR] get_user_remote_limit_extensions: {e}")
        return 0
