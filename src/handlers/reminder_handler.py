"""
Обработчик создания напоминаний
Содержит логику создания и управления напоминаниями
"""

from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.database.db_operations import get_user_data, save_reminder
from src.utils.keyboards import get_main_menu_keyboard, get_input_keyboard, get_yes_no_keyboard
from src.utils.logger import log_shift_exchange


async def handle_reminder_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик диалога создания напоминания"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    user_data = get_user_data(tguser)
    name = user_data[0] if user_data else tguser

    # Начало создания напоминания
    if 'reminder_state' not in context.user_data:
        log_shift_exchange('info', 'Пользователь начал создание напоминания', 
                          user=tguser, action='reminder_start')
        context.user_data['reminder_state'] = 'waiting_for_time'
        
        await update.message.reply_text(
            "🔔 *Создание напоминания*\n\n"
            "📋 *Инструкция:*\n"
            "1. Введите дату и время напоминания\n"
            "2. Укажите текст сообщения\n"
            "3. Подтвердите создание\n\n"
            "📅 Введите время для напоминания в формате:\n"
            "*ДД.ММ.ГГГГ ЧЧ:ММ*\n\n"
            "Пример: 25.12.2025 14:30",
            reply_markup=get_input_keyboard(),
            parse_mode='markdown'
        )
        return

    # Ввод времени
    if context.user_data['reminder_state'] == 'waiting_for_time':
        try:
            reminder_time = datetime.strptime(text, "%d.%m.%Y %H:%M")
            if reminder_time < datetime.now():
                await update.message.reply_text(
                    "⚠️ *Ошибка времени*\n\n"
                    "Время напоминания не может быть в прошлом.\n"
                    "Введите корректное время в будущем.\n\n"
                    "Формат: *ДД.ММ.ГГГГ ЧЧ:ММ*",
                    reply_markup=get_input_keyboard(),
                    parse_mode='markdown'
                )
                return
            
            context.user_data['reminder_time'] = reminder_time
            context.user_data['reminder_state'] = 'waiting_for_text'
            
            await update.message.reply_text(
                "✅ *Время принято*\n\n"
                f"📅 Напоминание установлено на: {reminder_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                "📝 Теперь введите текст для напоминания:",
                reply_markup=get_input_keyboard(),
                parse_mode='markdown'
            )
        except ValueError:
            await update.message.reply_text(
                "❌ *Неверный формат даты*\n\n"
                "Пожалуйста, введите время в правильном формате:\n"
                "*ДД.ММ.ГГГГ ЧЧ:ММ*\n\n"
                "Пример: 25.12.2025 14:30",
                reply_markup=get_input_keyboard(),
                parse_mode='markdown'
            )
        return

    # Ввод текста напоминания
    if context.user_data['reminder_state'] == 'waiting_for_text':
        context.user_data['reminder_text'] = text
        context.user_data['reminder_state'] = 'waiting_for_confirmation'

        preview = f"""🔔 *Предпросмотр напоминания*

📋 *Детали:*
📅 Дата и время: {context.user_data['reminder_time'].strftime("%d.%m.%Y %H:%M")}
📝 Текст напоминания: {context.user_data['reminder_text']}
👤 Создано: {name}

✅ Подтвердить создание? (*Да* / *Нет*)"""

        await update.message.reply_text(
            preview, 
            reply_markup=get_yes_no_keyboard(),
            parse_mode='markdown'
        )
        return

    # Подтверждение создания
    if context.user_data['reminder_state'] == 'waiting_for_confirmation':
        if text.lower() == 'да':
            # Сохраняем напоминание
            if save_reminder(tguser, context.user_data['reminder_text'], context.user_data['reminder_time']):
                log_shift_exchange('info', 'Напоминание успешно создано', 
                                  user=tguser, 
                                  reminder_time=context.user_data['reminder_time'].strftime('%Y-%m-%d %H:%M:%S'),
                                  reminder_text=context.user_data['reminder_text'][:50] + '...' if len(context.user_data['reminder_text']) > 50 else context.user_data['reminder_text'],
                                  action='reminder_created')

                await update.message.reply_text(
                    "✅ *Напоминание создано!*\n\n"
                    f"📅 Время: {context.user_data['reminder_time'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"📝 Текст: {context.user_data['reminder_text']}\n\n"
                    "🔔 Вы получите уведомление в указанное время",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='markdown'
                )
                print(f"[INFO] Reminder created by {tguser} at {context.user_data['reminder_time']}")
            else:
                log_shift_exchange('error', 'Ошибка при создании напоминания', 
                                  user=tguser, action='reminder_error')
                await update.message.reply_text(
                    "❌ *Ошибка при создании напоминания*\n\n"
                    "Попробуйте еще раз или обратитесь к администратору.",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='markdown'
                )

            # Очищаем состояние
            context.user_data.pop('reminder_state', None)
            context.user_data.pop('reminder_text', None)
            context.user_data.pop('reminder_time', None)
        else:
            await update.message.reply_text(
                "❌ *Создание отменено*\n\n"
                "Напоминание не было создано.\n"
                "Вы можете создать новое напоминание в любое время.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            # Очищаем состояние
            context.user_data.pop('reminder_state', None)
            context.user_data.pop('reminder_text', None)
            context.user_data.pop('reminder_time', None)
        return
