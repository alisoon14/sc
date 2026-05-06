"""
Обработчик обмена сменами
Содержит логику создания, согласования и выполнения обменов
"""

from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.database.db_operations import (
    get_user_data, get_shift_by_user_and_date, get_shift_type_name,
    get_telegram_id_by_tguser, get_db_connection
)
from src.database.shift_exchange import (
    create_shift_exchange, get_shift_exchange, update_exchange_approval,
    reject_shift_exchange, is_shift_exchangeable, execute_shift_transfer,
    is_exchange_fully_approved, get_user_role_for_exchange, get_shift_exchange_details
)
from src.utils.keyboards import get_main_menu_keyboard, get_input_keyboard, get_yes_no_keyboard, get_employees_keyboard
from src.utils.logger import log_shift_exchange
from src.config import SHIFT_EXCHANGE_ROLES


async def handle_shift_exchange_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик диалога обмена сменами"""
    # Проверяем тип чата - обработчик работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    text = update.message.text
    tguser = update.effective_user.username
    user_data = get_user_data(tguser)

    # Начало обмена смен
    if text in ["🔄 Отдать смену (Поменяться сменами)", "Поменяться сменами"]:
        log_shift_exchange('info', 'Пользователь начал процесс обмена сменами', 
                          user=tguser, action='start_exchange')
        context.user_data['exchange_state'] = 'waiting_for_date'
        
        await update.message.reply_text(
            "🔄 *Система обмена сменами*\n\n"
            "📋 *Инструкция:*\n"
            "1. Введите дату смены, которую хотите передать\n"
            "2. Выберите коллегу из списка\n"
            "3. Система отправит запрос на согласование\n"
            "4. Обмен произойдет после подтверждения всех сторон\n\n"
            "⚠️ *Обратите внимание:*\n"
            "• Некоторые типы смен не подлежат обмену\n"
            "• При совпадении смен типы могут автоматически измениться\n"
            "• Все изменения нужно проверить в календаре\n\n"
            "📅 Введите дату смены в формате *ДД.ММ.ГГГГ*:",
            reply_markup=get_input_keyboard(),
            parse_mode='markdown'
        )
        return

    # Ввод даты смены
    if context.user_data.get('exchange_state') == 'waiting_for_date':
        try:
            date = datetime.strptime(text, "%d.%m.%Y").date()
            log_shift_exchange('info', 'Дата смены введена корректно', 
                              user=tguser, date=date.strftime('%d.%m.%Y'), action='date_input')
        except ValueError:
            log_shift_exchange('warning', 'Неверный формат даты', 
                              user=tguser, input_text=text, action='date_error')
            await update.message.reply_text(
                "❌ *Неверный формат даты*\n\n"
                "Пожалуйста, введите дату в правильном формате:\n"
                "*ДД.ММ.ГГГГ*\n\n"
                "Пример: 25.12.2025",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            return

        # Ищем смену пользователя на указанную дату
        shift = get_shift_by_user_and_date(tguser, date)
        if not shift:
            log_shift_exchange('warning', 'Смена не найдена на указанную дату', 
                              user=tguser, date=date.strftime('%d.%m.%Y'), action='shift_not_found')
            await update.message.reply_text(
                f"❌ *Смена не найдена*\n\n"
                f"📅 Дата: {date.strftime('%d.%m.%Y')}\n\n"
                f"⚠️ У вас нет назначенной смены на эту дату.\n"
                f"Проверьте правильность даты или ваш график работы.\n\n"
                f"🌐 Календарь смен: https://smena.center2m.com/calendar",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.pop('exchange_state', None)
            return

        # Проверяем, разрешен ли обмен для данного типа смены
        if not is_shift_exchangeable(shift['shift_type_id']):
            shift_type_name = get_shift_type_name(shift['shift_type_id'])
            log_shift_exchange('warning', 'Попытка обмена запрещенного типа смены', 
                              user=tguser, date=date.strftime('%d.%m.%Y'), 
                              shift_type_id=shift['shift_type_id'], 
                              shift_type_name=shift_type_name, 
                              action='forbidden_shift_type')
            await update.message.reply_text(
                f"❌ *Обмен невозможен*\n\n"
                f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
                f"🏷️ Тип смены: {shift_type_name}\n\n"
                f"⚠️ Смены данного типа не подлежат обмену согласно внутренним правилам.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.pop('exchange_state', None)
            return

        log_shift_exchange('info', 'Смена найдена и допустима для обмена', 
                          user=tguser, date=date.strftime('%d.%m.%Y'), 
                          shift_id=shift['id'], shift_type_id=shift['shift_type_id'], 
                          action='shift_found')

        # Сохраняем данные в контексте
        context.user_data.update({
            'exchange_state': 'waiting_for_recipient',
            'exchange_date': date,
            'schedule_id': shift['id'],
            'shift_type_id': shift['shift_type_id']
        })

        # Получаем список сотрудников
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, tguser FROM Employees WHERE active = 1 AND tguser != %s", (tguser,))
                employees = cursor.fetchall()

        context.user_data['available_recipients'] = {emp['name']: emp['tguser'] for emp in employees}

        shift_type_name = get_shift_type_name(shift['shift_type_id'])
        await update.message.reply_text(
            f"✅ *Смена найдена*\n\n"
            f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
            f"🏷️ Тип смены: {shift_type_name}\n"
            f"🆔 ID смены: {shift['id']}\n\n"
            f"👥 *Выберите коллегу* из списка ниже, которому хотите передать эту смену:\n\n"
            f"💡 *Подсказка:* Нажмите на имя сотрудника из предложенного списка",
            reply_markup=get_employees_keyboard(employees),
            parse_mode='markdown'
        )
        return

    # Выбор получателя
    if context.user_data.get('exchange_state') == 'waiting_for_recipient':
        recipient_name = text.strip()
        recipients = {k.strip(): v for k, v in context.user_data.get('available_recipients', {}).items()}

        if recipient_name not in recipients:
            log_shift_exchange('warning', 'Выбран несуществующий получатель', 
                              user=tguser, recipient_input=recipient_name, action='invalid_recipient')
            
            # Пересоздаем кнопки со списком сотрудников
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT name, tguser FROM Employees WHERE active = 1 AND tguser != %s", (tguser,))
                    employees = cursor.fetchall()
            
            await update.message.reply_text(
                "⚠️ *Сотрудник не найден*\n\n"
                "Пожалуйста, выберите сотрудника из предложенного списка выше.\n\n"
                "💡 *Подсказка:* Нажмите на кнопку с именем сотрудника,\n"
                "не вводите имя вручную.",
                reply_markup=get_employees_keyboard(employees),
                parse_mode='markdown'
            )
            return

        # Сохраняем получателя
        context.user_data.update({
            'recipient_name': recipient_name,
            'recipient_tguser': recipients[recipient_name],
            'exchange_state': 'waiting_for_confirmation'
        })

        log_shift_exchange('info', 'Получатель выбран', 
                          user=tguser, recipient_name=recipient_name, 
                          recipient_tguser=recipients[recipient_name], action='recipient_selected')

        shift_type_name = get_shift_type_name(context.user_data['shift_type_id'])
        preview = f"""🔁 *Предпросмотр обмена сменами*

📋 *Детали передаваемой смены:*
📅 Дата: {context.user_data['exchange_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {shift_type_name}
🆔 ID смены: {context.user_data['schedule_id']}

👥 *Участники обмена:*
📤 Передает: {user_data[0]} (вы)
📥 Принимает: {recipient_name}

⚠️ *Важно:*
• После подтверждения отменить обмен будет невозможно
• Принимающий сотрудник должен согласиться первым
• Затем согласование проходит у руководства
• Все участники получат уведомления о статусе

✅ Подтвердить создание запроса?  
_Ответьте: *Да* или *Нет*_"""
        
        # Кнопки для подтверждения
        await update.message.reply_text(
            preview, 
            reply_markup=get_yes_no_keyboard(),
            parse_mode='markdown'
        )
        return

    # Подтверждение создания обмена
    if context.user_data.get('exchange_state') == 'waiting_for_confirmation':
        if text.strip().lower() == 'да':
            log_shift_exchange('info', 'Пользователь подтвердил создание обмена', 
                              user=tguser, action='exchange_confirmed')
            
            # Создаем запрос на обмен
            exchange_id = create_shift_exchange(
                context.user_data['schedule_id'],
                tguser,
                context.user_data['recipient_tguser']
            )
            
            if not exchange_id:
                await update.message.reply_text("❌ Ошибка при создании запроса на обмен.")
                return

            # Отправляем уведомление принимающему
            await send_exchange_notification_to_recipient(context, exchange_id, user_data)
            
            await update.message.reply_text(
                "✅ *Запрос отправлен!*\n\n"
                f"📤 Запрос на обмен отправлен сотруднику: *{context.user_data['recipient_name']}*\n\n"
                f"📱 Сотрудник получит уведомление в Telegram\n"
                f"⏳ Ожидайте ответа от принимающей стороны\n"
                f"🔔 Вы получите уведомление о статусе обмена",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.clear()
        else:
            log_shift_exchange('info', 'Пользователь отменил создание обмена', 
                              user=tguser, action='exchange_cancelled')
            await update.message.reply_text(
                "❌ *Обмен отменён*\n\n"
                "Запрос на обмен сменой не был создан.\n"
                "Вы можете начать новый обмен в любое время.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='markdown'
            )
            context.user_data.clear()
        return


async def send_exchange_notification_to_recipient(context, exchange_id, user_data):
    """Отправляет уведомление о запросе обмена принимающему сотруднику"""
    from src.utils.keyboards import get_shift_exchange_inline_keyboard
    
    shift_type_name = get_shift_type_name(context.user_data['shift_type_id'])
    
    message = f"""📨 <b>Запрос на обмен сменами</b>

👋 Вам поступил запрос на принятие смены от коллеги!

📋 <b>Детали передаваемой смены:</b>
📅 Дата: {context.user_data['exchange_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {shift_type_name}
🆔 ID смены: {context.user_data['schedule_id']}

👥 <b>Участники:</b>
📤 Передает: {user_data[0]} (@{context.user_data.get('tguser', 'N/A')})
📥 Принимает: {context.user_data['recipient_name']} (вы)

ℹ️ <b>Процесс согласования:</b>
1. Сначала подтверждаете вы (принимающий)
2. Затем подтверждает руководство
3. После всех согласований смена будет передана

⚠️ <b>Внимание:</b> Проверьте свой график на указанную дату!"""

    recipient_id = get_telegram_id_by_tguser(context.user_data['recipient_tguser'])
    print(f"[DEBUG] Попытка отправить уведомление пользователю: {context.user_data['recipient_tguser']}")
    print(f"[DEBUG] Telegram ID для {context.user_data['recipient_tguser']}: {recipient_id}")
    
    if recipient_id:
        try:
            from telegram import Bot
            from src.config import TELEGRAM_BOT_TOKEN
            
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=recipient_id,
                text=message,
                parse_mode='HTML',
                reply_markup=get_shift_exchange_inline_keyboard(exchange_id)
            )
            print(f"[DEBUG] Уведомление успешно отправлено {context.user_data['recipient_tguser']} (ID: {recipient_id})")
            log_shift_exchange('info', 'Уведомление отправлено принимающему', 
                              exchange_id=exchange_id, 
                              recipient=context.user_data['recipient_tguser'],
                              recipient_id=recipient_id, action='notification_sent')
        except Exception as e:
            log_shift_exchange('error', 'Ошибка при отправке уведомления', 
                              exchange_id=exchange_id, error=str(e), action='notification_error')
            print(f"[ERROR] Ошибка при отправке уведомления: {e}")
    else:
        log_shift_exchange('error', 'Telegram ID получателя не найден', 
                          exchange_id=exchange_id, 
                          recipient=context.user_data['recipient_tguser'],
                          action='recipient_id_not_found')
        print(f"[ERROR] Telegram ID не найден для пользователя {context.user_data['recipient_tguser']}")
        print(f"[INFO] Возможно, пользователь {context.user_data['recipient_tguser']} не зарегистрирован в боте")


async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, tguser: str, exchange_id: int):
    """Обрабатывает подтверждение обмена"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    log_shift_exchange('info', 'Начало процесса подтверждения обмена', 
                      exchange_id=exchange_id, user=tguser, action='confirmation_start')

    exchange = get_shift_exchange(exchange_id)
    if not exchange:
        log_shift_exchange('warning', 'Обмен не найден', 
                          exchange_id=exchange_id, user=tguser, action='exchange_not_found')
        
        # Определяем тип ответа (callback query или обычное сообщение)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Обмен не найден или уже завершен.",
                parse_mode='markdown'
            )
        else:
            await update.message.reply_text("Обмен не найден.")
        return

    user_role = get_user_role_for_exchange(tguser)
    
    # Определяем, может ли пользователь согласовать обмен
    can_approve = False
    role_name = ""
    
    if not exchange['approved_by_recipient'] and tguser == exchange['recipient_tguser']:
        can_approve = True
        role_name = "Принимающий сотрудник"
        update_exchange_approval(exchange_id, 'recipient', True)
    elif exchange['approved_by_recipient'] and not exchange['approved_by_lead'] and user_role == 'lead':
        can_approve = True
        role_name = "Старший инженер"
        update_exchange_approval(exchange_id, 'lead', True)
    elif exchange['approved_by_recipient'] and not exchange['approved_by_manager'] and user_role == 'manager':
        can_approve = True
        role_name = "Руководитель"
        update_exchange_approval(exchange_id, 'manager', True)

    if not can_approve:
        message = ("⏳ *Ожидание согласования*\n\n"
                  "Сейчас не ваша очередь согласования или вы уже подтверждали этот обмен.")
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode='markdown'
            )
        else:
            await update.message.reply_text(message)
        return

    log_shift_exchange('info', f'{role_name} согласовал обмен', 
                      exchange_id=exchange_id, user=tguser, role=role_name, action='approval_given')

    # Проверяем, полностью ли согласован обмен
    updated_exchange = get_shift_exchange(exchange_id)
    if is_exchange_fully_approved(updated_exchange):
        # Выполняем перенос смены
        success, changes_message = execute_shift_transfer(exchange_id)
        
        if success:
            result_message = f"✅ *Обмен успешно завершён!*\n\n"
            if changes_message:
                result_message += f"{changes_message}\n\n"
            result_message += f"🌐 Проверьте изменения в календаре: https://smena.center2m.com/calendar"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(result_message, parse_mode='markdown')
            else:
                await update.message.reply_text(result_message, parse_mode='markdown')
            
            # Отправляем уведомление инициатору о завершении обмена
            await send_completion_notification_to_initiator(context, exchange_id, updated_exchange)
        else:
            error_message = f"❌ Ошибка при выполнении обмена: {changes_message}"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
    else:
        success_message = (f"✅ *Согласование принято*\n\n"
                          f"🎭 Роль: {role_name}\n"
                          f"⏳ Ожидание согласований других участников")
        
        if update.callback_query:
            await update.callback_query.edit_message_text(success_message, parse_mode='markdown')
        else:
            await update.message.reply_text(success_message, parse_mode='markdown')
        
        # Отправляем уведомления следующим участникам процесса согласования
        await send_next_approval_notifications(context, exchange_id, updated_exchange)


async def process_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, exchange_id: int):
    """Обрабатывает отклонение обмена"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    log_shift_exchange('info', 'Начало процесса отклонения обмена', 
                      exchange_id=exchange_id, user=update.effective_user.username, action='rejection_start')
    
    if reject_shift_exchange(exchange_id):
        log_shift_exchange('info', 'Обмен отклонен', 
                          exchange_id=exchange_id, 
                          rejected_by=update.effective_user.username,
                          action='exchange_rejected')
        
        rejection_message = ("❌ *Обмен отклонён*\n\n"
                           "Запрос на обмен сменой был отклонён.\n"
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
        
        # Отправляем уведомление инициатору об отклонении
        exchange = get_shift_exchange(exchange_id)
        if exchange:
            await send_rejection_notification_to_initiator(context, exchange_id, exchange, update.effective_user.username)
    else:
        error_message = "❌ Ошибка при отклонении обмена."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_message)
        else:
            await update.message.reply_text(error_message)


async def send_next_approval_notifications(context, exchange_id, exchange):
    """Отправляет уведомления следующим участникам процесса согласования"""
    from src.utils.keyboards import get_shift_exchange_inline_keyboard
    from src.config import SHIFT_EXCHANGE_ROLES
    from telegram import Bot
    from src.config import TELEGRAM_BOT_TOKEN
    
    # Определяем, кому нужно отправить уведомления
    notifications_to_send = []
    
    # Если принимающий согласился, но ни старший инженер, ни руководитель ещё не согласились
    if exchange['approved_by_recipient'] and not exchange['approved_by_lead'] and not exchange['approved_by_manager']:
        lead_username = SHIFT_EXCHANGE_ROLES.get('lead_engineer')
        manager_username = SHIFT_EXCHANGE_ROLES.get('manager')
        
        if lead_username:
            notifications_to_send.append(('lead_engineer', lead_username, 'Старший инженер'))
        if manager_username:
            notifications_to_send.append(('manager', manager_username, 'Руководитель'))
    
    # Отправляем уведомления
    for role_key, username, role_name in notifications_to_send:
        user_id = get_telegram_id_by_tguser(username)
        print(f"[DEBUG] Отправка уведомления о необходимости согласования обмена участнику: {username} (роль: {role_name})")
        print(f"[DEBUG] Telegram ID для {username}: {user_id}")
        
        if user_id:
            # Получаем информацию об обмене
            from src.database.shift_exchange import get_shift_exchange_details
            exchange_details = get_shift_exchange_details(exchange_id)
            
            if exchange_details:
                message = f"""📨 <b>Требуется согласование обмена смен</b>

👋 Ожидается ваше согласование обмена смен!

📋 <b>Детали обмена:</b>
📅 Дата: {exchange_details['shift_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {exchange_details['shift_type_name']}
🆔 ID смены: {exchange_details['schedule_id']}

👥 <b>Участники:</b>
📤 Передает: {exchange_details['requester_name']} (@{exchange_details['requester_tguser']})
📥 Принимает: {exchange_details['recipient_name']} (@{exchange_details['recipient_tguser']})

✅ <b>Статус согласований:</b>
{'✅' if exchange['approved_by_recipient'] else '⏳'} Принимающий сотрудник
{'✅' if exchange['approved_by_lead'] else '⏳'} Старший инженер
{'✅' if exchange['approved_by_manager'] else '⏳'} Руководитель

🎭 <b>Ваша роль:</b> {role_name}

ℹ️ <b>Процедура согласования:</b> Достаточно согласования любого из руководителей (старший инженер ИЛИ руководитель)

⚠️ <b>Важно:</b> Проверьте детали обмена перед согласованием!"""

                try:
                    bot = Bot(token=TELEGRAM_BOT_TOKEN)
                    await bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=get_shift_exchange_inline_keyboard(exchange_id)
                    )
                    print(f"[DEBUG] Уведомление о согласовании успешно отправлено {username} (ID: {user_id})")
                    log_shift_exchange('info', f'Уведомление о согласовании отправлено {role_name}', 
                                      exchange_id=exchange_id, 
                                      recipient=username,
                                      recipient_id=user_id, 
                                      role=role_name,
                                      action='approval_notification_sent')
                except Exception as e:
                    log_shift_exchange('error', f'Ошибка при отправке уведомления о согласовании {role_name}', 
                                      exchange_id=exchange_id, 
                                      error=str(e), 
                                      role=role_name,
                                      action='approval_notification_error')
                    print(f"[ERROR] Ошибка при отправке уведомления о согласовании {username}: {e}")
            else:
                print(f"[ERROR] Не удалось получить детали обмена {exchange_id}")
        else:
            print(f"[ERROR] Telegram ID не найден для участника согласования {username} (роль: {role_name})")
            print(f"[INFO] Возможно, пользователь {username} не зарегистрирован в боте")
    
    # Также уведомляем инициатора об изменении статуса
    if exchange_details:
        await send_status_update_to_initiator(exchange_id, exchange, exchange_details)


async def send_status_update_to_initiator(exchange_id, exchange, exchange_details):
    """Отправляет уведомление инициатору об изменении статуса обмена"""
    from telegram import Bot
    from src.config import TELEGRAM_BOT_TOKEN
    
    initiator_id = get_telegram_id_by_tguser(exchange['initiator_tguser'])
    print(f"[DEBUG] Отправка уведомления о статусе обмена инициатору: {exchange['initiator_tguser']}")
    print(f"[DEBUG] Telegram ID для {exchange['initiator_tguser']}: {initiator_id}")
    
    if initiator_id:
        # Формируем статус согласований
        status_text = "📊 <b>Статус согласований:</b>\n"
        status_text += f"{'✅' if exchange['approved_by_recipient'] else '⏳'} Принимающий сотрудник\n"
        status_text += f"{'✅' if exchange['approved_by_lead'] else '⏳'} Старший инженер\n"
        status_text += f"{'✅' if exchange['approved_by_manager'] else '⏳'} Руководитель"
        
        # Определяем текущий этап
        if exchange['approved_by_recipient'] and not exchange['approved_by_lead']:
            current_stage = "Ожидание согласования старшим инженером"
        elif exchange['approved_by_recipient'] and exchange['approved_by_lead'] and not exchange['approved_by_manager']:
            current_stage = "Ожидание согласования руководителем"
        else:
            current_stage = "Обработка..."
        
        message = f"""📈 <b>Обновление статуса обмена смен</b>

📋 <b>Детали обмена:</b>
📅 Дата: {exchange_details['shift_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {exchange_details['shift_type_name']}
👥 С кем меняетесь: {exchange_details['recipient_name']}

{status_text}

⏳ <b>Текущий этап:</b> {current_stage}

💡 Вы получите уведомление, когда обмен будет полностью согласован."""

        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=initiator_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"[DEBUG] Уведомление о статусе успешно отправлено инициатору {exchange['initiator_tguser']} (ID: {initiator_id})")
            log_shift_exchange('info', 'Уведомление о статусе отправлено инициатору', 
                              exchange_id=exchange_id, 
                              initiator=exchange['initiator_tguser'],
                              initiator_id=initiator_id, 
                              action='status_notification_sent')
        except Exception as e:
            log_shift_exchange('error', 'Ошибка при отправке уведомления о статусе инициатору', 
                              exchange_id=exchange_id, 
                              error=str(e), 
                              action='status_notification_error')
            print(f"[ERROR] Ошибка при отправке уведомления о статусе {exchange['initiator_tguser']}: {e}")
    else:
        print(f"[ERROR] Telegram ID не найден для инициатора {exchange['initiator_tguser']}")
        print(f"[INFO] Возможно, пользователь {exchange['initiator_tguser']} не зарегистрирован в боте")


async def send_completion_notification_to_initiator(context, exchange_id, exchange):
    """Отправляет уведомление инициатору о завершении обмена"""
    from telegram import Bot
    from src.config import TELEGRAM_BOT_TOKEN
    
    # Получаем детальную информацию об обмене
    exchange_details = get_shift_exchange_details(exchange_id)
    if not exchange_details:
        log_shift_exchange('error', 'Не удалось получить детали обмена для уведомления о завершении', 
                          exchange_id=exchange_id, action='completion_notification_error')
        return
    
    initiator_id = get_telegram_id_by_tguser(exchange['initiator_tguser'])
    print(f"[DEBUG] Отправка уведомления о завершении обмена инициатору: {exchange['initiator_tguser']}")
    print(f"[DEBUG] Telegram ID для {exchange['initiator_tguser']}: {initiator_id}")
    
    if initiator_id:
        message = f"""🎉 <b>Обмен смен успешно завершён!</b>

📋 <b>Детали обмена:</b>
📅 Дата: {exchange_details['shift_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {exchange_details['shift_type_name']}
🆔 ID смены: {exchange_details['schedule_id']}

👥 <b>Участники:</b>
📤 Передали: {exchange_details['requester_name']} (@{exchange_details['requester_tguser']})
📥 Принял: {exchange_details['recipient_name']} (@{exchange_details['recipient_tguser']})

✅ <b>Все согласования получены:</b>
✅ Принимающий сотрудник
✅ {('Старший инженер' if exchange['approved_by_lead'] else 'Руководитель')}

🌐 <b>Смена успешно передана!</b>
Проверьте изменения в календаре: https://smena.center2m.com/calendar

📱 <b>Что дальше:</b>
• Смена отображается в календаре у принимающего сотрудника
• Вы освобождены от этой смены
• При необходимости свяжитесь с принимающим для координации"""

        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=initiator_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"[DEBUG] Уведомление о завершении успешно отправлено инициатору {exchange['initiator_tguser']} (ID: {initiator_id})")
            log_shift_exchange('info', 'Уведомление о завершении отправлено инициатору', 
                              exchange_id=exchange_id, 
                              initiator=exchange['initiator_tguser'],
                              initiator_id=initiator_id, 
                              action='completion_notification_sent')
        except Exception as e:
            log_shift_exchange('error', 'Ошибка при отправке уведомления о завершении инициатору', 
                              exchange_id=exchange_id, 
                              error=str(e), 
                              action='completion_notification_error')
            print(f"[ERROR] Ошибка при отправке уведомления о завершении {exchange['initiator_tguser']}: {e}")
    else:
        log_shift_exchange('warning', 'Telegram ID не найден для отправки уведомления о завершении', 
                          initiator=exchange['initiator_tguser'], 
                          action='completion_notification_failed')
        print(f"[WARNING] Telegram ID не найден для пользователя {exchange['initiator_tguser']}")


async def send_rejection_notification_to_initiator(context, exchange_id, exchange, rejected_by):
    """Отправляет уведомление инициатору об отклонении обмена"""
    from telegram import Bot
    from src.config import TELEGRAM_BOT_TOKEN
    
    # Получаем детальную информацию об обмене
    exchange_details = get_shift_exchange_details(exchange_id)
    if not exchange_details:
        log_shift_exchange('error', 'Не удалось получить детали обмена для уведомления об отклонении', 
                          exchange_id=exchange_id, action='rejection_notification_error')
        return
    
    initiator_id = get_telegram_id_by_tguser(exchange['initiator_tguser'])
    print(f"[DEBUG] Отправка уведомления об отклонении обмена инициатору: {exchange['initiator_tguser']}")
    print(f"[DEBUG] Telegram ID для {exchange['initiator_tguser']}: {initiator_id}")
    
    if initiator_id:
        message = f"""❌ <b>Обмен смен отклонён</b>

📋 <b>Детали обмена:</b>
📅 Дата: {exchange_details['shift_date'].strftime('%d.%m.%Y')}
🏷️ Тип смены: {exchange_details['shift_type_name']}
🆔 ID смены: {exchange_details['schedule_id']}

👥 <b>Участники:</b>
📤 Передавали: {exchange_details['requester_name']} (@{exchange_details['requester_tguser']})
📥 Должен был принять: {exchange_details['recipient_name']} (@{exchange_details['recipient_tguser']})

🚫 <b>Обмен отклонён пользователем:</b> @{rejected_by}

💡 <b>Что делать дальше:</b>
• Вы можете попробовать договориться с другим сотрудником
• Используйте команду /exchange для создания нового запроса
• При необходимости обратитесь к руководству

📝 <b>Совет:</b> Убедитесь, что принимающий сотрудник может работать в указанную дату"""

        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=initiator_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"[DEBUG] Уведомление об отклонении успешно отправлено инициатору {exchange['initiator_tguser']} (ID: {initiator_id})")
            log_shift_exchange('info', 'Уведомление об отклонении отправлено инициатору', 
                              exchange_id=exchange_id, 
                              initiator=exchange['initiator_tguser'],
                              initiator_id=initiator_id,
                              rejected_by=rejected_by, 
                              action='rejection_notification_sent')
        except Exception as e:
            log_shift_exchange('error', 'Ошибка при отправке уведомления об отклонении инициатору', 
                              exchange_id=exchange_id, 
                              error=str(e), 
                              action='rejection_notification_error')
            print(f"[ERROR] Ошибка при отправке уведомления об отклонении {exchange['initiator_tguser']}: {e}")
    else:
        log_shift_exchange('warning', 'Telegram ID не найден для отправки уведомления об отклонении', 
                          initiator=exchange['initiator_tguser'], 
                          action='rejection_notification_failed')
        print(f"[WARNING] Telegram ID не найден для пользователя {exchange['initiator_tguser']}")


async def handle_exchange_approval(update: Update, context: ContextTypes.DEFAULT_TYPE, approve: bool = True):
    """Обработчик одобрения/отклонения обмена смен"""
    # Проверяем тип чата - команда работает только в личных сообщениях
    if update.effective_chat.type != 'private':
        return
    
    command = update.message.text
    tguser = update.effective_user.username
    
    try:
        # Извлекаем ID обмена из команды
        if approve:
            exchange_id = int(command.replace('/approve_exchange_', ''))
        else:
            exchange_id = int(command.replace('/reject_exchange_', ''))
        
        if approve:
            await process_confirmation(update, context, tguser, exchange_id)
        else:
            await process_rejection(update, context, exchange_id)
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ *Ошибка обработки команды*\n\n"
            "Неверный формат команды. Попробуйте еще раз.",
            parse_mode='markdown'
        )
