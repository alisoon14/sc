"""
Конфигурация приложения
Содержит все настройки и переменные окружения
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env рядом с корнем проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
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

# Настройки второй базы данных (ServiceDesk)
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
TELEGRAM_API_BASE = f"https://api.telegram.org/bot8179803541:AAHNdnhIQtedIzqEwdRTxgsR-WvxX0MHLXo"

# Required environment variables for startup validation
REQUIRED_ENV_VARS = [
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_ID',
    'DB_HOST',
    'DB_USER',
    'DB_NAME'
]


def get_missing_env_vars():
    return [name for name in REQUIRED_ENV_VARS if not globals().get(name)]


def validate_config():
    missing = get_missing_env_vars()
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Проверьте .env файл или переменные окружения."
        )


# Списки разрешенных пользователей для различных операций
ALLOWED_WORKLOG_OWNERS = {
    "testusr1",
}

# Роли для согласования обменов смен
SHIFT_EXCHANGE_ROLES = {
    "lead_engineer": "adminrole1",
    "manager": "adminrole2"
}

# Роли для согласования удаленки
REMOTE_REQUEST_ROLES = {
    "lead_engineer": "adminrole1",
    "manager": "adminrole2"
}

# Администраторы (могут управлять сменами других пользователей)
ADMIN_ROLES = {
    "lead_engineer": "adminrole1",
    "manager": "adminrole2"
}

# Пользователи, которым не нужно подтверждение для удаленки
REMOTE_NO_APPROVAL_USERS = [
    "adminrole1",
    "adminrole2",
    "testusr1"
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
