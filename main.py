"""
Основной файл Telegram бота для управления сменами
Реструктурированная версия с разделением на модули
"""

import asyncio
import sys
import os

# Добавляем путь к корневой директории проекта
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Импорт компонентов Telegram Bot API
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Импорты из модульной структуры
from src.config import TELEGRAM_BOT_TOKEN, validate_config
from src.utils.auth_decorators import with_auth, group_ignore
from src.handlers.command_handlers import (
    start_command as start,
    handle_main_message,
    handle_exchange_commands,
    note_command,
    refresh_command
)
from src.handlers.remote_work_handler import handle_remote_commands
from src.handlers.admin_handlers import (
    handle_add_remote_shift, handle_check_telegram_ids, handle_register_telegram_id,
    handle_reminder_stats, handle_restart_reminder_service, handle_test_reminder
)
from src.handlers.callback_handlers import handle_callback_query
from src.services.reminder_service import reminder_checker



def main():
    """Основная функция запуска бота"""

    try:
        validate_config()
    except EnvironmentError as error:
        print(f"[ERROR] Configuration invalid: {error}")
        sys.exit(1)

    print("[INFO] Starting SmenaControl Bot (Refactored Version)")
    
    # Создание приложения бота
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавляем обработчик ошибок
    async def error_handler(update, context):
        """Обработчик ошибок бота"""
        import traceback
        print(f"[ERROR] Bot error: {context.error}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        # Если ошибка произошла в личном чате, уведомляем пользователя
        if update and update.effective_chat and update.effective_chat.type == 'private':
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка при обработке запроса.\n"
                    "Попробуйте еще раз или обратитесь к администратору."
                )
            except Exception as e:
                print(f"[ERROR] Failed to send error message: {e}")
    
    app.add_error_handler(error_handler)
    # Регистрация обработчиков с проверкой авторизации
    app.add_handler(CommandHandler("start", with_auth(start)))
    app.add_handler(CommandHandler("note", with_auth(note_command)))  
    app.add_handler(CommandHandler("refresh", with_auth(refresh_command)))
    # Административные команды
    app.add_handler(CommandHandler("addremoteshift", with_auth(handle_add_remote_shift)))
    app.add_handler(CommandHandler("checktelegramids", with_auth(handle_check_telegram_ids)))
    app.add_handler(CommandHandler("registertelegramid", with_auth(handle_register_telegram_id)))
    app.add_handler(CommandHandler("reminderstats", with_auth(handle_reminder_stats)))
    app.add_handler(CommandHandler("restartreminders", with_auth(handle_restart_reminder_service)))
    app.add_handler(CommandHandler("testreminder", with_auth(handle_test_reminder)))
    # Обработчик callback queries (inline кнопки) - только для личных чатов
    app.add_handler(CallbackQueryHandler(group_ignore(handle_callback_query)))
    # Обработчик команд обмена смен и удаленной работы - только для личных чатов
    app.add_handler(MessageHandler(filters.COMMAND, with_auth(handle_exchange_commands)))
    app.add_handler(MessageHandler(filters.Regex(r"^/(approve_remote_|reject_remote_)\d+$"), with_auth(handle_remote_commands)))
    # Основной обработчик сообщений - только для авторизованных пользователей в личных чатах
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, with_auth(handle_main_message)))
    
    # Обработчик для игнорирования всех сообщений в группах (должен быть последним)
    async def ignore_group_messages(update, context):
        """Игнорирует все сообщения в группах"""
        pass
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, ignore_group_messages), group=-1)
    
    # Функция инициализации фоновых задач
    async def post_init(app):
        """Запуск фоновых задач"""
        asyncio.create_task(reminder_checker())
        print("[INFO] Background tasks initialized")
    
    app.post_init = post_init
    
    print("[INFO] Bot is starting... Press Ctrl+C to stop")
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
    except Exception as e:
        print(f"[ERROR] Bot error: {e}")


if __name__ == "__main__":
    main()
