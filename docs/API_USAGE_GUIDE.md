#  Руководство по использованию API SmenaControl Bot

##  Содержание

1. [Работа с данными пользователя](#работа-с-данными-пользователя)
2. [Работа со сменами](#работа-со-сменами)
3. [Работа с обменом смен](#работа-с-обменом-смин)
4. [Работа с удаленной работой](#работа-с-удаленной-работой)
5. [Работа с напоминаниями](#работа-с-напоминаниями)
6. [Работа с Telegram API](#работа-с-telegram-api)
7. [Работа с ServiceDesk API](#работа-с-servicedesk-api)
8. [Обработка ошибок](#обработка-ошибок)

---

##  Работа с данными пользователя

### Получение данных пользователя

```python
from src.database.db_operations import get_user_data

# Получить все данные пользователя по Telegram username
user_data = get_user_data("username")

if user_data:
    name, phone, grade = user_data
    print(f"Имя: {name}")
    print(f"Телефон: {phone}")
    print(f"Грейд: {grade}")  # Джуниор, Mid, Adv
else:
    print("Пользователь не найден")
```

---

### Получение Telegram ID

```python
from src.database.db_operations import get_telegram_id_by_tguser

telegram_id = get_telegram_id_by_tguser("username")
if telegram_id:
    print(f"Telegram ID: {telegram_id}")
```

---

### Обновление Telegram ID

```python
from src.database.db_operations import update_telegram_id

success = update_telegram_id("username", 123456789)
if success:
    print(" Telegram ID обновлен")
else:
    print(" Ошибка при обновлении")
```

---

### Получение ПК username по Telegram username

```python
from src.database.db_operations import get_static_user_from_db

pc_username = get_static_user_from_db("tguser")
print(f"ПК username: {pc_username}")
```

---

### Получение ServiceDesk ID техника

```python
from src.database.db_operations import get_sdid_name_from_db

sd_id = get_sdid_name_from_db("pc_username")
print(f"ServiceDesk ID: {sd_id}")
```

---

##  Работа со сменами

### Установить пользователя на смену

```python
from src.database.db_operations import set_onshift

# Устанавливает пользователя как дежурного
# Все остальные пользователи становятся недежурными
success = set_onshift("username")

if success:
    print(" Пользователь установлен на смену")
    print(" Все его заявки переведены на ServiceDesk")
```

---

### Обновить время начала смены

```python
from src.database.db_operations import update_start_shift_time
from datetime import datetime

# Обновляет LastLoginTime в обеих БД
success = update_start_shift_time("username")

if success:
    print(f" Время смены обновлено: {datetime.now()}")
```

---

### Получить смены на конкретную дату

```python
from src.database.db_operations import get_today_shifts

# Получить смены на сегодня
shifts = get_today_shifts()

for shift in shifts:
    print(f" {shift['name']}")
    print(f" {shift['shift_date']}")
    print(f" {shift['shift_time']}")
    print(f" Тип: {shift['shift_type_id']}")
    print("---")
```

---

### Сохранить заметку о смене

```python
from src.database.db_operations import save_shift_note
from datetime import date

# Сохранить заметку
success = save_shift_note(
    tguser="username",
    note_text="Проблема с сервером решена",
    note_date=date.today()
)

if success:
    print(" Заметка сохранена")
```

---

##  Работа с обменом смин

### Получить информацию об обмене

```python
from src.database.shift_exchange import get_shift_exchange

# Получить информацию об обмене между двумя пользователями
exchange = get_shift_exchange("user_a", "user_b")

if exchange:
    print(f"Статус: {exchange['status']}")
    print(f"Дата: {exchange['shift_date']}")
    print(f"Причина: {exchange['reason']}")
    print(f"Одобрено Lead: {exchange['approved_by_lead']}")
    print(f"Одобрено Manager: {exchange['approved_by_manager']}")
```

---

### Получить роль пользователя для обмена

```python
from src.database.shift_exchange import get_user_role_for_exchange

# Получить роль пользователя (lead, manager, user)
role = get_user_role_for_exchange("username")

if role == "lead_engineer":
    print(" Это старший инженер")
elif role == "manager":
    print(" Это менеджер")
else:
    print(" Обычный пользователь")
```

---

### Сохранить запрос на обмен

```python
from src.database.shift_exchange import save_shift_exchange
from datetime import date

# Сохранить запрос на обмен смины
success = save_shift_exchange(
    user_from="user_a",
    user_to="user_b",
    shift_date=date.today(),
    reason="Личные дела",
    status="pending"
)

if success:
    print(" Запрос на обмен сохранен")
    print(" Ожидается согласование Lead Engineer")
```

---

### Одобрить обмен смины

```python
from src.database.shift_exchange import approve_shift_exchange

# Одобрить обмен смины (Lead Engineer)
success = approve_shift_exchange(
    exchange_id=123,
    approved_by="lead",  # или "manager"
    status="approved"
)

if success:
    print(" Обмен одобрен")
```

---

### Отклонить обмен смины

```python
from src.database.shift_exchange import reject_shift_exchange

# Отклонить обмен смины
success = reject_shift_exchange(
    exchange_id=123,
    rejected_by="lead",  # или "manager"
)

if success:
    print(" Обмен отклонен")
    print(" Пользователи получили уведомление")
```

---

##  Работа с удаленной работой

### Проверить лимит удаленной работы

```python
from src.database.db_operations import get_user_available_remote_limit
from datetime import datetime

current_date = datetime.now()

# Получить доступный лимит удаленной работы на месяц
available_limit = get_user_available_remote_limit(
    tguser="username",
    month=current_date.month,
    year=current_date.year
)

print(f" Доступно дней удаленки: {available_limit}")

if available_limit > 0:
    print(f" Можно работать удаленно {available_limit} дней")
else:
    print(" Лимит исчерпан, требуется согласование менеджера")
```

---

### Получить количество использованных дней

```python
from src.database.db_operations import get_monthly_remote_count

# Получить количество уже использованных дней удаленки
used_count = get_monthly_remote_count(
    tguser="username",
    month=5,
    year=2026
)

print(f"Использовано дней: {used_count}")
```

---

##  Работа с напоминаниями

### Получить невыполненные напоминания

```python
from src.database.db_operations import get_pending_reminders

# Получить все напоминания, которые нужно отправить
pending = get_pending_reminders()

print(f" Всего напоминаний к отправке: {len(pending)}")

for reminder in pending:
    print(f" От: {reminder['tguser']}")
    print(f" Время: {reminder['reminder_time']}")
    print(f" Текст: {reminder['reminder_text']}")
    print(f" Отправлено: {reminder['is_sent']}")
    print("---")
```

---

### Сохранить напоминание

```python
from src.database.db_operations import save_reminder
from datetime import datetime

# Сохранить новое напоминание
reminder_id = save_reminder(
    tguser="username",
    reminder_text="Провести встречу с клиентом",
    reminder_time=datetime(2026, 5, 7, 14, 30),  # 7 мая, 14:30
)

print(f" Напоминание создано с ID: {reminder_id}")
```

---

### Отметить напоминание как отправленное

```python
from src.database.db_operations import mark_reminder_sent

# Отметить напоминание как отправленное
success = mark_reminder_sent(reminder_id=123)

if success:
    print(" Напоминание отмечено как отправленное")
```

---

### Фоновый сервис напоминаний

```python
# В main.py уже инициализируется автоматически:

async def post_init(app):
    """Запуск фоновых задач"""
    asyncio.create_task(reminder_checker())
    print("[INFO] Background tasks initialized")

# reminder_service.py постоянно проверяет БД на новые напоминания
# Каждые 30 секунд:
# 1. Получает список невыполненных напоминаний
# 2. Отправляет каждое в групповой чат
# 3. Помечает как отправленное
```

---

##  Работа с Telegram API

### Отправить сообщение в главный чат

```python
from src.services.telegram_service import send_telegram_message

message = """ <b>Новое уведомление</b>

 <b>От:</b> Иван Петров
 <b>Сообщение:</b> Смена начата"""

success = send_telegram_message(message)

if success:
    print(" Сообщение отправлено")
else:
    print(" Ошибка при отправке")
```

---

### Отправить сообщение в чат техподдержки

```python
from src.services.telegram_service import send_telegram_message_tb

message = """ <b>Важное сообщение для техподдержки</b>

Произошла проблема с системой"""

success = send_telegram_message_tb(message)
```

---

### Отправить уведомление о начале смены

```python
from src.services.telegram_service import send_shift_start_notification_to_groups

message = """ <b>Смена началась!</b>

 <b>На смене:</b> Иван Петров (@ivanov)
 <b>Заявки:</b> 5 активных
 <b>Время:</b> 09:00 - 21:00"""

success = send_shift_start_notification_to_groups(message)
```

---

### Форматирование сообщений

```python
# HTML формат
html_message = """<b>Жирный текст</b>
<i>Курсив</i>
<u>Подчеркивание</u>
<s>Зачеркивание</s>
<code>Монотон</code>
<pre>Блок кода</pre>

<a href="https://example.com">Ссылка</a>"""

# Markdown формат
markdown_message = """*Жирный текст*
_Курсив_
~Зачеркивание~
`Код`
```
Блок кода
```
[Ссылка](https://example.com)"""

# Используется в параметре parse_mode: 'HTML' или 'Markdown'
```

---

##  Работа с ServiceDesk API

### Получить заявки техника

```python
from src.services.servicedesk_api import get_current_requests_and_tasks

# Получить все заявки и задачи техника
sd_id = 12345  # ServiceDesk ID техника

requests, tasks = get_current_requests_and_tasks(sd_id)

print(f" Заявок: {len(requests)}")
for request in requests:
    print(f"  ID: {request['id']}, Статус: {request['status']}")

print(f" Задач: {len(tasks)}")
for task in tasks:
    print(f"  ID: {task['id']}, Приоритет: {task['priority']}")
```

---

### Передать заявки другому технику

```python
from src.services.servicedesk_api import transfer_requests

# Передать заявки от одного техника к другому
success = transfer_requests(
    from_sd_id=12345,  # ServiceDesk ID от кого
    to_sd_id=67890,    # ServiceDesk ID кому
    status_list=[1, 2, 3]  # Статусы заявок для передачи
)

if success:
    print(" Заявки успешно переданы")
else:
    print(" Ошибка при передаче")
```

---

### Передать задачи

```python
from src.services.servicedesk_api import transfer_tasks

# Передать все задачи
success = transfer_tasks(
    from_sd_id=12345,
    to_sd_id=67890
)

if success:
    print(" Задачи успешно переданы")
```

---

### Выполнить заявку

```python
from src.services.servicedesk_api import execute_request

# Выполнить заявку (закрыть)
success = execute_request(
    request_id=54321,
    action="close",  # или "complete"
    comment="Проблема решена"
)

if success:
    print(" Заявка выполнена")
```

---

##  Обработка ошибок

### Обработка ошибок БД

```python
from src.database.db_operations import get_user_data
import pymysql

try:
    user_data = get_user_data("username")
    if user_data:
        name, phone, grade = user_data
    else:
        print(" Пользователь не найден")
except pymysql.MySQLError as e:
    print(f" Ошибка БД: {e}")
    # Подключиться к резервной БД или перезапустить
except Exception as e:
    print(f" Неизвестная ошибка: {e}")
```

---

### Обработка ошибок Telegram

```python
from src.services.telegram_service import send_telegram_message

try:
    message = "Тестовое сообщение"
    success = send_telegram_message(message)
    
    if not success:
        print(" Сообщение не отправлено (возможно, проблема с сетью)")
except Exception as e:
    print(f" Ошибка Telegram API: {e}")
```

---

### Обработка ошибок авторизации

```python
from src.middleware.auth_middleware import check_user_access
from telegram import Update

async def safe_handler(update: Update, context):
    """Безопасный обработчик с обработкой ошибок"""
    try:
        # Проверяем авторизацию
        if not await check_user_access(update, context):
            return  # Пользователь не авторизован
        
        # Наша логика
        tguser = update.effective_user.username
        
        # ... код ...
        
    except ValueError as e:
        await update.message.reply_text(f" Ошибка значения: {e}")
    except KeyError as e:
        await update.message.reply_text(f" Отсутствует ключ: {e}")
    except Exception as e:
        await update.message.reply_text(f" Неожиданная ошибка: {e}")
```

---

### Логирование ошибок

```python
from src.utils.logger import log_shift_exchange

# Логировать ошибку
log_shift_exchange(
    level='error',
    message='Ошибка при обновлении смены',
    user='username',
    action='start_shift',
    details={'error_code': 500, 'error_msg': 'Database connection timeout'}
)

# Логировать предупреждение
log_shift_exchange(
    level='warning',
    message='Пользователь без username',
    user='unknown',
    action='auth_check'
)

# Логировать информацию
log_shift_exchange(
    level='info',
    message='Смена успешно начата',
    user='username',
    action='start_shift'
)
```

---

##  Создание собственного обработчика

### Пример: Новая команда `/status`

```python
# В src/handlers/command_handlers.py добавить:

from telegram import Update
from telegram.ext import ContextTypes
from src.utils.auth_decorators import with_auth
from src.database.db_operations import get_user_data, get_today_shifts
from src.services.telegram_service import send_telegram_message

@with_auth
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показать текущий статус"""
    
    tguser = update.effective_user.username
    
    try:
        # Получаем данные пользователя
        user_data = get_user_data(tguser)
        
        if not user_data:
            await update.message.reply_text(
                " Не удалось получить информацию о пользователе"
            )
            return
        
        name, phone, grade = user_data
        
        # Получаем сегодняшние смены
        today_shifts = get_today_shifts()
        
        # Формируем ответ
        response = f""" <b>Статус</b>

 <b>Пользователь:</b> {name}
 <b>Грейд:</b> {grade}
 <b>Телефон:</b> {phone}

 <b>Смены на сегодня:</b>
"""
        
        if today_shifts:
            for shift in today_shifts:
                response += f"  • {shift['name']} ({shift['shift_time']})\n"
        else:
            response += "  Смен нет\n"
        
        await update.message.reply_text(response, parse_mode='HTML')
        
    except Exception as e:
        print(f"[ERROR] status_command: {e}")
        await update.message.reply_text(
            " Произошла ошибка при получении статуса.\n"
            "Попробуйте еще раз."
        )

# В main.py добавить:
from src.handlers.command_handlers import status_command

app.add_handler(CommandHandler("status", with_auth(status_command)))
```

---

### Пример: Новый callback handler

```python
# В src/handlers/callback_handlers.py добавить:

async def handle_my_action(update, context):
    """Обработчик для кастомной кнопки"""
    
    query = update.callback_query
    data = query.data
    
    if data.startswith("my_action_"):
        action_type = data.split("_")[2]
        
        if action_type == "save":
            await query.edit_message_text(
                text=" Данные сохранены"
            )
        elif action_type == "cancel":
            await query.edit_message_text(
                text=" Отменено"
            )

# В handle_callback_query() добавить:
elif data.startswith("my_action_"):
    await handle_my_action(update, context)
```

---

##  Примеры работы со статистикой

### Получить статистику

```python
from src.services.statistics import get_current_statistics

# Получить текущую статистику
stats = get_current_statistics()

print(f" Статистика:")
print(f"Активных техников: {stats['active_technicians']}")
print(f"Среднее время ответа: {stats['avg_response_time']} мин")
print(f"Решено заявок сегодня: {stats['resolved_today']}")
```

---

### Получить статистику по пользователю

```python
from src.services.statistics import get_technician_statistics

# Получить статистику техника
user_stats = get_technician_statistics("username")

print(f" Статистика для: username")
print(f" Дни на смене: {user_stats['shift_days']}")
print(f" Всего заявок: {user_stats['total_requests']}")
print(f" Решено заявок: {user_stats['resolved_requests']}")
print(f" Среднее время: {user_stats['avg_time']} мин")
```

---

*Руководство актуально на: 06.05.2026*
*Версия: 1.0*
