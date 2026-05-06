"""
Обёртки для обработчиков с проверкой авторизации
"""

from src.middleware.auth_middleware import check_user_access


def with_auth(handler):
    """
    Декоратор для добавления проверки авторизации к обработчикам
    """
    async def wrapper(update, context):
        try:
            # Игнорируем сообщения в группах - бот не должен на них реагировать
            if update.effective_chat.type != 'private':
                return
            
            # Проверяем авторизацию только для личных сообщений
            if not await check_user_access(update, context):
                return
            
            # Если проверка прошла, вызываем оригинальный обработчик
            return await handler(update, context)
        except Exception as e:
            print(f"[ERROR] Auth wrapper error: {e}")
            try:
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ Произошла ошибка при проверке доступа.\n"
                        "Попробуйте еще раз."
                    )
            except Exception as reply_error:
                print(f"[ERROR] Failed to send auth error message: {reply_error}")
    
    return wrapper


def group_ignore(handler):
    """
    Декоратор для игнорирования сообщений в группах
    """
    async def wrapper(update, context):
        # Игнорируем все сообщения не из личных чатов
        if update.effective_chat.type != 'private':
            return
        
        return await handler(update, context)
    
    return wrapper
