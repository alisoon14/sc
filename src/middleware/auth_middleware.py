"""
Middleware для авторизации пользователей
Проверяет доступ пользователей к боту
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_operations import get_user_data
from src.utils.logger import log_shift_exchange


async def check_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет доступ пользователя к боту
    Возвращает True если пользователь авторизован, False если нет
    """
    try:
        # Игнорируем сообщения в группах - бот не должен на них реагировать
        if update.effective_chat.type != 'private':
            return False
        
        # Проверяем наличие username
        if not update.effective_user.username:
            await update.message.reply_text(
                "❌ Доступ запрещен\n\n"
                "У вас не установлен username в Telegram.\n"
                "Установите username в настройках Telegram и попробуйте снова."
            )
            
            log_shift_exchange('warning', 'Попытка доступа без username', 
                             user='unknown', 
                             telegram_id=update.effective_user.id,
                             action='access_denied_no_username')
            return False
        
        tguser = update.effective_user.username
        user_data = get_user_data(tguser)
        
        # Проверяем, есть ли пользователь в базе
        if not user_data:
            await update.message.reply_text(
                f"❌ Доступ запрещен\n\n"
                f"Пользователь @{tguser} не найден в базе данных.\n\n"
                f"Обратитесь к администратору для получения доступа к боту."
            )
            
            log_shift_exchange('warning', 'Попытка доступа неавторизованного пользователя', 
                             user=tguser, 
                             telegram_id=update.effective_user.id,
                             action='access_denied_not_in_db')
            return False
        
        # Пользователь авторизован
        return True
        
    except Exception as e:
        print(f"[ERROR] check_user_access error: {e}")
        try:
            await update.message.reply_text(
                "❌ Произошла ошибка при проверке доступа.\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
        except Exception as reply_error:
            print(f"[ERROR] Failed to send access check error message: {reply_error}")
        return False


async def auth_required(handler):
    """
    Декоратор для обработчиков, требующих авторизации
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Проверяем доступ пользователя
        if not await check_user_access(update, context):
            return
        
        # Если проверка прошла, вызываем оригинальный обработчик
        return await handler(update, context)
    
    return wrapper


def create_auth_filter():
    """
    Создает фильтр для проверки авторизации
    """
    async def auth_filter(update: Update):
        # Игнорируем сообщения в группах
        if update.effective_chat.type != 'private':
            return False
        
        # Проверяем username
        if not update.effective_user.username:
            return False
            
        # Проверяем наличие в базе
        tguser = update.effective_user.username
        user_data = get_user_data(tguser)
        return user_data is not None
    
    return auth_filter
