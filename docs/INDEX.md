#  Индекс документации SmenaControl Bot

**Дата обновления:** 06.05.2026  
**Версия проекта:** 1.0

---

##  Быстрая навигация

Выберите, что вам нужно:

###  Я новичок, хочу понять проект
 Начните с [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)
- Общий обзор системы
- Архитектура приложения
- Компоненты и их назначение
- Инструкция по запуску

###  Мне нужны диаграммы и схемы
 Смотрите [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)
- Диаграмма общей архитектуры
- Процессы взаимодействия компонентов
- Диаграммы рабочих процессов
- ERD база данных

###  Я разработчик, нужны примеры кода
 Используйте [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)
- Примеры основных функций
- Работа с БД
- Работа с Telegram API
- Как создавать новые команды
- Обработка ошибок

###  Нужен быстрый справочник
 Откройте [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Таблицы функций
- Быстрый поиск функционала
- Классические паттерны
- Частые ошибки

###  Хочу тестовые скрипты
 Посмотрите [TEST_SCRIPTS.md](TEST_SCRIPTS.md)
- Готовые проверки проекта
- Сценарии для автоматизированного тестирования
- Примеры запуска и результатов
- Проверка критичных функций

---

##  Полный список документов

### 1.  PROJECT_DOCUMENTATION.md
**Полная документация проекта**

Содержит:
-  Обзор системы
-  Архитектуру приложения
-  Описание всех компонентов
-  Таблицу взаимодействий
-  Описание базы данных
-  Рабочие процессы
-  Безопасность
-  Инструкцию по запуску

**Лучше всего для:**
-  Обучения новых разработчиков
-  Общего понимания проекта
-  Поиска информации о компонентах

---

### 2.  ARCHITECTURE_DIAGRAMS.md
**Визуальные диаграммы и схемы**

Содержит:
1. Общую архитектуру системы
2. Поток обработки сообщения
3. Процесс "Заступить на смену"
4. Процесс "Обмен смен"
5. Процесс "Удаленная работа"
6. Сервис напоминаний
7. Таблицу взаимодействий компонентов
8. Матрицу ролей и прав доступа
9. ERD базы данных

**Лучше всего для:**
-  Визуального представления
-  Презентаций
-  Понимания процессов
-  Обучения архитектуре

---

### 3.  API_USAGE_GUIDE.md
**Практическое руководство по использованию API**

Разделы:
-  Работа с данными пользователя
-  Работа со сменами
-  Обмен сменами
-  Удаленная работа
-  Напоминания
-  Telegram API
-  ServiceDesk API
-  Обработка ошибок
-  Создание собственных обработчиков
-  Примеры статистики

**Лучше всего для:**
-  Поиска примеров кода
-  Добавления новой функциональности
-  Отладки и исправления ошибок
-  Написания нового кода

---

### 4.  QUICK_REFERENCE.md
**Краткая шпаргалка**

Содержит:
-  Таблицы команд
-  Быстрый поиск функций
-  Структуру таблиц БД
-  Переменные окружения
-  Конфигурацию
-  Форматирование сообщений
-  Паттерны и практики
-  Частые ошибки и решения
-  Быстрый старт

**Лучше всего для:**
-  Быстрого поиска нужной информации
-  Справки во время разработки
-  Решения проблем

---

### 5.  TEST_SCRIPTS.md
**Набор готовых тестовых скриптов**

Содержит:
-  Сценарии тестирования проекта
-  Проверки работы команд
-  Проверки работы БД
-  Тесты на авторизацию и API
-  Примеры использования

**Лучше всего для:**
-  Быстрой проверки работоспособности
-  Тестирования изменений
-  Проверки новых фич

---

##  Все документы проекта

| # | Файл | Описание |
|---|------|---------|
| 1 | [INDEX.md](INDEX.md) | Навигация по документации |
| 2 | [README.md](README.md) | Стартовая страница проекта |
| 3 | [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | Полная документация проекта |
| 4 | [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) | Диаграммы и схемы |
| 5 | [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) | Практическое руководство по API |
| 6 | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Краткий справочник |
| 7 | [TEST_SCRIPTS.md](TEST_SCRIPTS.md) | Готовые тесты и проверки |

---

##  Обзор структуры проекта

```
SmenaControl/

 main.py                              ← ТОЧКА ВХОДА
 requirements.txt                     ← Зависимости
 CreateDB.sql                         ← Схема БД
 .env                                 ← Переменные окружения

 src/                                 ← Основной код
    config.py                        ← Конфигурация
   
    database/                        ← Слой работы с БД
       db_operations.py             • Основные операции
       shift_exchange.py            • Операции обмена
   
    handlers/                        ← Обработчики
       command_handlers.py          • /start, /note, /refresh
       admin_handlers.py            • Админ команды
       callback_handlers.py         • Кнопки Telegram
       reminder_handler.py          • Напоминания
       remote_work_handler.py       • Удаленная работа
       shift_exchange_handler.py    • Обмен сменами
       shift_operations.py          • Операции со сменами
   
    services/                        ← Сервисы
       telegram_service.py          • Telegram API
       servicedesk_api.py           • ServiceDesk API
       reminder_service.py          • Сервис напоминаний
       statistics.py                • Сбор статистики
       background_tasks.py          • Фоновые задачи
   
    middleware/                      ← Middleware
       auth_middleware.py           • Проверка доступа
   
    utils/                           ← Утилиты
        auth_decorators.py           • @with_auth, @group_ignore
        helpers.py                   • Вспомогательные функции
        keyboards.py                 • Клавиатуры Telegram
        logger.py                    • Логирование

 docs/                                ← Документация
     INDEX.md                         ← Вы здесь
     PROJECT_DOCUMENTATION.md         ← Полная документация
     ARCHITECTURE_DIAGRAMS.md         ← Диаграммы
     API_USAGE_GUIDE.md               ← Примеры кода
     QUICK_REFERENCE.md               ← Шпаргалка
     TEST_SCRIPTS.md                  ← Тесты и проверки
```

---

##  Ключевые компоненты

### 1. **main.py** - Точка входа
- Инициализирует Telegram Bot
- Регистрирует обработчики
- Запускает polling
- Инициализирует фоновые задачи

### 2. **config.py** - Конфигурация
- Загружает переменные окружения
- Содержит все константы
- Определяет роли и права доступа

### 3. **database/** - Слой доступа к БД
- `db_operations.py` - основные операции с БД
- `shift_exchange.py` - операции обмена смин

### 4. **handlers/** - Обработчики команд
- Обрабатывают команды и сообщения
- Взаимодействуют с БД и сервисами
- Отправляют ответы пользователю

### 5. **services/** - Внешние сервисы
- `telegram_service.py` - работа с Telegram API
- `servicedesk_api.py` - работа с ServiceDesk API
- `reminder_service.py` - фоновый сервис напоминаний

### 6. **middleware/** - Middleware
- `auth_middleware.py` - проверка авторизации пользователей

### 7. **utils/** - Утилиты
- `auth_decorators.py` - декораторы для защиты
- `helpers.py` - вспомогательные функции
- `keyboards.py` - создание клавиатур Telegram
- `logger.py` - логирование событий

---

##  Таблица взаимодействия документов

| Что вам нужно | Документ | Раздел | Примечание |
|---|---|---|---|
| Общее описание | PROJECT_DOC | Обзор системы | Начните отсюда |
| Как запустить | PROJECT_DOC | Инструкция по запуску | 4 шага |
| Архитектура | ARCHITECTURE | Диаграмма 1 | Визуально |
| Процесс смены | ARCHITECTURE | Диаграмма 3 | Пошагово |
| Получить данные | API_GUIDE | Работа с пользователем | get_user_data() |
| Начать смену | API_GUIDE | Работа со сменами | set_onshift() |
| Обмен смин | API_GUIDE | Работа с обменом | save_shift_exchange() |
| Удаленка | API_GUIDE | Работа с удаленной работой | get_user_available_remote_limit() |
| Напоминания | API_GUIDE | Работа с напоминаниями | save_reminder() |
| Telegram API | API_GUIDE | Работа с Telegram | send_telegram_message() |
| ServiceDesk API | API_GUIDE | Работа с ServiceDesk | transfer_requests() |
| Ошибки | API_GUIDE | Обработка ошибок | try-except примеры |
| Новая команда | API_GUIDE | Создание обработчика | 2 примера |
| Быстрый поиск | QUICK_REF | Быстрый поиск функций | Таблицы |
| Команды | QUICK_REF | Где что находится | Командная таблица |
| Шпаргалка | QUICK_REF | Вся страница | Печатайте! |

---

##  Рекомендуемый порядок обучения

### День 1⃣ - Основы
1. Прочитайте [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#обзор-системы) (Обзор системы)
2. Посмотрите [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-1-общая-архитектура-системы) (Диаграмма архитектуры)
3. Изучите [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#-компоненты-системы) (Компоненты)

### День 2⃣ - Детали
4. Посмотрите [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-2-поток-обработки-сообщения) (Поток обработки)
5. Изучите [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#-рабочие-процессы) (Рабочие процессы)
6. Прочитайте о [Базе данных](PROJECT_DOCUMENTATION.md#-база-данных)

### День 3⃣ - Кодирование
7. Посмотрите примеры в [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-данными-пользователя)
8. Изучите [Создание новых обработчиков](API_USAGE_GUIDE.md#-создание-собственного-обработчика)
9. Используйте [QUICK_REFERENCE.md](QUICK_REFERENCE.md) как шпаргалку

---

##  Поиск по теме

###  Смены и начало смены
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#4-обработчики-srchandlers) → Shift Operations
- Диаграмма: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-3-процесс-заступить-на-смену)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-со-сменами)
- Команды: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-быстрый-поиск-функций) → shift operations

###  Обмен смин
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#42-shiftexchangepy--операции-обмена-смин)
- Диаграмма: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-4-процесс-обмен-смин)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-обменом-смин)

###  Удаленная работа
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#46-remote_work_handlerpy--удаленная-работа)
- Диаграмма: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-5-процесс-удаленная-работа)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-удаленной-работой)

###  Напоминания
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#52-reminder_servicepy--сервис-напоминаний)
- Диаграмма: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-6-сервис-напоминаний-фоновая-задача)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-напоминаниями)

###  Безопасность и авторизация
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#-безопасность-и-авторизация)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-обработка-ошибок)
- Шпаргалка: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-как-добавить-защиту-авторизации)

###  Telegram API
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#51-telegram_servicepy--работа-с-telegram-api)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-telegram-api)
- Форматирование: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-форматирование-сообщений-telegram)

###  ServiceDesk API
- Описание: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#53-servicedesk_apipython--интеграция-с-servicedesk)
- Примеры: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md#-работа-с-servicedesk-api)

---

##  Типичные сценарии

### Сценарий 1: "Мне нужно добавить новую команду"
1. Прочитайте [Создание собственного обработчика](API_USAGE_GUIDE.md#-создание-собственного-обработчика)
2. Посмотрите примеры в `src/handlers/command_handlers.py`
3. Используйте [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-как-добавить-защиту-авторизации) для защиты
4. Добавьте в `main.py`

### Сценарий 2: "У меня ошибка, не знаю как решить"
1. Посмотрите [Обработка ошибок](API_USAGE_GUIDE.md#-обработка-ошибок)
2. Проверьте [Частые ошибки](QUICK_REFERENCE.md#-частые-ошибки-и-решения)
3. Посмотрите логи в `*.log` файлах

### Сценарий 3: "Нужно получить данные из БД"
1. Откройте [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-быстрый-поиск-функций) → Получение данных
2. Найдите нужную функцию
3. Посмотрите пример в [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)

### Сценарий 4: "Мне нужна архитектура проекта"
1. Посмотрите [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-1-общая-архитектура-системы)
2. Прочитайте [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#-архитектура-приложения)
3. Используйте для презентаций и документации

---

##  Быстрый старт

### Если у вас есть 5 минут
- Прочитайте [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-быстрый-старт) → Быстрый старт

### Если у вас есть 30 минут
- Прочитайте [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md#-обзор-системы)
- Посмотрите [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md#диаграмма-1-общая-архитектура-системы)


---

##  Внутренние контакты

секрет

---


---

##  Цель документации

 **Помочь разработчикам:**
- Быстро разобраться в проекте
- Найти нужную информацию
- Добавлять новый функционал
- Исправлять ошибки
- Обучать новых членов команды

---

** Начните с раздела выше, который соответствует вашему вопросу!**

---

*Документация актуальна на: 06.05.2026*
*Если вы нашли неточность - обновите документы!*
