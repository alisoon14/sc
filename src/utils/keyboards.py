"""
Утилиты для создания клавиатур Telegram
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [KeyboardButton("🚀 Начать смену")],
        [KeyboardButton("🏠 Начать смену (Удаленно)")],
        [KeyboardButton("🔔 Создать напоминание")],
        [KeyboardButton("🔄 Отдать смену (Поменяться сменами)")],
        [KeyboardButton("📋 Запросить удаленку")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_confirmation_keyboard():
    """Возвращает клавиатуру подтверждения (Да/Нет)"""
    keyboard = [
        [KeyboardButton("✅ Да")],
        [KeyboardButton("❌ Нет")],
        [KeyboardButton("🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_to_menu_keyboard():
    """Возвращает клавиатуру с кнопкой возврата в главное меню"""
    keyboard = [
        [KeyboardButton("🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_input_keyboard():
    """Возвращает клавиатуру с кнопкой возврата для ввода данных"""
    keyboard = [
        [KeyboardButton("🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_yes_no_keyboard():
    """Возвращает клавиатуру Да/Нет с кнопкой возврата"""
    keyboard = [
        [KeyboardButton("Да"), KeyboardButton("Нет")],
        [KeyboardButton("🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_employees_keyboard(employees):
    """Возвращает клавиатуру с списком сотрудников и кнопкой возврата"""
    buttons = [[KeyboardButton(emp['name'])] for emp in employees]
    buttons.append([KeyboardButton("🏠 Главное меню")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_shift_exchange_inline_keyboard(exchange_id):
    """Возвращает inline клавиатуру для обмена сменами"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Согласиться", callback_data=f"confirm_exchange_{exchange_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_exchange_{exchange_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_remote_request_inline_keyboard(request_id):
    """Возвращает inline клавиатуру для запросов удаленки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_remote_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_remote_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
