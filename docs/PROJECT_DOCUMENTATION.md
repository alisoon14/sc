#  Полная документация проекта SmenaControl Bot

##  Содержание

1. [Обзор системы](#обзор-системы)
2. [Архитектура приложения](#архитектура-приложения)
3. [Компоненты системы](#компоненты-системы)
4. [Структура папок](#структура-папок)
5. [База данных](#база-данных)
6. [Рабочие процессы](#рабочие-процессы)
7. [Интеграции с внешними сервисами](#интеграции-с-внешними-сервисами)
8. [Безопасность и авторизация](#безопасность-и-авторизация)
9. [Диаграмма взаимодействия компонентов](#диаграмма-взаимодействия-компонентов)
10. [Инструкция по запуску](#инструкция-по-запуску)

---

##  Обзор системы

**SmenaControl Bot** - это Telegram бот для автоматизации управления рабочими сменами в технической поддержке.

### Основные функции:

-  **Управление сменами**: заступление на смену с автоматическим переводом заявок
-  **Обмен сменами**: механизм обмена сменами между сотрудниками с согласованием
-  **Удаленная работа**: система запросов и согласований удаленных смен
-  **Напоминания**: создание и отправка напоминаний в групповой чат
-  **Статистика**: отчеты по работе техподдержки
-  **Административные функции**: управление лимитами и правами доступа

### Стек технологий:

```
Backend:
 Python 3.7+          # Язык программирования
 python-telegram-bot  # Библиотека для работы с Telegram API
 PyMySQL              # Драйвер для работы с MySQL базой данных
 requests             # HTTP библиотека для API запросов
 asyncio              # Асинхронное программирование
 python-dotenv        # Загрузка переменных окружения

Database:
 MySQL/MariaDB        # Основная база данных (производство)
 MySQL/MariaDB        # Вторая база данных (ServiceDesk интеграция)

External Services:
 Telegram Bot API     # Для отправки сообщений и работы с ботом
 ServiceDesk API v3   # Для управления заявками и задачами
 Login/Action URLs    # Для аутентификации и выполнения действий
```

---

##  Архитектура приложения

### Многоуровневая архитектура:

```

                    TELEGRAM USERS                            

                             
                    Telegram Bot API
                             

                    MAIN.PY - Точка входа                      
  - Инициализация приложения                                   
  - Регистрация обработчиков                                   
  - Запуск polling                                             
  - Инициализация фоновых задач                                

                             
        
                                                
                                                
    
  MIDDLEWARE          HANDLERS            SERVICES       
  AUTH LAYER         (обработчики)       (сервисы)       
    
                                                  
                 
                                                
                                                
    
            DATABASE LAYER (БД операции)                 
      - Работа с двумя БД                               
      - Запросы и обновления данных                      
      - Управление состоянием пользователей             
    
                         
        
                                        
                                        
              
     MySQL         MySQL 2        Telegram 
     DB 1          (Backup)       API      
              
```

---

##  Компоненты системы

### 1. **Точка входа (`main.py`)**

Главный файл приложения, отвечающий за:
- Инициализацию Telegram Bot API
- Регистрацию всех обработчиков команд и сообщений
- Добавление middleware для авторизации
- Запуск polling (постоянное прослушивание сообщений)
- Инициализацию фоновых задач

**Ключевые функции:**
```python
def main():
    # Создание приложения
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", with_auth(start)))
    app.add_handler(MessageHandler(...))
    
    # Инициализация фоновых задач
    app.post_init = post_init  # запуск reminder_checker
    
    # Запуск
    app.run_polling()
```

---

### 2. **Конфигурация (`src/config.py`)**

Центральный файл с конфигурацией, содержит:

**Переменные окружения:**
```python
# Telegram
TELEGRAM_BOT_TOKEN      # Токен бота
TELEGRAM_CHAT_ID        # ID главного чата
TELEGRAM_CHAT_ID_TB     # ID чата техподдержки
THREAD_ID               # ID потока сообщений

# Базы данных
DB_HOST, DB_USER, DB_PASS, DB_NAME          # Основная БД
DB_HOST_2, DB_USER_2, DB_PASS_2, DB_NAME_2  # Резервная БД

# API
LOGIN_URL, ACTION_URL   # Для аутентификации
SD_API_TOKEN            # ServiceDesk API токен
```

**Константы:**
```python
FORBIDDEN_SHIFT_TYPES        # Типы смен, запрещенные к обмену
ADMIN_ROLES                  # Администраторские роли
SHIFT_EXCHANGE_ROLES         # Роли для согласования обменов
REMOTE_REQUEST_ROLES         # Роли для согласования удаленки
REMOTE_NO_APPROVAL_USERS     # Пользователи без требования подтверждения
ALLOWED_WORKLOG_OWNERS       # Разрешенные владельцы рабочих логов
```

---

### 3. **Слой базы данных (`src/database/`)**

#### **3.1 `db_operations.py` - Основные операции с БД**

Модуль для работы с MySQL базой данных.

**Основные функции:**

| Функция | Описание | Параметры | Возвращает |
|---------|---------|-----------|-----------|
| `get_db_connection()` | Создает подключение к основной БД | - | Connection |
| `get_db_connection_2()` | Создает подключение ко второй БД | - | Connection |
| `get_user_data(tguser)` | Получает данные пользователя | tguser | (name, phone, grade) |
| `get_telegram_id_by_tguser(tguser)` | Получает Telegram ID | tguser | telegram_id |
| `update_telegram_id(tguser, telegram_id)` | Сохраняет Telegram ID | tguser, id | bool |
| `set_onshift(tguser)` | Устанавливает пользователя дежурным | tguser | bool |
| `update_start_shift_time(tguser)` | Обновляет время начала смены | tguser | bool |
| `get_static_user_from_db(tguser)` | Получает username пользователя | tguser | username |
| `get_today_shifts()` | Получает смены на сегодня | - | list[dict] |
| `get_pending_reminders()` | Получает невыполненные напоминания | - | list[dict] |
| `mark_reminder_sent(reminder_id)` | Помечает напоминание как отправленное | id | bool |

**Пример использования:**
```python
from src.database.db_operations import get_user_data, set_onshift

# Получаем данные пользователя
user_info = get_user_data("username")  # ('Иван Петров', '79999999999', 'Mid')

# Устанавливаем пользователя на смену
success = set_onshift("username")      # True/False
```

---

#### **3.2 `shift_exchange.py` - Операции обмена смен**

Специализированный модуль для управления обменом сменами.

**Основные функции:**
- `get_shift_exchange(user1, user2)` - Получает информацию об обмене смен
- `get_user_role_for_exchange(tguser)` - Получает роль пользователя (lead, manager, user)
- `save_shift_exchange(...)` - Сохраняет запрос на обмен
- `approve_shift_exchange(...)` - Одобряет обмен
- `reject_shift_exchange(...)` - Отклоняет обмен

**Процесс обмена смен:**
```
1. Пользователь инициирует обмен
   ↓
2. Запрос сохраняется в БД со статусом "pending"
   ↓
3. Старший инженер (lead_engineer) получает уведомление
   ↓
4. Lead одобряет → Запрос идет на согласование руководителю
   ↓
5. Менеджер одобряет → Обмен завершен
   ↓
6. Если кто-то отклонил → Обмен отклонен
```

---

### 4. **Обработчики (`src/handlers/`)**

Модули, обрабатывающие команды и сообщения пользователей.

#### **4.1 `command_handlers.py` - Основные команды**

**Команды:**

| Команда | Описание | Тип | Обработчик |
|---------|---------|------|-----------|
| `/start` | Начало работы с ботом | Command | `start_command()` |
| `/note` | Создание заметки/напоминания | Command | `note_command()` |
| `/refresh` | Обновление информации | Command | `refresh_command()` |
| Text сообщения | Обработка главного меню | Message | `handle_main_message()` |

**Функция `start_command()`:**
```python
async def start_command(update, context):
    """
    Запускается при команде /start
    - Сохраняет Telegram ID пользователя
    - Получает информацию о пользователе
    - Показывает смены на сегодня
    - Выводит главное меню
    """
    tguser = update.effective_user.username
    telegram_id = update.effective_user.id
    
    # Сохраняем ID
    update_telegram_id(tguser, telegram_id)
    
    # Получаем данные и смены
    user_data = get_user_data(tguser)
    today_shifts = get_today_shifts()
    
    # Отправляем сообщение с главным меню
    await update.message.reply_text(
        message_text,
        reply_markup=get_main_menu_keyboard()
    )
```

**Главное меню включает:**
-  Заступить на смену
-  Обменять смену
-  Работать удаленно
-  Создать напоминание
-  Статистика
-  Администраторские функции (только для админов)

---

#### **4.2 `admin_handlers.py` - Административные команды**

**Команды для администраторов:**

| Команда | Описание | Доступ |
|---------|---------|--------|
| `/addremoteshift` | Добавить удаленную смену | Lead/Manager |
| `/checktelegramids` | Проверить Telegram ID пользователей | Admin |
| `/registertelegramid` | Зарегистрировать Telegram ID | Admin |
| `/reminderstats` | Статистика напоминаний | Admin |
| `/restartreminders` | Перезапустить сервис напоминаний | Admin |
| `/testreminder` | Отправить тестовое напоминание | Admin |

---

#### **4.3 `callback_handlers.py` - Обработка inline кнопок**

Обработчик для кнопок, создаваемых Telegram Bot API.

```python
async def handle_callback_query(update, context):
    """
    Обрабатывает клики по inline кнопкам
    """
    query = update.callback_query
    data = query.data  # Данные кнопки
    
    # В зависимости от data выполняем действие
    if data == "start_shift":
        await start_shift_handler(...)
    elif data == "exchange_shift":
        await shift_exchange_handler(...)
    # и т.д.
```

---

#### **4.4 `reminder_handler.py` - Обработка напоминаний**

Управление созданием и отправкой напоминаний.

**Процесс создания напоминания:**
```
1. Пользователь выбирает "Создать напоминание"
   ↓
2. Вводит текст напоминания
   ↓
3. Выбирает дату и время
   ↓
4. Напоминание сохраняется в БД (is_sent = 0)
   ↓
5. Фоновый сервис проверяет напоминания каждые 30 сек
   ↓
6. Когда время пришло - отправляет в групповой чат
   ↓
7. Помечает как отправленное (is_sent = 1)
```

---

#### **4.5 `shift_exchange_handler.py` - Обмен сменами**

Управление процессом обмена сменами между пользователями.

**Процесс:**
```
Пользователь A          Система           Lead Engineer      Manager
                                                              
     Инициирует обмен →                                    
                           Сохраняет →                   
                                                              
                                         Получает         
                                         уведомление        
                                                
                                                              
                                    Одобрить/Отклонить    
                                        (callback query)      
                              Если одобрил → Запрос идет к →
                                                            
                                              Одобрить/Отклонить 
                                                  (callback query)   
                                                                    
                                              ЗАВЕРШЕНО → 
     Уведомление 
```

---

#### **4.6 `remote_work_handler.py` - Удаленная работа**

Управление запросами на удаленную работу.

**Статусы удаленной работы:**
- `pending` - В ожидании согласования
- `approved` - Одобрено
- `rejected` - Отклонено

**Процесс согласования:**
```
1. Пользователь запрашивает удаленную работу
2. Проверяется лимит удаленных дней в месяце
3. Если есть лимит - требуется согласование:
   - Lead Engineer (обязательно)
   - Manager (обязательно)
4. Если пользователь в списке REMOTE_NO_APPROVAL_USERS:
   - Одобрение пропускается автоматически
5. Статус обновляется, пользователь получает уведомление
```

---

#### **4.7 `shift_operations.py` - Операции со сменами**

Функции для работы со сменами.

**Основные операции:**
- `start_shift(tguser)` - Начать смену
- `transfer_requests(from_user, to_user)` - Передать заявки другому пользователю
- `get_current_shift_info()` - Получить информацию о текущей смене

---

### 5. **Сервисы (`src/services/`)**

Модули для работы с внешними сервисами и фоновыми задачами.

#### **5.1 `telegram_service.py` - Работа с Telegram API**

**Основные функции:**

```python
send_telegram_message(message)
    # Отправляет сообщение в основной чат

send_telegram_message_tb(message)
    # Отправляет сообщение в чат техподдержки

send_shift_start_notification_to_groups(message)
    # Отправляет уведомление о начале смены (принудительно)

send_message_to_user(telegram_id, message)
    # Отправляет личное сообщение пользователю
```

**Параметры сообщения:**
```python
{
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message_text,
    'parse_mode': 'HTML'  # или 'Markdown'
}
```

---

#### **5.2 `reminder_service.py` - Сервис напоминаний**

**Фоновая задача, которая:**
1. Запускается при инициализации приложения
2. Каждые 30 секунд проверяет БД на невыполненные напоминания
3. Отправляет напоминания в групповой чат
4. Помечает напоминания как отправленные

**Основные функции:**

```python
async def reminder_checker():
    """
    Бесконечный цикл проверки напоминаний
    """
    while True:
        pending_reminders = get_pending_reminders()
        for reminder in pending_reminders:
            await process_reminder(reminder)
        await asyncio.sleep(30)  # Проверяем каждые 30 сек

async def process_reminder(reminder):
    """
    Обрабатывает одно напоминание
    - Формирует сообщение
    - Отправляет в чат
    - Помечает как отправленное в БД
    """
```

---

#### **5.3 `servicedesk_api.py` - Интеграция с ServiceDesk**

**Функции для работы с API ServiceDesk:**

```python
get_current_requests_and_tasks(technician_sd_id)
    # Получает список заявок и задач техника

transfer_requests(from_id, to_id, status_list)
    # Передает заявки от одного техника к другому

transfer_tasks(from_id, to_id)
    # Передает задачи от одного техника к другому

get_request_info(request_id)
    # Получает информацию о конкретной заявке
```

**API endpoints:**
```
GET  /api/v3/requests?technician_id=X    # Заявки техника
POST /api/v3/requests/{id}/execute       # Выполнить заявку
GET  /api/v3/tasks?technician_id=X       # Задачи техника
POST /api/v3/tasks/{id}/execute          # Выполнить задачу
```

---

#### **5.4 `statistics.py` - Сбор статистики**

**Функции для получения статистики:**

```python
get_current_statistics()
    # Получает текущую статистику:
    # - Кол-во активных техников
    # - Среднее время ответа
    # - Решенные заявки за день
    # - и т.д.

get_technician_statistics(tguser)
    # Получает статистику для конкретного техника

get_shift_statistics(date)
    # Получает статистику для конкретной смены
```

---

#### **5.5 `background_tasks.py` - Фоновые задачи**

Модуль для управления фоновыми задачами (может использоваться для расширения).

---

### 6. **Middleware и Утилиты (`src/middleware/`, `src/utils/`)**

#### **6.1 `auth_middleware.py` - Авторизация**

**Основная функция проверки доступа:**

```python
async def check_user_access(update, context):
    """
    Проверяет доступ пользователя
    Возвращает True если авторизован, иначе False
    
    Проверяет:
    1. Тип чата (только личные сообщения)
    2. Наличие username в Telegram
    3. Наличие пользователя в БД
    """
```

**Процесс авторизации:**
```
Пользователь отправляет сообщение
    ↓
Декоратор @with_auth перехватывает
    ↓
check_user_access():
    - Если группа → пропускаем
    - Если нет username → отказываем доступ
    - Если нет в БД → отказываем доступ
    - Если в БД → разрешаем
    ↓
Обработчик выполняется (если авторизован)
```

---

#### **6.2 `auth_decorators.py` - Декораторы**

**Декораторы для обработчиков:**

```python
@with_auth
# Добавляет проверку авторизации
# Игнорирует сообщения из групп

@group_ignore
# Игнорирует все сообщения из групп
# Нужен для callback handlers (не требуют авторизации)
```

**Использование:**
```python
app.add_handler(CommandHandler("start", with_auth(start)))
app.add_handler(CallbackQueryHandler(group_ignore(handle_callback)))
```

---

#### **6.3 `logger.py` - Логирование**

**Логирование событий:**

```python
log_shift_exchange(level, message, user=None, action=None, details=None)
    # Логирует события в файлы:
    # - bot.log (основной лог)
    # - shift_exchange_*.log (логи обменов смен)
    
    # Уровни: 'info', 'warning', 'error'
    # Пример:
    log_shift_exchange('info', 'Смена начата', user='username', action='shift_start')
```

---

#### **6.4 `keyboards.py` - Клавиатуры Telegram**

**Функции для создания клавиатур:**

```python
get_main_menu_keyboard()
    # Главное меню

get_confirmation_keyboard()
    # Кнопки подтверждения (Да/Нет)

get_shift_menu_keyboard()
    # Меню управления сменами

get_exchange_menu_keyboard()
    # Меню обмена смен

get_remote_work_keyboard()
    # Меню удаленной работы

get_back_to_menu_keyboard()
    # Кнопка "Назад в меню"
```

**Пример использования:**
```python
keyboard = get_main_menu_keyboard()
await update.message.reply_text(
    "Главное меню:",
    reply_markup=keyboard
)
```

---

#### **6.5 `helpers.py` - Вспомогательные функции**

**Утилиты:**

```python
format_shift_info(shift_data)
    # Форматирует информацию о смене

parse_date_input(date_string)
    # Парсит дату из пользовательского ввода

get_shift_type_name(shift_type_id)
    # Преобразует ID типа смены в название

validate_username(username)
    # Проверяет валидность username

get_user_local_time()
    # Получает местное время пользователя
```

---

##  База данных

### Таблицы и их назначение:

#### **1. `Employees` - Сотрудники**

```sql
CREATE TABLE Employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,           -- ФИО
    active TINYINT DEFAULT 1,             -- Активный ли сотрудник
    phone TEXT,                           -- Телефон
    username TEXT,                        -- Юзернейм ПК
    LastLoginTime DATETIME,               -- Последнее заступление на смену
    tguser TEXT,                          -- Telegram username
    mail TEXT,                            -- Рабочая почта
    position TEXT,                        -- Должность
    TechnitianIdSd INT,                   -- ID в ServiceDesk
    onshift INT DEFAULT 0,                -- Статус на смене (0/1)
    telegram_id BIGINT,                   -- Telegram ID
    grade ENUM('Джуниор','Mid','Adv'),   -- Грейд
    employment_date DATE,                 -- Дата приема
    web_role ENUM('user','admin'),       -- Роль в веб системе
    web_last_login TIMESTAMP,             -- Последний вход в веб
    web_created_at TIMESTAMP              -- Дата создания учетной записи
)
```

**Использование:**
- Хранит информацию о всех сотрудниках
- Связь между Telegram и внутренними системами (username, ПК username, ServiceDesk ID)
- Статус нахождения на смене

---

#### **2. `Reminders` - Напоминания**

```sql
CREATE TABLE Reminders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tguser VARCHAR(255),                  -- Telegram username создателя
    reminder_text TEXT,                   -- Текст напоминания
    reminder_time DATETIME,               -- Время отправки
    created_time DATETIME DEFAULT NOW(),  -- Время создания
    is_sent TINYINT DEFAULT 0             -- Отправлено ли (0/1)
)
```

**Использование:**
- Хранит все напоминания
- Используется сервисом напоминаний для отправки
- `is_sent = 0` означает, что напоминание еще не отправлено

---

#### **3. `RemoteWorkRequests` - Запросы на удаленную работу**

```sql
CREATE TABLE RemoteWorkRequests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tguser VARCHAR(100) NOT NULL,         -- Кто запрашивает
    shift_date DATE NOT NULL,             -- На какую дату
    reason TEXT NOT NULL,                 -- Причина
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    approved_by_lead TINYINT DEFAULT 0,   -- Одобрено lead engineer
    approved_by_manager TINYINT DEFAULT 0,-- Одобрено manager
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Использование:**
- Управление запросами на удаленную работу
- Отслеживание согласований
- Статусы: pending (ожидает), approved (одобрено), rejected (отклонено)

---

#### **4. `RemoteLimitExtensions` - Расширения лимита удаленки**

```sql
CREATE TABLE RemoteLimitExtensions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tguser VARCHAR(50) NOT NULL,          -- Кому расширили
    month INT,                            -- Месяц (1-12)
    year INT,                             -- Год
    added_by VARCHAR(50),                 -- Кто добавил
    reason TEXT,                          -- Причина
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Использование:**
- Хранит дополнительные лимиты удаленной работы
- Может использоваться для исключений или специальных условий

---

#### **5. `ActualShiftTimes` - Фактические времена начала смены**

```sql
CREATE TABLE ActualShiftTimes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(255) NOT NULL,      -- ФИО
    tguser VARCHAR(255),                  -- Telegram username
    actual_start_time DATETIME NOT NULL,  -- Фактическое начало
    shift_date DATE NOT NULL,             -- Дата смены
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Использование:**
- Отслеживание времени фактического начала смены
- Используется для аналитики и отчетов

---

#### **6. `ShiftExchanges` - Обмены смен**

```sql
CREATE TABLE ShiftExchanges (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_from VARCHAR(100) NOT NULL,      -- От кого
    user_to VARCHAR(100) NOT NULL,        -- Кому
    shift_date DATE NOT NULL,             -- Дата смены
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    reason TEXT,                          -- Причина обмена
    approved_by_lead TINYINT DEFAULT 0,   -- Одобрено lead
    approved_by_manager TINYINT DEFAULT 0,-- Одобрено manager
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Использование:**
- Управление обменом сменами между сотрудниками
- Отслеживание согласований

---

##  Рабочие процессы

### Процесс 1: Заступление на смену

```
1. Пользователь отправляет сообщение "Заступить на смену"
                    ↓
2. Система получает сообщение
                    ↓
3. Проверяется авторизация (with_auth)
                    ↓
4. Получается Telegram username пользователя
                    ↓
5. Из БД получается username ПК
                    ↓
6. Из БД получается ServiceDesk ID техника
                    ↓
7. Вызывается perform_login_and_action(username, sd_id)
   - Логинится в систему
   - Переводит все заявки на этого техника
                    ↓
8. Обновляется статус пользователя в БД (onshift = 1)
                    ↓
9. Обновляется время последнего входа (LastLoginTime)
                    ↓
10. Отправляется уведомление в групповой чат Telegram
                    ↓
11. Пользователю отправляется подтверждение
```

---

### Процесс 2: Обмен смен

```
Пользователь A инициирует обмен
                    ↓
Система проверяет:
  - Есть ли смена на дату
  - Разрешен ли тип смены (не в FORBIDDEN_SHIFT_TYPES)
  - Существует ли пользователь B
                    ↓
Запрос сохраняется в БД (status = 'pending')
                    ↓
Lead Engineer получает уведомление
                    ↓
Lead нажимает "Одобрить" или "Отклонить"
                    ↓
Если Lead одобрил:
   Запрос идет на согласование Manager
             ↓
        Manager получает уведомление
             ↓
        Manager нажимает "Одобрить" или "Отклонить"
             ↓
        Если Manager одобрил:
           status = 'approved'
           Пользователи получают уведомление
           Смены в календаре обновляются (!)
             ↓
        Если Manager отклонил:
           status = 'rejected'
           Пользователи получают уведомление
                    ↓
Если Lead отклонил:
   status = 'rejected'
   Пользователи получают уведомление
```

---

### Процесс 3: Запрос на удаленную работу

```
Пользователь выбирает "Работать удаленно"
                    ↓
Система выбирает дату смены
                    ↓
Пользователь вводит причину
                    ↓
Система проверяет лимит удаленных дней в месяце
                    ↓
Если лимит не выбран или пользователь в REMOTE_NO_APPROVAL_USERS:
   Автоматически одобряется (status = 'approved')
   Данные передаются в ServiceDesk
   Пользователь получает подтверждение
             ↓
Если требуется согласование:
   Запрос сохраняется в БД (status = 'pending')
   Отправляется Lead Engineer
             ↓
        Lead одобряет → запрос идет Manager
             ↓
        Manager одобряет → status = 'approved'
             ↓
        Данные передаются в ServiceDesk
             ↓
        Пользователь получает подтверждение
```

---

### Процесс 4: Создание напоминания

```
Пользователь выбирает "Создать напоминание"
                    ↓
Бот просит ввести текст напоминания
                    ↓
Пользователь вводит текст
                    ↓
Бот просит выбрать дату
                    ↓
Пользователь выбирает дату
                    ↓
Бот просит выбрать время
                    ↓
Пользователь выбирает время
                    ↓
Напоминание сохраняется в БД:
  - tguser: username пользователя
  - reminder_text: введенный текст
  - reminder_time: выбранное время
  - is_sent: 0 (не отправлено)
                    ↓
Пользователю отправляется подтверждение
                    ↓
Фоновый сервис reminder_service проверяет каждые 30 сек
                    ↓
Когда наступает reminder_time:
   Формируется сообщение
   Отправляется в групповой чат
   В БД устанавливается is_sent = 1
```

---

##  Интеграции с внешними сервисами

### 1. **Telegram Bot API**

**Использование:**
- Отправка/получение сообщений
- Создание inline кнопок
- Управление состоянием разговора

**Основной endpoint:**
```
https://api.telegram.org/bot{TOKEN}/sendMessage
```

**Параметры:**
```python
{
    'chat_id': chat_id,              # ID чата
    'text': message,                 # Текст сообщения
    'parse_mode': 'HTML',            # Формат текста
    'reply_markup': keyboard_json,   # Клавиатура
    'message_thread_id': thread_id   # ID потока (для тредов)
}
```

---

### 2. **ServiceDesk API v3**

**Использование:**
- Получение заявок и задач техника
- Передача заявок между техниками
- Изменение статусов

**Base URL:**
```
https://support.center2m.com/api/v3
```

**Endpoints:**

| Метод | Endpoint | Описание |
|-------|----------|---------|
| GET | `/requests?technician_id=X` | Получить заявки техника |
| POST | `/requests/{id}/execute` | Выполнить заявку |
| GET | `/tasks?technician_id=X` | Получить задачи техника |
| POST | `/tasks/{id}/execute` | Выполнить задачу |
| GET | `/changes` | Получить изменения |

**Авторизация:**
```
Authorization: Bearer {SD_API_TOKEN}
```

---

### 3. **Login/Action URLs**

**Использование:**
- Аутентификация в системе
- Выполнение действий от имени пользователя

**Параметры:**
```python
LOGIN_URL = "https://..."     # URL для входа
ACTION_URL = "https://..."    # URL для выполнения действий
```

---

##  Безопасность и авторизация

### Уровни доступа:

```

         ОБЩИЕ ПОЛЬЗОВАТЕЛИ               
  - Заступить на смену                    
  - Запросить обмен смены                 
  - Запросить удаленную работу            
  - Создать напоминание                   
  - Смотреть статистику                   

                    ↑

     СТАРШИЙ ИНЖЕНЕР (lead_engineer)      
  - Все операции обычного пользователя    
  - Согласовать обмены смин              
  - Согласовать удаленную работу         
  - Добавить удаленную смену другому     

                    ↑

    МЕНЕДЖЕР / АДМИНИСТРАТОР (manager)    
  - Все операции lead engineer            
  - Управление Telegram ID пользователей  
  - Перезапуск сервиса напоминаний       
  - Тестирование системы                  
  - Просмотр статистики по пользователям 

```

### Процесс авторизации:

```
1. Пользователь отправляет сообщение
        ↓
2. @with_auth декоратор перехватывает
        ↓
3. check_user_access() проверяет:
    Тип чата == 'private'?
    Наличие username в Telegram?
    Наличие в БД?
        ↓
4. Если все ОК → обработчик выполняется
   Если ошибка → отправляется сообщение об ошибке
```

### Безопасность данных:

-  **Переменные окружения** - чувствительные данные в `.env`
-  **Валидация входных данных** - проверка всех параметров
-  **Логирование** - все действия логируются
-  **Обработка ошибок** - graceful error handling
-  **Параметризованные запросы** - защита от SQL injection

---

##  Диаграмма взаимодействия компонентов

```
TELEGRAM USERS
    
    
                                             
                                             
TELEGRAM BOT API                              
                                             
     /sendMessage                           
     /getUpdates                            
     /setWebhook (опционально)             
                                             
                                             
MAIN.PY (ApplicationBuilder.polling)          
                                             
    
                                             
                                             
MIDDLEWARE (with_auth, group_ignore)          
                                             
    
                                             
                                             
HANDLERS                                      
     CommandHandler (/start, /note, etc)   
     MessageHandler (text messages)        
     CallbackQueryHandler (inline buttons) 
     ErrorHandler                          
                                             
    
                                             
                                             
SERVICES                                      
     telegram_service (отправка сообщений) 
     servicedesk_api (API интеграция)      
     reminder_service (фоновая задача)     
     statistics (сбор данных)              
                                             
    
                                             
                                             
DATABASE LAYER                                
     db_operations.py                      
     shift_exchange.py                     
                                             
    
                                             
                                             
MYSQL DATABASES                               
     work_schedule_db (основная)           
     SD DB (ServiceDesk - вторая)          
                                             
    
                       
              EXTERNAL SERVICES
               Telegram API
               ServiceDesk API
               Login/Action URLs
```

---

##  Структура папок

```
SmenaControl/

 main.py                               # Точка входа приложения
 requirements.txt                      # Python зависимости
 CreateDB.sql                          # SQL для создания БД
 .env                                  # Переменные окружения (не в Git!)

 src/                                  # Основной исходный код
    __init__.py
   
    config.py                         # Конфигурация системы
   
    database/                         # Слой доступа к БД
       __init__.py
       db_operations.py             # Основные DB операции
       shift_exchange.py            # Операции обмена смин
   
    handlers/                         # Обработчики команд
       __init__.py
       command_handlers.py           # Основные команды (/start, /note)
       admin_handlers.py             # Админ команды
       callback_handlers.py          # Обработка кнопок
       reminder_handler.py           # Управление напоминаниями
       remote_work_handler.py        # Удаленная работа
       shift_exchange_handler.py     # Обмен сменами
       shift_operations.py           # Операции со сменами
   
    services/                         # Внешние сервисы
       __init__.py
       telegram_service.py           # Telegram API
       servicedesk_api.py            # ServiceDesk API
       reminder_service.py           # Фоновый сервис напоминаний
       statistics.py                 # Сбор статистики
       background_tasks.py           # Прочие фоновые задачи
   
    middleware/                       # Middleware слой
       __init__.py
       auth_middleware.py            # Проверка доступа
   
    utils/                            # Вспомогательные функции
        __init__.py
        auth_decorators.py            # Декораторы авторизации
        helpers.py                    # Общие функции
        keyboards.py                  # Telegram клавиатуры
        logger.py                     # Логирование

 docs/                                 # Документация
    PROJECT_DOCUMENTATION.md          # Этот файл
    old_version.py                   # Старая версия
    *.sql                             # SQL миграции

 logs/                                 # Файлы логов
    bot.log                          # Основной лог
    shift_exchange_*.log             # Логи обменов

 .gitignore                            # Исключения из Git
     .env
     *.log
     __pycache__/
     *.pyc
```

---

##  Инструкция по запуску

### Предварительные требования:

1. **Python 3.7+**
2. **MySQL/MariaDB** (2 базы данных)
3. **Telegram Bot Token** (от BotFather в Telegram)
4. **ServiceDesk API Token**

### Шаг 1: Клонирование и установка

```bash
# Клонируем репозиторий
git clone <repository_url>
cd SmenaControl

# Создаем виртуальное окружение
python -m venv venv

# Активируем виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

---

### Шаг 2: Подготовка базы данных

```bash
# Входим в MySQL
mysql -u root -p

# Создаем БД
CREATE DATABASE work_schedule_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Загружаем схему
mysql -u root -p work_schedule_db < CreateDB.sql
```

---

### Шаг 3: Конфигурация окружения

Создаем файл `.env` в корневой папке:

```env
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_CHAT_ID_TB=-1001234567891
THREAD_ID=123

# Database 1
DB_HOST=localhost
DB_USER=root
DB_PASS=password
DB_NAME=work_schedule_db

# Database 2 (ServiceDesk)
DB_HOST_2=10.77.129.34
DB_USER_2=sd_user
DB_PASS_2=sd_password
DB_NAME_2=servicedesk_db

# API
LOGIN_URL=https://...
ACTION_URL=https://...
SD_API_TOKEN=your_servicedesk_token

# Notifications Settings
REMOTE_NOTIFICATIONS_SEND_TO_MAIN_CHAT=true
REMOTE_NOTIFICATIONS_SEND_TO_TB_CHAT=true
REMOTE_NOTIFICATIONS_DEBUG_MODE=false
```

---

### Шаг 4: Запуск бота

```bash
# Простой запуск
python main.py

# С логированием (Linux/Mac)
python main.py 2>&1 | tee bot.log

# С логированием (Windows в PowerShell)
python main.py | Tee-Object -FilePath bot.log
```

---

### Шаг 5: Проверка работы

1. Откройте Telegram
2. Найдите вашего бота (по username)
3. Напишите `/start`
4. Бот должен ответить сообщением с главным меню

---

##  Примеры использования API

### Пример 1: Отправка сообщения в Telegram

```python
from src.services.telegram_service import send_telegram_message

message = " Смена началась!"
send_telegram_message(message)
```

---

### Пример 2: Получение данных пользователя

```python
from src.database.db_operations import get_user_data

user_info = get_user_data("username")
if user_info:
    name, phone, grade = user_info
    print(f"Пользователь: {name}, Грейд: {grade}")
```

---

### Пример 3: Создание новой команды

```python
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.auth_decorators import with_auth

@with_auth
async def my_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Новая команда"""
    await update.message.reply_text("Привет!")

# В main.py добавить:
app.add_handler(CommandHandler("mycommand", my_new_command))
```

---

##  Обычные ошибки и их решения

| Ошибка | Причина | Решение |
|--------|--------|--------|
| `[ERROR] Bot error: Unauthorized` | Неверный Token | Проверить TELEGRAM_BOT_TOKEN в .env |
| `[ERROR] get_db_connection: Access denied` | Неверные креденшалы БД | Проверить DB_USER, DB_PASS, DB_HOST |
| ` Доступ запрещен` | Пользователя нет в БД | Добавить пользователя в таблицу Employees |
| ` У вас не установлен username` | Telegram username не установлен | Установить username в настройках Telegram |

---

##  Контакты и поддержка

- **Lead Engineer**: @wezersovvv
- **Manager**: @Electrowind
- **Telegram Group**: [Ссылка на групп]

---

##  Лицензия

Приватный проект. Все права защищены.

---

*Документация актуальна на: 06.05.2026*
*Версия: 1.0*
