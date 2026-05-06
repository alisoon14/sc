"""
Вспомогательные функции
Содержит различные утилиты для обработки данных
"""

import re
import logging
import requests
import urllib3
from datetime import datetime

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка основного логирования
logging.basicConfig(
    level=logging.INFO,
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def setup_debug_requests():
    """Настраивает отладку HTTP-запросов"""
    def my_get(*args, **kwargs):
        print(f"[DEBUG GET] URL: {args[0]}")
        return original_get(*args, **kwargs)

    original_get = requests.get
    requests.get = my_get


def strip_html_tags(text: str) -> str:
    """Удаляет HTML теги из текста"""
    return re.sub(r'<[^>]+>', '', text)


def clean_id(request_id):
    """Очищает ID от специальных символов"""
    return re.sub(r'\W+', '', str(request_id))


def format_time_duration(seconds):
    """Форматирует количество секунд в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}ч {minutes}мин"


def validate_date_format(date_string, date_format="%d.%m.%Y"):
    """Проверяет корректность формата даты"""
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False


def validate_datetime_format(datetime_string, datetime_format="%d.%m.%Y %H:%M"):
    """Проверяет корректность формата даты и времени"""
    try:
        datetime.strptime(datetime_string, datetime_format)
        return True
    except ValueError:
        return False


def safe_get_dict_value(dictionary, key, default=None):
    """Безопасное получение значения из словаря"""
    try:
        return dictionary.get(key, default)
    except (KeyError, TypeError):
        return default


def format_shift_exchange_message(exchange_data, shift_data, user_data):
    """Форматирует сообщение об обмене смен"""
    from src.database.db_operations import get_shift_type_name
    
    shift_type_name = get_shift_type_name(shift_data.get('shift_type_id', 0))
    
    return f"""🔁 *Обмен сменами*

📅 Дата: {shift_data.get('date', 'Неизвестно')}
🏷️ Тип смены: {shift_type_name}
👤 Инициатор: {user_data.get('name', 'Неизвестно')}
📊 Статус: {exchange_data.get('status', 'В процессе')}"""


def create_pagination_text(items, page_size=10, current_page=1):
    """Создает пагинацию для списка элементов"""
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_index = (current_page - 1) * page_size
    end_index = min(start_index + page_size, total_items)
    
    page_items = items[start_index:end_index]
    
    pagination_info = f"Страница {current_page} из {total_pages} (всего: {total_items})"
    
    return page_items, pagination_info


def truncate_text(text, max_length=100, suffix="..."):
    """Обрезает текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def escape_markdown_v2(text):
    """Экранирует специальные символы для Markdown V2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))


def is_valid_telegram_username(username):
    """Проверяет корректность Telegram username"""
    if not username:
        return False
    # Username должен содержать только буквы, цифры и подчеркивания
    # Длина от 5 до 32 символов
    return bool(re.match(r'^[a-zA-Z0-9_]{5,32}$', username))


def get_current_timestamp():
    """Возвращает текущий timestamp в читаемом формате"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
