"""
Обработчики команд для Telegram бота
Содержит основные команды и их логику
"""

import re
from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.database.db_operations import (
    get_user_data, update_telegram_id, save_shift_note, 
    set_onshift, update_start_shift_time, get_static_user_from_db,
    get_monthly_remote_count, get_user_available_remote_limit,
    get_today_shifts
)
from src.config import REMOTE_NO_APPROVAL_USERS
from src.database.shift_exchange import get_shift_exchange, get_user_role_for_exchange
from src.services.telegram_service import perform_login_and_action
from src.services.servicedesk_api import get_current_requests_and_tasks, transfer_requests, transfer_tasks
from src.services.statistics import get_current_statistics
from src.handlers.shift_operations import start_shift
from src.handlers.reminder_handler import handle_reminder_conversation
from src.handlers.shift_exchange_handler import handle_shift_exchange_conversation
from src.utils.logger import log_shift_exchange
from src.utils.keyboards import get_main_menu_keyboard, get_confirmation_keyboard, get_back_to_menu_keyboard, get_input_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    tguser = update.effective_user.username
    telegram_id = update.effective_user.id

    # Сохраняем telegram_id
    if update_telegram_id(tguser, telegram_id):
        print(f"[DEBUG] telegram_id сохранён: {tguser} → {telegram_id}")
    else:
        print(f"[ERROR] сохранение telegram_id для {tguser}")

    # Получаем данные пользователя
    user_data = get_user_data(tguser)
    if user_data:
        name, phone, grade = user_data
        user_info = f"👤*Пользователь: {name}* \n🎖️ *Грейд:* {grade}"
    else:
        name = tguser
        user_info = f"👤*Пользователь: {name}*"

    # Получаем смены на сегодня
    shifts_info = ""
    today_shifts = get_today_shifts()
    if today_shifts:
        day_shifts = []
        night_shifts = []
        
        for shift in today_shifts:
            shift_name = shift['name']
            shift_type_id = shift['shift_type_id']
            
            if shift_type_id not in [1, 2, 11, 102]:
                continue
            
            if shift_type_id in [1, 11]:  # Дневные смены
                day_shifts.append(shift_name)
            elif shift_type_id in [2, 102]:  # Ночные смены
                night_shifts.append(shift_name)
        
        # Формируем компактный текст смен
        shift_parts = []
        if day_shifts:
            shift_parts.append(f"(09-21) {', '.join(day_shifts)}")
        if night_shifts:
            shift_parts.append(f"(21-09) {', '.join(night_shifts)}")

        if shift_parts:
            shifts_info = f"\n📅 *Смены сегодня:* {' | '.join(shift_parts)}"

    # Статистика удаленки
    current_date = datetime.now()
    monthly_remote_count = get_monthly_remote_count(tguser, current_date.year, current_date.month)
    available_remote_limit = get_user_available_remote_limit(tguser, current_date.year, current_date.month)
    has_bypass = tguser in REMOTE_NO_APPROVAL_USERS
    
    if has_bypass:
        remote_info = "🔓 *БАЙПАС удаленки* — без ограничений"
    else:
        # Добавляем информацию о лимитах по грейдам
        if user_data:
            _, _, grade = user_data
            grade_info = ""
            if grade == 'Джуниор (Jun)':
                grade_info = " (Jun: 0/мес)"
            elif grade == 'Специалист (Mid)':
                grade_info = " (Mid: 1/мес)"
            elif grade == 'Продвинутый (Adv)':
                grade_info = " (Adv: 2/мес)"
        else:
            grade_info = ""
        
        remote_info = f"📊 *Удаленка:* {monthly_remote_count}/{available_remote_limit} за {current_date.strftime('%m.%Y')}{grade_info}"

    # Основное приветственное сообщение
    welcome_text = f"""👋 *Добро пожаловать в SmenaControl!*

{user_info}{shifts_info}
{remote_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 **Начать смену** — из офиса
🏠 **Начать смену (Удаленно)** — удаленно{' (БАЙПАС)' if has_bypass else ''}

🔔 **Создать напоминание**
🔄 **Отдать смену (Поменяться сменами) — После согласований отдает смену выбранному человеку**

{f'📋 **Запросить удаленку** — подача заявки' if not has_bypass else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ *Лимиты удаленки по грейдам:*
• Джуниор (Jun): 0 раз/месяц
• Специалист (Mid): 1 раз/месяц  
• Продвинутый (Adv): 2 раза/месяц

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 */refresh* — обновить данные
💡 */note <текст>* — добавить заметку"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='markdown'
    )


async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /note для добавления заметок"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    tguser = update.effective_user.username
    user_data = get_user_data(tguser)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден в базе данных")
        return
    
    # Получаем текст заметки
    note_text = ' '.join(context.args) if context.args else None
    
    if not note_text:
        await update.message.reply_text(
            "📝 *Добавление заметки к смене*\n\n"
            "Используйте: `/note <текст заметки>`\n\n"
            "*Пример:* `/note Выполнил проверку всех критических систем`",
            parse_mode='markdown'
        )
        return
    
    # Сохраняем заметку
    result = save_shift_note(tguser, note_text)
    
    if result:
        await update.message.reply_text(
            f"✅ *Заметка добавлена*\n\n"
            f"📝 {note_text}\n"
            f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка при сохранении заметки")


async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /refresh"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    await start_command(update, context)


async def handle_start_shift_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик диалога начала смены"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    user_data = get_user_data(tguser)

    if text == "🚀 Начать смену":
        await start_shift(update, context, is_remote=False)
        return

    if text == "🏠 Начать смену (Удаленно)":
        await start_shift(update, context, is_remote=True)
        return

    # Команда завершения смены
    if text == "⏹️ Завершить смену":
        user_data = get_user_data(tguser)
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден в базе данных")
            return

        result = set_onshift(tguser, False)
        
        if result:
            current_time = datetime.now()
            await update.message.reply_text(
                f"✅ *Смена завершена*\n\n"
                f"🕐 Время завершения: {current_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"👤 Сотрудник: {user_data[0]}",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            log_shift_exchange('info', 'Смена завершена', 
                              user=tguser, action='end_shift')
        else:
            await update.message.reply_text(
                "❌ Ошибка при завершении смены",
                reply_markup=get_main_menu_keyboard()
            )


async def handle_sd_operations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик операций ServiceDesk"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    
    if text == "📋 Мои текущие заявки":
        # Получаем текущие заявки и задачи
        user_data = get_user_data(tguser)
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден в базе данных")
            return

        name = user_data[0]
        static_user = get_static_user_from_db(name)
        
        if not static_user:
            await update.message.reply_text("❌ Статический пользователь не найден")
            return

        login_result = await perform_login_and_action(
            static_user['username'],
            static_user['password'],
            lambda cookies: get_current_requests_and_tasks(static_user['username'], cookies)
        )
        
        if login_result['success']:
            requests_data = login_result['result']
            
            if not requests_data['requests'] and not requests_data['tasks']:
                await update.message.reply_text("📋 *Активных заявок и задач нет*")
                return
            
            message_parts = ["📋 *Ваши текущие заявки и задачи:*\n"]
            
            if requests_data['requests']:
                message_parts.append("*🎫 Заявки:*")
                for req in requests_data['requests']:
                    message_parts.append(f"• #{req['id']} - {req['subject']}")
                    message_parts.append(f"  📊 {req['status']} | 🕐 {req['created_time']}")
                message_parts.append("")
            
            if requests_data['tasks']:
                message_parts.append("*📋 Задачи:*")
                for task in requests_data['tasks']:
                    message_parts.append(f"• #{task['id']} - {task['title']}")
                    message_parts.append(f"  📊 {task['status']} | 🕐 {task['created_time']}")
            
            response_text = "\n".join(message_parts)
            
            # Разделяем на части, если сообщение слишком длинное
            if len(response_text) > 4000:
                parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await update.message.reply_text(part, parse_mode='markdown')
            else:
                await update.message.reply_text(response_text, parse_mode='markdown')
        else:
            await update.message.reply_text(f"❌ Ошибка получения данных: {login_result['error']}")
    
    elif text == "📈 Статистика":
        stats = get_current_statistics()
        await update.message.reply_text(
            f"📈 *Статистика системы*\n\n"
            f"👥 Активных пользователей: {stats['active_users']}\n"
            f"🔄 Смен сегодня: {stats['shifts_today']}\n"
            f"⏰ Напоминаний активных: {stats['active_reminders']}\n"
            f"🏠 Запросов на удаленку (месяц): {stats['remote_requests_month']}",
            parse_mode='markdown'
        )


async def handle_transfer_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик диалога передачи заявок"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    
    if text == "🔄 Передать заявки":
        context.user_data['transfer_state'] = 'waiting_for_ids'
        await update.message.reply_text(
            "🔄 *Передача заявок*\n\n"
            "Введите номера заявок через запятую (например: 123456, 654321):",
            reply_markup=get_input_keyboard(),
            parse_mode='markdown'
        )
        return
    
    # Обработка ввода номеров заявок
    if context.user_data.get('transfer_state') == 'waiting_for_ids':
        try:
            # Парсим номера заявок
            request_ids = [int(x.strip()) for x in text.split(',')]
            context.user_data['transfer_request_ids'] = request_ids
            context.user_data['transfer_state'] = 'waiting_for_target'
            
            await update.message.reply_text(
                f"📋 *Заявки для передачи:* {', '.join(map(str, request_ids))}\n\n"
                "👤 Введите username получателя:",
                reply_markup=get_input_keyboard(),
                parse_mode='markdown'
            )
        except ValueError:
            await update.message.reply_text(
                "❌ *Неверный формат*\n\n"
                "Введите номера заявок через запятую (только цифры):",
                reply_markup=get_input_keyboard(),
                parse_mode='markdown'
            )
        return
    
    # Обработка ввода получателя
    if context.user_data.get('transfer_state') == 'waiting_for_target':
        target_username = text.strip()
        request_ids = context.user_data.get('transfer_request_ids', [])
        
        # Подтверждение передачи
        context.user_data['transfer_target'] = target_username
        
        await update.message.reply_text(
            f"❓ *Подтвердите передачу*\n\n"
            f"📋 Заявки: {', '.join(map(str, request_ids))}\n"
            f"👤 Получатель: {target_username}\n\n"
            f"Продолжить?",
            reply_markup=get_confirmation_keyboard(),
            parse_mode='markdown'
        )
        return


async def handle_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик текстовых сообщений"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    
    # Обработка различных типов сообщений
    if text in ["🚀 Начать смену", "🏠 Начать смену (Удаленно)", "⏹️ Завершить смену"]:
        await handle_start_shift_conversation(update, context)
    elif text in ["🔄 Отдать смену (Поменяться сменами)", "Поменяться сменами"]:
        await handle_shift_exchange_conversation(update, context)
    elif text in ["📋 Запросить удаленку", "🏠 Запросить удаленку"]:
        from src.handlers.remote_work_handler import handle_remote_request_conversation
        await handle_remote_request_conversation(update, context)
    elif text in ["🔔 Создать напоминание"]:
        await handle_reminder_conversation(update, context)
    elif text in ["📋 Мои текущие заявки", "📈 Статистика"]:
        await handle_sd_operations(update, context)
    elif text in ["🔄 Передать заявки"]:
        await handle_transfer_conversation(update, context)
    elif text in ["🏠 Главное меню"]:
        # Очищаем состояние пользователя и возвращаем в главное меню
        context.user_data.clear()
        await start_command(update, context)
    else:
        # Обработка состояний диалогов
        if context.user_data.get('shift_state'):
            await handle_start_shift_conversation(update, context)
        elif context.user_data.get('exchange_state'):
            await handle_shift_exchange_conversation(update, context)
        elif context.user_data.get('remote_state'):
            from src.handlers.remote_work_handler import handle_remote_request_conversation
            await handle_remote_request_conversation(update, context)
        elif context.user_data.get('reminder_state'):
            await handle_reminder_conversation(update, context)
        elif context.user_data.get('transfer_state'):
            await handle_transfer_conversation(update, context)


async def handle_exchange_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команд обмена смен"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    command = update.message.text
    
    # Команды подтверждения/отклонения обмена смен
    if command.startswith('/approve_exchange_'):
        from src.handlers.shift_exchange_handler import handle_exchange_approval
        await handle_exchange_approval(update, context, approve=True)
    elif command.startswith('/reject_exchange_'):
        from src.handlers.shift_exchange_handler import handle_exchange_approval
        await handle_exchange_approval(update, context, approve=False)
    else:
        # Неизвестная команда
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /start для получения списка доступных функций.",
            reply_markup=get_main_menu_keyboard()
        )



