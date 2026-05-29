#  Шпаргалка SmenaControl Bot - Быстрый справочник

##  Где что находится?

### Основные команды команды
| Команда | Файл | Функция | Описание |
|---------|------|---------|---------|
| `/start` | `command_handlers.py` | `start_command()` | Начало работы, главное меню |
| `/note` | `command_handlers.py` | `note_command()` | Создание напоминания |
| `/refresh` | `command_handlers.py` | `refresh_command()` | Обновление информации |
| Текст сообщение | `command_handlers.py` | `handle_main_message()` | Обработка меню |

### Административные команды
| Команда | Файл | Функция |
|---------|------|---------|
| `/addremoteshift` | `admin_handlers.py` | `handle_add_remote_shift()` |
| `/checktelegramids` | `admin_handlers.py` | `handle_check_telegram_ids()` |
| `/registertelegramid` | `admin_handlers.py` | `handle_register_telegram_id()` |
| `/reminderstats` | `admin_handlers.py` | `handle_reminder_stats()` |
| `/restartreminders` | `admin_handlers.py` | `handle_restart_reminder_service()` |
| `/testreminder` | `admin_handlers.py` | `handle_test_reminder()` |

---

##  Быстрый поиск функций

### Получение данных

```python
get_user_data(tguser)                      # Имя, телефон, грейд
get_telegram_id_by_tguser(tguser)         # Telegram ID
get_static_user_from_db(tguser)           # ПК username
get_sdid_name_from_db(username)           # ServiceDesk ID
get_today_shifts()                        # Смены на сегодня
get_pending_reminders()                   # Невыполненные напоминания
get_monthly_remote_count(tguser, ...)     # Использованные дни удаленки
get_user_available_remote_limit(...)      # Доступный лимит удаленки
```

### Обновление данных

```python
update_telegram_id(tguser, id)            # Сохранить Telegram ID
set_onshift(tguser)                       # Установить на смену
update_start_shift_time(tguser)           # Обновить время начала
save_shift_note(tguser, note, date)       # Сохранить заметку
save_reminder(tguser, text, time)         # Создать напоминание
mark_reminder_sent(reminder_id)           # Отметить отправленное
```

### Работа с обменом смин

```python
get_shift_exchange(user1, user2)          # Получить информацию
get_user_role_for_exchange(tguser)        # Получить роль (lead/manager/user)
save_shift_exchange(...)                  # Сохранить запрос
approve_shift_exchange(...)               # Одобрить
reject_shift_exchange(...)                # Отклонить
```

### Работа с Telegram

```python
send_telegram_message(text)               # В основной чат
send_telegram_message_tb(text)            # В TB чат
send_shift_start_notification(text)       # Уведомление о смене
```

### Работа с ServiceDesk

```python
get_current_requests_and_tasks(sd_id)    # Заявки и задачи
transfer_requests(from_id, to_id, ...)   # Передать заявки
transfer_tasks(from_id, to_id)           # Передать задачи
execute_request(req_id, action, ...)     # Выполнить заявку
```

---

##  Как добавить защиту авторизации?

### Вариант 1: Использовать декоратор `@with_auth`

```python
from src.utils.auth_decorators import with_auth

@with_auth
async def my_handler(update, context):
    # Функция автоматически проверит авторизацию
    pass

# В main.py:
app.add_handler(CommandHandler("command", with_auth(my_handler)))
```

### Вариант 2: Для callback queries используйте `@group_ignore`

```python
from src.utils.auth_decorators import group_ignore

@group_ignore
async def my_callback_handler(update, context):
    # Игнорирует сообщения из групп
    pass

# В main.py:
app.add_handler(CallbackQueryHandler(group_ignore(my_callback_handler)))
```

---

##  Структура таблиц БД

### Employees (сотрудники)
```
id, name, tguser, telegram_id, username, TechnitianIdSd, 
onshift, grade, web_role, active, phone, mail, position, ...
```

### Reminders (напоминания)
```
id, tguser, reminder_text, reminder_time, created_time, is_sent
```

### RemoteWorkRequests (удаленка)
```
id, tguser, shift_date, reason, status, approved_by_lead, 
approved_by_manager, created_at
```

### ShiftExchanges (обмены смин)
```
id, user_from, user_to, shift_date, status, reason, 
approved_by_lead, approved_by_manager, created_at
```

### ActualShiftTimes (фактическое начало)
```
id, user_name, tguser, actual_start_time, shift_date, created_at
```

---

##  Переменные окружения (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_CHAT_ID_TB=
THREAD_ID=

# БД 1
DB_HOST=
DB_USER=
DB_PASS=
DB_NAME=

# БД 2
DB_HOST_2=
DB_USER_2=
DB_PASS_2=
DB_NAME_2=

# API
LOGIN_URL=
ACTION_URL=
SD_API_TOKEN=

# Уведомления
REMOTE_NOTIFICATIONS_SEND_TO_MAIN_CHAT=
REMOTE_NOTIFICATIONS_SEND_TO_TB_CHAT=
REMOTE_NOTIFICATIONS_DEBUG_MODE=
```

---

##  Конфигурация в config.py

### Роли и права
```python
ADMIN_ROLES = {
    "lead_engineer": "username",
    "manager": "username"
}

REMOTE_NO_APPROVAL_USERS = ["username1", "username2"]
ALLOWED_WORKLOG_OWNERS = {"Имя 1", "Имя 2"}
```

### Запрещенные типы смин
```python
FORBIDDEN_SHIFT_TYPES = [12, 10, 13, 100]
```

---

##  Форматирование сообщений Telegram

### HTML формат
```html
<b>Жирный</b>
<i>Курсив</i>
<u>Подчеркивание</u>
<s>Зачеркивание</s>
<code>Моноширинный</code>
<a href="https://link.com">Ссылка</a>
```

### Markdown формат
```markdown
*Жирный*
_Курсив_
~Зачеркивание~
`Код`
[Ссылка](https://link.com)
```

---

##  Классические паттерны использования

### Паттерн 1: Получить данные пользователя и проверить

```python
tguser = update.effective_user.username
user_data = get_user_data(tguser)

if not user_data:
    await update.message.reply_text(" Пользователь не найден")
    return

name, phone, grade = user_data
```

### Паттерн 2: Обновить БД и отправить уведомление

```python
# Обновляем
success = set_onshift(tguser)

if success:
    # Логируем
    log_shift_exchange('info', 'Смена началась', user=tguser, action='start_shift')
    
    # Уведомляем
    await update.message.reply_text(" Смена началась!")
    send_telegram_message(f"@{tguser} начал смену")
```

### Паттерн 3: Обработка callback с валидацией

```python
query = update.callback_query
data = query.data

if data == "my_action":
    try:
        # Выполняем действие
        result = do_something()
        
        # Отправляем результат
        await query.edit_message_text(" Успешно!")
    except Exception as e:
        await query.edit_message_text(f" Ошибка: {e}")
```

### Паттерн 4: Работа с фоновыми задачами

```python
async def my_background_task():
    while True:
        try:
            # Делаем что-то
            data = get_something()
            
            # Обрабатываем
            process(data)
            
            # Ждем перед следующей итерацией
            await asyncio.sleep(30)
        except Exception as e:
            print(f"[ERROR] {e}")

# В main.py:
async def post_init(app):
    asyncio.create_task(my_background_task())
    
app.post_init = post_init
```

---

##  Частые ошибки и решения

| Ошибка | Решение |
|--------|--------|
| `Unauthorized` | Проверить `TELEGRAM_BOT_TOKEN` |
| `Access denied` | Добавить пользователя в БД |
| `No username` | Установить username в Telegram |
| `Connection timeout` | Проверить `DB_HOST`, port |
| `No reminders` | Напоминания не созданы или уже отправлены |

---

##  Структура проекта (минимум)

```
SmenaControl/
 main.py                    # ТОЧКА ВХОДА
 .env                       # СЕКРЕТЫ (не в Git!)
 requirements.txt           # Зависимости

 src/
    config.py             # Конфигурация
    database/
       db_operations.py  # Основные операции
       shift_exchange.py # Обмены смин
    handlers/             # Обработчики
    services/             # Сервисы
    middleware/           # Авторизация
    utils/                # Утилиты

 docs/
     PROJECT_DOCUMENTATION.md  # Полная документация
     ARCHITECTURE_DIAGRAMS.md   # Диаграммы
     API_USAGE_GUIDE.md         # Примеры
     QUICK_REFERENCE.md         # Эта шпаргалка
```

---

##  Быстрый старт

### 1⃣ Подготовка
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2⃣ Конфигурация
```bash
# Создать .env с переменными
cp .env.example .env
# Отредактировать .env
```

### 3⃣ База данных
```bash
mysql -u root -p
CREATE DATABASE work_schedule_db CHARACTER SET utf8mb4;
mysql -u root -p work_schedule_db < CreateDB.sql
```

### 4⃣ Запуск
```bash
python main.py
```

---

##  Полезные команды

### Проверка подключения БД
```python
from src.database.db_operations import get_user_data
result = get_user_data("test_user")
print(" БД работает" if result else " Ошибка БД")
```

### Проверка Telegram бота
```bash
# В браузере:
https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe
```

### Просмотр логов
```bash
tail -f bot.log
# или
Get-Content bot.log -Wait  # Windows PowerShell
```

---

##  Где искать информацию?

| Что нужно | Где искать |
|----------|-----------|
| Общее описание | [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) |
| Диаграммы и схемы | [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) |
| Примеры кода | [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) |
| Быстрый поиск | **Вы здесь**  |
| Исходный код | `/src/` папка |
| SQL запросы | `/src/database/` |
| Логирование | `*.log` файлы |

---

##  Важные ссылки в коде

### Entry Point
- `main.py` - Запуск приложения

### Конфигурация
- `src/config.py` - Все переменные

### Основной функционал
- `src/handlers/command_handlers.py` - Команды
- `src/database/db_operations.py` - Работа с БД
- `src/services/telegram_service.py` - Отправка сообщений

### Авторизация
- `src/middleware/auth_middleware.py` - Проверка доступа
- `src/utils/auth_decorators.py` - Декораторы

---

*Последнее обновление: 06.05.2026*
*Версия: 1.0*

** Помните:** Все функции имеют примеры в [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)!
