"""
Обработчики callback queries для inline кнопок
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.handlers.shift_exchange_handler import process_confirmation, process_rejection
from src.handlers.remote_work_handler import process_remote_request_approval, process_remote_request_rejection
from src.database.shift_exchange import log_shift_exchange


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик callback queries"""
    query = update.callback_query
    await query.answer()  # Убираем "loading" состояние кнопки
    
    callback_data = query.data
    user = update.effective_user
    tguser = user.username
    
    log_shift_exchange('info', 'Получен callback query', 
                      user=tguser, callback_data=callback_data, action='callback_received')
    
    # Обработка подтверждения обмена смен
    if callback_data.startswith('confirm_exchange_'):
        exchange_id = int(callback_data.replace('confirm_exchange_', ''))
        log_shift_exchange('info', 'Callback подтверждения обмена', 
                          exchange_id=exchange_id, user=tguser, action='confirm_callback')
        
        await process_confirmation(update, context, tguser, exchange_id)
        return
    
    # Обработка отклонения обмена смен
    if callback_data.startswith('reject_exchange_'):
        exchange_id = int(callback_data.replace('reject_exchange_', ''))
        log_shift_exchange('info', 'Callback отклонения обмена', 
                          exchange_id=exchange_id, user=tguser, action='reject_callback')
        
        await process_rejection(update, context, exchange_id)
        return
    
    # Обработка одобрения запроса удаленки
    if callback_data.startswith('approve_remote_'):
        request_id = int(callback_data.replace('approve_remote_', ''))
        log_shift_exchange('info', 'Callback одобрения удаленки', 
                          request_id=request_id, user=tguser, action='approve_remote_callback')
        
        await process_remote_request_approval(update, context, tguser, request_id)
        return
    
    # Обработка отклонения запроса удаленки
    if callback_data.startswith('reject_remote_'):
        request_id = int(callback_data.replace('reject_remote_', ''))
        log_shift_exchange('info', 'Callback отклонения удаленки', 
                          request_id=request_id, user=tguser, action='reject_remote_callback')
        
        await process_remote_request_rejection(update, context, request_id)
        return
    
    # Если callback_data не распознан
    log_shift_exchange('warning', 'Неизвестный callback query', 
                      user=tguser, callback_data=callback_data, action='unknown_callback')
    await query.edit_message_text("❌ Неизвестная команда")
