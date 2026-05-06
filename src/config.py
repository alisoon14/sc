"""
Конфигурация приложения
Содержит все настройки и переменные окружения
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHAT_ID_TB = os.getenv("TELEGRAM_CHAT_ID_TB")
THREAD_ID = os.getenv("THREAD_ID")

# Настройки для внешних API
LOGIN_URL = os.getenv("LOGIN_URL")
ACTION_URL = os.getenv("ACTION_URL")
SD_API_TOKEN = os.getenv("SD_API_TOKEN")

# Настройки первой базы данных
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Настройки второй базы данных
DB_HOST_2 = os.getenv("DB_HOST_2")
DB_USER_2 = os.getenv("DB_USER_2")
DB_PASS_2 = os.getenv("DB_PASS_2")
DB_NAME_2 = os.getenv("DB_NAME_2")

# Константы приложения
FORBIDDEN_SHIFT_TYPES = [12, 10, 13, 100]

# API URLs для ServiceDesk
SD_BASE_URL = "https://support.center2m.com"
SD_API_V3_URL = f"{SD_BASE_URL}/api/v3"
SD_REQUESTS_URL = f"{SD_API_V3_URL}/requests"
SD_TASKS_URL = f"{SD_API_V3_URL}/tasks" 
SD_CHANGES_URL = f"{SD_API_V3_URL}/changes"

# Telegram API URL
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Списки разрешенных пользователей для различных операций
ALLOWED_WORKLOG_OWNERS = {
    "Федорова Арина Александровна",
    "Бузанов Даниил Сергеевич", 
    "Нехорошков Кирилл Александрович",
    "Петрянкин Артем Евгеньевич",
    "Кривохин Андрей Михайлович",
    "Лещенко Федор"
}

# Роли для согласования обменов смен
SHIFT_EXCHANGE_ROLES = {
    "lead_engineer": "wezersovvv",
    "manager": "Electrowind"
}

# Роли для согласования удаленки
REMOTE_REQUEST_ROLES = {
    "lead_engineer": "wezersovvv",
    "manager": "Electrowind"
}

# Администраторы (могут управлять сменами других пользователей)
ADMIN_ROLES = {
    "lead_engineer": "wezersovvv",
    "manager": "Electrowind"
}

# Пользователи, которым не нужно подтверждение для удаленки
REMOTE_NO_APPROVAL_USERS = [
    "Electrowind",
    "wezersovvv",
    "arnfed"
]

# Лимиты для удаленки в зависимости от грейда
REMOTE_MONTHLY_LIMITS_BY_GRADE = {
    'Джуниор (Jun)': 0,      # Джуниор - 0 удаленок
    'Специалист (Mid)': 1,   # Мид - 1 удаленка
    'Продвинутый (Adv)': 2   # Продвинутый - 2 удаленки
}

# Лимит по умолчанию для пользователей без грейда или с неизвестным грейдом
REMOTE_MONTHLY_LIMIT = 1  # Количество раз в месяц

# Настройки уведомлений для тестирования (отдельно для каждой группы)
REMOTE_NOTIFICATIONS = {
    "send_to_approvers": True,      # Уведомления руководителям о новых запросах (только в личку)
    "send_to_requesters": True,     # Уведомления пользователям о статусе запроса (только в личку)
    "send_to_main_chat": True,     # Уведомления в основной чат (TELEGRAM_CHAT_ID)
    "send_to_tb_chat": True,       # Уведомления в TB чат (TELEGRAM_CHAT_ID_TB)
    "debug_mode": False             # Режим отладки с консольными сообщениями
}
