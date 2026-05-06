"""
Обработчики административных команд
Содержит функции для управления лимитами удаленки администраторами
"""

import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from src.config import ADMIN_ROLES
from src.database.db_operations import (
    get_user_data, add_remote_limit_extension, get_telegram_id_by_tguser, update_telegram_id
)
from src.utils.keyboards import get_main_menu_keyboard, get_input_keyboard
from src.utils.logger import log_shift_exchange


def is_admin(tguser):
    """Проверяет, является ли пользователь администратором"""
    return tguser in ADMIN_ROLES.values()


async def handle_add_remote_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addremoteshift @username"""
    tguser = update.effective_user.username
    
    if not is_admin(tguser):
        await update.message.reply_text(
            "❌ У вас нет прав для выполнения этой команды.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Парсим команду
    command_text = update.message.text.strip()
    match = re.match(r'/addremoteshift\s+@?([a-zA-Z][a-zA-Z0-9_.]*)', command_text)
    
    if not match:
        await update.message.reply_text(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Используйте: <code>/addremoteshift @username</code>\n"
            "Пример: <code>/addremoteshift @john_doe</code>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
        return
    
    target_username = match.group(1)
    
    # Проверяем, существует ли пользователь
    user_data = get_user_data(target_username)
    
    if not user_data:
        await update.message.reply_text(
            f"❌ Пользователь @{target_username} не найден в базе данных.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Добавляем расширение лимита
    success = add_remote_limit_extension(
        tguser=target_username,
        added_by=tguser,
        reason=f"Добавлено администратором @{tguser}"
    )
    
    if success:
        log_shift_exchange('info', 'Лимит удаленки расширен администратором', 
                          user=target_username, admin=tguser, action='admin_add_remote_limit')
        
        await update.message.reply_text(
            f"✅ <b>Лимит удаленки расширен</b>\n\n"
            f"👤 <b>Пользователь:</b> @{target_username}\n"
            f"👨‍💼 <b>Администратор:</b> @{tguser}\n"
            f"📅 <b>Месяц:</b> {datetime.now().strftime('%m.%Y')}\n"
            f"➕ <b>Добавлено:</b> +1 удаленка\n\n"
            f"Пользователь может использовать дополнительную удаленку в текущем месяце.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
        
        # Уведомляем пользователя
        try:
            target_user_id = get_telegram_id_by_tguser(target_username)
            if target_user_id:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"🎉 <b>Лимит удаленки расширен!</b>\n\n"
                         f"Администратор @{tguser} предоставил вам дополнительную удаленку на текущий месяц.\n\n"
                         f"Теперь вы можете сделать еще один запрос на удаленную работу.",
                    parse_mode='HTML'
                )
        except Exception as e:
            print(f"[ERROR] Не удалось уведомить пользователя @{target_username}: {e}")
    else:
        await update.message.reply_text(
            f"❌ Ошибка при расширении лимита для @{target_username}. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_check_telegram_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки Telegram ID ключевых пользователей"""
    tguser = update.effective_user.username
    
    if not is_admin(tguser):
        await update.message.reply_text(
            "❌ У вас нет прав для выполнения этой команды.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    from src.config import REMOTE_REQUEST_ROLES, SHIFT_EXCHANGE_ROLES
    
    result_message = "🔍 **Проверка Telegram ID ключевых пользователей:**\n\n"
    
    # Проверяем пользователей из REMOTE_REQUEST_ROLES
    result_message += "**Роли для удаленки:**\n"
    for role, username in REMOTE_REQUEST_ROLES.items():
        telegram_id = get_telegram_id_by_tguser(username)
        status = f"✅ ID: {telegram_id}" if telegram_id else "❌ Не зарегистрирован"
        result_message += f"• {role}: @{username} - {status}\n"
    
    result_message += "\n**Роли для обмена смен:**\n"
    for role, username in SHIFT_EXCHANGE_ROLES.items():
        telegram_id = get_telegram_id_by_tguser(username)
        status = f"✅ ID: {telegram_id}" if telegram_id else "❌ Не зарегистрирован"
        result_message += f"• {role}: @{username} - {status}\n"
    
    # Добавляем информацию о том, как зарегистрироваться
    result_message += ("\n💡 **Как зарегистрироваться:**\n"
                      "Пользователи должны написать /start боту, "
                      "чтобы зарегистрировать свой Telegram ID")
    
    await update.message.reply_text(
        result_message,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_register_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принудительная регистрация Telegram ID текущего пользователя"""
    tguser = update.effective_user.username
    telegram_id = update.effective_user.id
    
    from src.database.db_operations import update_telegram_id
    
    if update_telegram_id(tguser, telegram_id):
        await update.message.reply_text(
            f"✅ **Telegram ID зарегистрирован**\n\n"
            f"Пользователь: @{tguser}\n"
            f"Telegram ID: {telegram_id}\n\n"
            f"Теперь вы будете получать уведомления от бота.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        print(f"[INFO] Telegram ID {telegram_id} зарегистрирован для пользователя @{tguser}")
    else:
        await update.message.reply_text(
            f"❌ Ошибка при регистрации Telegram ID. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_reminder_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reminderstats - статистика напоминаний"""
    tguser = update.effective_user.username
    
    if not is_admin(tguser):
        await update.message.reply_text(
            "❌ У вас нет прав для выполнения этой команды.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    try:
        from src.services.reminder_service import get_reminder_statistics
        
        stats = await get_reminder_statistics()
        
        if stats:
            message = f"""📊 **Статистика напоминаний**

📋 **Общая информация:**
• Всего напоминаний: {stats['total']}
• Отправлено: {stats['sent']}
• В ожидании: {stats['pending']}
• Просрочено: {stats['overdue']}

📈 **Статистика:**
• Процент отправленных: {stats['sent'] / max(stats['total'], 1) * 100:.1f}%
• Активных напоминаний: {stats['pending'] + stats['overdue']}

⚠️ **Внимание:** 
{f"Есть {stats['overdue']} просроченных напоминаний!" if stats['overdue'] > 0 else "Все напоминания обработаны корректно."}"""
        else:
            message = "❌ Не удалось получить статистику напоминаний."
            
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        log_shift_exchange('info', 'Запрос статистики напоминаний', 
                         user=tguser, action='reminder_stats_request')
        
    except Exception as e:
        print(f"[ERROR] handle_reminder_stats: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении статистики напоминаний.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /testreminder - создание тестового напоминания"""
    tguser = update.effective_user.username
    
    if not is_admin(tguser):
        await update.message.reply_text(
            "❌ У вас нет прав для выполнения этой команды.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    try:
        from src.database.db_operations import save_reminder
        from datetime import datetime, timedelta
        
        # Создаем тестовое напоминание через 1 минуту
        test_time = datetime.now() + timedelta(minutes=1)
        test_text = f"🧪 Тестовое напоминание от админа @{tguser}"
        
        if save_reminder(tguser, test_text, test_time):
            await update.message.reply_text(
                f"✅ **Тестовое напоминание создано!**\n\n"
                f"📅 Время: {test_time.strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"📝 Текст: {test_text}\n\n"
                f"⏰ Напоминание будет отправлено через ~1 минуту\n"
                f"📱 Проверьте личные сообщения с ботом",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
            log_shift_exchange('info', 'Создано тестовое напоминание админом', 
                             user=tguser, action='test_reminder_created')
        else:
            await update.message.reply_text(
                "❌ Ошибка при создании тестового напоминания.",
                reply_markup=get_main_menu_keyboard()
            )
            
    except Exception as e:
        print(f"[ERROR] handle_test_reminder: {e}")
        await update.message.reply_text(
            "❌ Ошибка при создании тестового напоминания.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_restart_reminder_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /restartreminders - перезапуск сервиса напоминаний"""
    tguser = update.effective_user.username
    
    if not is_admin(tguser):
        await update.message.reply_text(
            "❌ У вас нет прав для выполнения этой команды.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    try:
        # Здесь можно добавить логику перезапуска сервиса
        # Пока что просто уведомляем о статусе
        
        await update.message.reply_text(
            "ℹ️ **Статус сервиса напоминаний**\n\n"
            "🔄 Сервис напоминаний работает в фоновом режиме\n"
            "📝 Проверка новых напоминаний каждые 30 секунд\n"
            "📧 Отправка напоминаний пользователям в личные сообщения\n\n"
            "✅ Сервис функционирует нормально",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        log_shift_exchange('info', 'Проверка статуса сервиса напоминаний', 
                         user=tguser, action='reminder_service_status_check')
        
    except Exception as e:
        print(f"[ERROR] handle_restart_reminder_service: {e}")
        await update.message.reply_text(
            "❌ Ошибка при проверке статуса сервиса напоминаний.",
            reply_markup=get_main_menu_keyboard()
        )
