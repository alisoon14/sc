"""
Модуль логирования для системы обмена сменами
Содержит настройку логгера и функции для записи логов
"""

import logging
from datetime import datetime


def setup_shift_exchange_logger():
    """Настраивает отдельный логгер для операций обмена сменами"""
    logger = logging.getLogger('shift_exchange')
    logger.setLevel(logging.INFO)
    
    # Создаем файл лога с текущей датой
    log_filename = f"logs/shift_exchange_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Создаем обработчик файла
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Очищаем предыдущие обработчики и добавляем новый
    logger.handlers.clear()
    logger.addHandler(file_handler)
    
    return logger


# Инициализируем логгер
shift_logger = setup_shift_exchange_logger()


def log_shift_exchange(level, message, **kwargs):
    """
    Функция для логирования операций обмена сменами
    
    Args:
        level: уровень логирования ('info', 'warning', 'error')
        message: сообщение для лога
        **kwargs: дополнительные параметры для контекста
    """
    # Формируем контекстную информацию
    context_parts = []
    for key, value in kwargs.items():
        context_parts.append(f"{key}={value}")
    context = " | " + " | ".join(context_parts) if context_parts else ""
    
    log_message = f"{message}{context}"
    
    if level.lower() == 'info':
        shift_logger.info(log_message)
    elif level.lower() == 'warning':
        shift_logger.warning(log_message)
    elif level.lower() == 'error':
        shift_logger.error(log_message)
    else:
        shift_logger.info(log_message)
