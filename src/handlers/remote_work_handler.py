"""
Обработчик запросов на удаленную работу
Содержит логику создания, согласования и выполнения запросов на удаленку
"""

import re
from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.database.db_operations import (
    get_user_data, get_telegram_id_by_tguser, get_db_connection,
    create_remote_request, get_remote_request, update_remote_request_approval,
    approve_remote_request, reject_remote_request, get_monthly_remote_count,
    is_shift_remote_approved, get_shift_by_user_and_date, get_user_available_remote_limit
)
from src.utils.keyboards import get_main_menu_keyboard, get_input_keyboard, get_yes_no_keyboard
from src.utils.logger import log_shift_exchange
from src.config import (
    REMOTE_REQUEST_ROLES, 
    REMOTE_NO_APPROVAL_USERS, 
    REMOTE_MONTHLY_LIMIT,
    REMOTE_NOTIFICATIONS
)


async def handle_remote_request_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик диалога запроса удаленки"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    user_data = get_user_data(tguser)

    # Начало запроса удаленки
    if text in ["📋 Запросить удаленку", "🏠 Запросить удаленку"]:
        log_shift_exchange('info', 'Пользователь начал запрос удаленки', 
                          user=tguser, action='start_remote_request')
        
        # Проверяем, есть ли у пользователя байпас
        if tguser in REMOTE_NO_APPROVAL_USERS:
            await update.message.reply_text(
                f"🔓 *У вас есть БАЙПАС удаленки!*\n\n"
                f"Вам не нужно создавать запросы на удаленную работу.\n"
                f"Просто используйте кнопку *\"🏠 Начать смену (Удаленно)\"* когда хотите работать удаленно.\n\n"
                f"Система автоматически одобрит вашу удаленную смену без согласования.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            return
        
        # Проверяем лимит за текущий месяц
        current_date = datetime.now()
        monthly_count = get_monthly_remote_count(tguser, current_date.year, current_date.month)
        available_limit = get_user_available_remote_limit(tguser, current_date.year, current_date.month)
        
        # Получаем информацию о грейде для отображения
        user_data = get_user_data(tguser)
        grade_info = ""
        if user_data:
            _, _, grade = user_data
            if grade == 'Джуниор (Jun)':
                grade_info = "\n💡 *Ваш лимит:* Джуниор (Jun) — 0 удаленок/месяц"
            elif grade == 'Специалист (Mid)':
                grade_info = "\n💡 *Ваш лимит:* Специалист (Mid) — 1 удаленка/месяц"
            elif grade == 'Продвинутый (Adv)':
                grade_info = "\n💡 *Ваш лимит:* Продвинутый (Adv) — 2 удаленки/месяц"
        
        if monthly_count >= available_limit:
            await update.message.reply_text(
                f"❌ *Лимит исчерпан*\n\n"
                f"Вы уже использовали максимальное количество удаленок в этом месяце: {monthly_count}/{available_limit}{grade_info}\n\n"
                f"Следующий запрос можно будет сделать в следующем месяце.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            return

        context.user_data['remote_state'] = 'waiting_for_date'
        
        await update.message.reply_text(
            "🏠 *Запрос на удаленную работу*\n\n"
            "📋 *Инструкция:*\n"
            "1. Выберите дату смены для удаленной работы\n"
            "2. Укажите причину запроса\n"
            "3. Система отправит запрос на согласование\n"
            "4. После одобрения вы сможете взять смену удаленно\n\n"
            f"📊 *Статистика:* Использовано {monthly_count}/{available_limit} запросов в этом месяце{grade_info}\n\n"
            "📅 Введите дату смены в формате *ДД.ММ.ГГГГ*:",
            reply_markup=get_input_keyboard(),
            parse_mode='markdown'
        )
        return

    # Ввод даты смены
    if context.user_data.get('remote_state') == 'waiting_for_date':
        try:
            shift_date = datetime.strptime(text, "%d.%m.%Y").date()
            
            # Проверяем, что дата не в прошлом (разрешаем текущий день)
            if shift_date < datetime.now().date():
                await update.message.reply_text(
                    "⚠️ *Неверная дата*\n\n"
                    "Дата смены не может быть в прошлом.\n"
                    "Введите корректную дату в формате *ДД.ММ.ГГГГ*:",
                    reply_markup=get_input_keyboard(),
                    parse_mode='markdown'
                )
                return
            
            log_shift_exchange('info', 'Дата смены для удаленки введена корректно', 
                              user=tguser, date=shift_date.strftime('%d.%m.%Y'), action='remote_date_input')
        except ValueError:
            log_shift_exchange('warning', 'Неверный формат даты для удаленки', 
                              user=tguser, input_text=text, action='remote_date_error')
            await update.message.reply_text(
                "❌ *Неверный формат даты*\n\n"
                "Пожалуйста, введите дату в правильном формате:\n"
                "*ДД.ММ.ГГГГ*\n\n"
                "Пример: 25.12.2025",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            return

        # Проверяем, есть ли у пользователя смена на эту дату
        shift = get_shift_by_user_and_date(tguser, shift_date)
        if not shift:
            await update.message.reply_text(
                f"❌ *Смена не найдена*\n\n"
                f"📅 Дата: {shift_date.strftime('%d.%m.%Y')}\n\n"
                f"⚠️ У вас нет назначенной смены на эту дату.\n"
                f"Проверьте правильность даты или ваш график работы.\n\n"
                f"🌐 Календарь смен: https://smena.center2m.com/calendar",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.pop('remote_state', None)
            return

        # Проверяем, не был ли уже запрос на эту дату
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT status FROM RemoteWorkRequests 
                        WHERE tguser = %s AND shift_date = %s AND status != 'rejected'
                    """, (tguser, shift_date))
                    existing_request = cursor.fetchone()
                    
                    if existing_request:
                        status_text = {
                            'pending': 'ожидает рассмотрения',
                            'approved': 'уже одобрен'
                        }.get(existing_request['status'], existing_request['status'])
                        
                        await update.message.reply_text(
                            f"⚠️ *Запрос уже существует*\n\n"
                            f"📅 Дата: {shift_date.strftime('%d.%m.%Y')}\n"
                            f"📊 Статус: {status_text}\n\n"
                            f"Вы не можете создать повторный запрос на эту дату.",
                            reply_markup=get_main_menu_keyboard(),
                            parse_mode='markdown'
                        )
                        context.user_data.pop('remote_state', None)
                        return
        except Exception as e:
            print(f"[ERROR] checking existing remote request: {e}")

        context.user_data.update({
            'remote_state': 'waiting_for_reason',
            'remote_date': shift_date
        })

        await update.message.reply_text(
            f"✅ *Дата принята*\n\n"
            f"📅 Смена: {shift_date.strftime('%d.%m.%Y')}\n\n"
            f"📝 Теперь укажите причину запроса на удаленную работу:\n\n"
            f"Например: Медицинские показания, семейные обстоятельства, транспортные проблемы и т.д.",
            reply_markup=get_input_keyboard(),
            parse_mode='markdown'
        )
        return

    # Ввод причины
    if context.user_data.get('remote_state') == 'waiting_for_reason':
        reason = text.strip()
        
        if len(reason) < 10:
            await update.message.reply_text(
                "⚠️ *Причина слишком короткая*\n\n"
                "Пожалуйста, укажите более подробную причину (минимум 10 символов):",
                reply_markup=get_input_keyboard(),
                parse_mode='markdown'
            )
            return

        context.user_data['remote_reason'] = reason
        context.user_data['remote_state'] = 'waiting_for_confirmation'

        preview = f"""🏠 *Предпросмотр запроса на удаленку*

📋 *Детали запроса:*
📅 Дата смены: {context.user_data['remote_date'].strftime('%d.%m.%Y')}
📝 Причина: {reason}
👤 Запрашивает: {user_data[0]} (вы)

ℹ️ *Процесс согласования:*
1. Запрос отправляется руководству
2. После одобрения вы сможете взять смену удаленно
3. Без одобрения удаленная работа будет заблокирована

✅ Подтвердить отправку запроса? (*Да* / *Нет*)"""

        await update.message.reply_text(
            preview,
            reply_markup=get_yes_no_keyboard(),
            parse_mode='markdown'
        )
        return

    # Подтверждение отправки запроса
    if context.user_data.get('remote_state') == 'waiting_for_confirmation':
        if text.strip().lower() == 'да':
            # Создаем запрос
            request_id = create_remote_request(
                tguser,
                context.user_data['remote_date'],
                context.user_data['remote_reason']
            )
            
            if not request_id:
                await update.message.reply_text("❌ Ошибка при создании запроса на удаленку.")
                return

            log_shift_exchange('info', 'Запрос на удаленку создан', 
                              user=tguser, request_id=request_id, 
                              date=context.user_data['remote_date'].strftime('%Y-%m-%d'),
                              action='remote_request_created')

            # Проверяем, нужно ли согласование
            if tguser in REMOTE_NO_APPROVAL_USERS:
                # Автоматически одобряем
                approve_remote_request(request_id)
                await update.message.reply_text(
                    "✅ *Запрос автоматически одобрен!*\n\n"
                    f"📅 Дата: {context.user_data['remote_date'].strftime('%d.%m.%Y')}\n"
                    f"🏠 Вы можете взять смену удаленно в указанную дату",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='markdown'
                )
            else:
                # Отправляем уведомления руководству (только если включено)
                if REMOTE_NOTIFICATIONS["send_to_approvers"]:
                    await send_remote_request_notifications(context, request_id, user_data)
                elif REMOTE_NOTIFICATIONS["debug_mode"]:
                    print(f"[DEBUG] Уведомления руководителям отключены. Запрос ID: {request_id}")
                
                await update.message.reply_text(
                    "✅ *Запрос отправлен!*\n\n"
                    f"📤 Запрос на удаленку отправлен руководству\n"
                    f"📱 Руководство получит уведомление в Telegram\n"
                    f"⏳ Ожидайте решения по запросу\n"
                    f"🔔 Вы получите уведомление о результате",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='markdown'
                )
            
            context.user_data.clear()
        else:
            await update.message.reply_text(
                "❌ *Запрос отменён*\n\n"
                "Запрос на удаленную работу не был отправлен.\n"
                "Вы можете создать новый запрос в любое время.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.clear()
        return


async def send_remote_request_notifications(context, request_id, user_data):
    """Отправляет уведомления о запросе на удаленку руководству"""
    from src.utils.keyboards import get_remote_request_inline_keyboard
    
    message = f"""🏠 *Запрос на удаленную работу*

👋 Поступил новый запрос на удаленную работу!

📋 *Детали запроса:*
📅 Дата смены: {context.user_data['remote_date'].strftime('%d.%m.%Y')}
📝 Причина: {context.user_data['remote_reason']}
👤 Сотрудник: {user_data[0]} (@{context.user_data.get('tguser', 'N/A')})

ℹ️ *Примечание:* После одобрения сотрудник сможет взять смену удаленно"""

    # Отправляем только личные сообщения руководителям
    for role, tg_username in REMOTE_REQUEST_ROLES.items():
        print(f"[DEBUG] Попытка отправить уведомление пользователю: {tg_username} (роль: {role})")
        user_id = get_telegram_id_by_tguser(tg_username)
        print(f"[DEBUG] Telegram ID для {tg_username}: {user_id}")
        
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=get_remote_request_inline_keyboard(request_id)
                )
                print(f"[DEBUG] Уведомление успешно отправлено {tg_username} (ID: {user_id})")
                if REMOTE_NOTIFICATIONS["debug_mode"]:
                    print(f"[DEBUG] Уведомление отправлено {tg_username} (ID: {user_id})")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить уведомление {tg_username}: {e}")
        else:
            print(f"[ERROR] Telegram ID не найден для пользователя {tg_username}")
            print(f"[INFO] Возможно, пользователь {tg_username} не зарегистрирован в боте")


async def process_remote_request_approval(update: Update, context: ContextTypes.DEFAULT_TYPE, tguser: str, request_id: int):
    """Обрабатывает одобрение запроса на удаленку"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    log_shift_exchange('info', 'Начало процесса одобрения запроса удаленки', 
                      request_id=request_id, user=tguser, action='remote_approval_start')

    remote_request = get_remote_request(request_id)
    if not remote_request:
        error_message = "Запрос на удаленку не найден."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)
        return

    # Проверяем права пользователя
    user_role = None
    if tguser == REMOTE_REQUEST_ROLES.get('lead_engineer'):
        user_role = 'lead'
    elif tguser == REMOTE_REQUEST_ROLES.get('manager'):
        user_role = 'manager'
    
    if not user_role:
        error_message = "У вас нет прав для одобрения этого запроса."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)
        return

    # Обновляем статус согласования
    update_remote_request_approval(request_id, user_role, True)
    approve_remote_request(request_id)

    role_name = "Старший инженер" if user_role == 'lead' else "Руководитель"
    log_shift_exchange('info', f'{role_name} одобрил запрос на удаленку', 
                      request_id=request_id, user=tguser, role=role_name, action='remote_approved')

    approval_message = (f"✅ *Запрос на удаленку одобрен*\n\n"
                       f"👤 {role_name} одобрил запрос\n"
                       f"📅 Дата: {remote_request['shift_date'].strftime('%d.%m.%Y')}\n"
                       f"🏠 Сотрудник может взять смену удаленно")

    if update.callback_query:
        await update.callback_query.edit_message_text(
            approval_message,
            parse_mode='markdown'
        )
    else:
        await update.message.reply_text(
            approval_message,
            parse_mode='markdown'
        )

    # Уведомляем инициатора (только если включено)
    if REMOTE_NOTIFICATIONS["send_to_requesters"]:
        initiator_id = get_telegram_id_by_tguser(remote_request['tguser'])
        if initiator_id:
            try:
                await context.bot.send_message(
                    chat_id=initiator_id,
                    text=f"✅ *Запрос на удаленку одобрен!*\n\n"
                         f"📅 Дата: {remote_request['shift_date'].strftime('%d.%m.%Y')}\n"
                         f"👤 Одобрил: {role_name}\n"
                         f"🏠 Теперь вы можете взять смену удаленно в указанную дату",
                    parse_mode='markdown'
                )
            except Exception as e:
                print(f"[ERROR] Failed to notify initiator: {e}")
    elif REMOTE_NOTIFICATIONS["debug_mode"]:
        print(f"[DEBUG] Уведомление пользователю отключено. Запрос {request_id} одобрен")


async def process_remote_request_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Обрабатывает отклонение запроса на удаленку"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    log_shift_exchange('info', 'Начало процесса отклонения запроса удаленки', 
                      request_id=request_id, user=update.effective_user.username, action='remote_rejection_start')
    
    remote_request = get_remote_request(request_id)
    if not remote_request:
        error_message = "Запрос на удаленку не найден."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)
        return

    if reject_remote_request(request_id):
        log_shift_exchange('info', 'Запрос на удаленку отклонен', 
                          request_id=request_id, 
                          rejected_by=update.effective_user.username,
                          action='remote_rejected')
        
        rejection_message = ("❌ *Запрос на удаленку отклонён*\n\n"
                           "Запрос был отклонён.\n"
                           "Инициатор получит уведомление об отклонении.")
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                rejection_message,
                parse_mode='markdown'
            )
        else:
            await update.message.reply_text(
                rejection_message,
                parse_mode='markdown'
            )

        # Уведомляем инициатора (только если включено)
        if REMOTE_NOTIFICATIONS["send_to_requesters"]:
            initiator_id = get_telegram_id_by_tguser(remote_request['tguser'])
            if initiator_id:
                try:
                    await context.bot.send_message(
                        chat_id=initiator_id,
                        text=f"❌ *Запрос на удаленку отклонён*\n\n"
                             f"📅 Дата: {remote_request['shift_date'].strftime('%d.%m.%Y')}\n"
                             f"К сожалению, ваш запрос был отклонён.\n"
                             f"Вы можете обратиться к руководству для выяснения причин.",
                        parse_mode='markdown'
                    )
                except Exception as e:
                    print(f"[ERROR] Failed to notify initiator: {e}")
        elif REMOTE_NOTIFICATIONS["debug_mode"]:
            print(f"[DEBUG] Уведомление пользователю отключено. Запрос {request_id} отклонен")
    else:
        error_message = "❌ Ошибка при отклонении запроса."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)


async def handle_remote_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик команд для удаленной работы"""
    # Проверяем тип чата - команды работают только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    command = update.message.text
    tguser = update.effective_user.username
    
    try:
        if command.startswith("/approve_remote_"):
            request_id = int(command.split("_")[2])
            await process_remote_request_approval(update, context, tguser, request_id)
        elif command.startswith("/reject_remote_"):
            request_id = int(command.split("_")[2])
            await process_remote_request_rejection(update, context, request_id)
        else:
            await update.message.reply_text("❌ Неизвестная команда для удаленной работы.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Неверный формат команды.")
    except Exception as e:
        print(f"[ERROR] handle_remote_commands: {e}")
        await update.message.reply_text("❌ Ошибка при обработке команды.")
