"""
Обработчики операций со сменами
Содержит функции для начала смены и связанных операций
"""

import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from src.database.db_operations import get_user_data, get_shift_notes, is_shift_remote_approved, set_onshift, update_start_shift_time, record_actual_shift_start
from src.services.servicedesk_api import get_current_requests_and_tasks, check_upcoming_changes, save_shift_start_assignments, generate_shift_report
from src.services.telegram_service import send_telegram_message, send_telegram_message_tb, perform_login_and_action
from src.utils.keyboards import get_main_menu_keyboard, get_input_keyboard
from src.config import REMOTE_NO_APPROVAL_USERS
from src.utils.logger import log_shift_exchange


def clean_id(request_id):
    """Очищает ID от специальных символов"""
    return re.sub(r'\W+', '', str(request_id))


async def start_shift(update: Update, context: ContextTypes.DEFAULT_TYPE, is_remote=False):
    """Обработчик начала смены"""
    tguser = update.effective_user.username
    mode_text = "Удаленно" if is_remote else "Из офиса"
    user_data = get_user_data(tguser)
    
    if not user_data:
        await update.message.reply_text(
            "❌ Пользователь не найден в базе данных.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Проверяем разрешение на удаленную работу
    if is_remote:
        current_date_obj = datetime.now().date()
        
        # Если у пользователя нет байпаса, проверяем одобрение
        if tguser not in REMOTE_NO_APPROVAL_USERS:
            if not is_shift_remote_approved(tguser, current_date_obj):
                await update.message.reply_text(
                    f"❌ <b>Удаленка не одобрена</b>\n\n"
                    f"На сегодня ({current_date_obj.strftime('%d.%m.%Y')}) нет одобренного запроса на удаленную работу.\n\n"
                    f"Сначала создайте запрос через <b>\"📋 Запросить удаленку\"</b> и дождитесь одобрения.",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='HTML'
                )
                return
    
    name, phone, grade = user_data
    print(f"[DEBUG] Данные пользователя {tguser}: name='{name}', phone='{phone}', grade='{grade}'")
    current_date = datetime.now().strftime("%d.%m.%Y")
    current_time = datetime.now().strftime("%H:%M")

    # Получаем актуальные данные о заявках и задачах
    allrequests, alltasks = get_current_requests_and_tasks()
    
    # Формируем отчет по предыдущей смене ПЕРЕД очисткой списков
    try:
        print(f"[DEBUG] Генерация отчета по предыдущей смене...")
        shift_report = generate_shift_report()
        print(f"[DEBUG] Отчет сгенерирован успешно")
    except Exception as e:
        print(f"[ERROR] Ошибка генерации отчета: {e}")
        shift_report = "Ошибка получения отчета по предыдущей смене"
    
    # Сохраняем списки назначенных заявок и задач при начале смены
    # При каждом старте смены список автоматически очищается и заполняется заново
    save_shift_start_assignments(tguser, allrequests, alltasks)
    
    # Устанавливаем приоритетный номер телефона на WestCall
    print(f"[DEBUG] Устанавливаем номер телефона {phone} на WestCall...")
    try:
        westcall_result = perform_login_and_action(phone)
        if westcall_result:
            print(f"[INFO] Номер телефона {phone} успешно установлен на WestCall")
        else:
            print(f"[WARNING] Не удалось установить номер телефона {phone} на WestCall")
    except Exception as e:
        print(f"[ERROR] Ошибка установки номера на WestCall: {e}")

    # Формируем ссылки на заявки
    request_links = [
        f"<a href=\"https://support.center2m.com/WorkOrder.do?woMode=viewWO&woID={clean_id(request_id)}\">{clean_id(request_id)}</a>"
        for request_id in allrequests
    ]
    
    # Формируем ссылки на задачи
    task_links = [
        f"<a href=\"https://support.center2m.com/ui/tasks?mode=detail&from=showAllTasks&taskId={clean_id(task_id)}\">{clean_id(task_id)}</a>"
        for task_id in alltasks
    ]

    request_links_text = "\n".join(request_links) if request_links else "Заявки отсутствуют."
    task_links_text = "\n".join(task_links) if task_links else "Задачи отсутствуют."
    
    # Получаем информацию о плановых работах
    upcoming_changes = check_upcoming_changes()
    
    # Получаем заметки смены
    notes = get_shift_notes()
    if notes:
        notes_text = "\n".join(
            [f"- {row['timestamp'].strftime('%d.%m.%Y %H:%M')} — {row['name']} — {row['note_text']}" for row in notes]
        )
    else:
        notes_text = "Нет записей."

    # Формируем основное сообщение
    message = f"""<b>🚀 Заступление на смену ({mode_text})</b>

<b>👤 Пользователь:</b> <a href="t.me/{tguser}">{name}</a>
<b>📅 Дата:</b> {current_date}  
<b>⏰ Время:</b> {current_time}  
<b>📞 Установлен приоритетный номер телефона ТП:</b> {phone}

<b>📩 Назначены следующие заявки, требующие внимания:</b>
{request_links_text}

<b>🗂 Назначены следующие задачи, требующие внимания:</b>
{task_links_text}

<b>📓 Протокол смены:</b>
{notes_text}

<b>🔧 Ближайшие плановые работы:</b>

{upcoming_changes}

<b>📊 Отчет по предыдущей смене:</b>

{shift_report}
"""

    # Устанавливаем статус "на смене" в базе данных
    set_onshift_result = set_onshift(tguser)
    if set_onshift_result:
        # Обновляем время начала смены (LastLoginTime)
        update_start_shift_time_result = update_start_shift_time(tguser)
        if update_start_shift_time_result:
            print(f"[INFO] LastLoginTime обновлен для пользователя {tguser}")
        else:
            print(f"[WARNING] Не удалось обновить LastLoginTime для пользователя {tguser}")
        
        # Записываем фактическое время заступления на смену
        actual_start_time = datetime.now()
        record_actual_result = record_actual_shift_start(tguser, actual_start_time)
        if record_actual_result:
            print(f"[INFO] Фактическое время заступления записано для пользователя {tguser}: {actual_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"[WARNING] Не удалось записать фактическое время заступления для пользователя {tguser}")
            
        log_shift_exchange('info', f'Смена начата {mode_text}', 
                          user=tguser, action='start_shift')
        print(f"[INFO] Пользователь {tguser} начал смену ({mode_text})")
    else:
        log_shift_exchange('error', f'Ошибка установки статуса onshift', 
                          user=tguser, action='start_shift_error')
        print(f"[WARNING] Не удалось установить статус onshift для пользователя {tguser}")

    # Отправляем сообщения
    send_telegram_message(message)

    # Сокращенное сообщение для техподдержки
    message_tb = f"""<b>🚀 Заступление на смену ({mode_text})</b>

<b>👤 Пользователь:</b> <a href="t.me/{tguser}">{name}</a>
<b>📅 Дата:</b> {current_date}  
<b>⏰ Время:</b> {current_time}  
<b>📞 Установлен приоритетный номер телефона ТП:</b> {phone}
"""
    send_telegram_message_tb(message_tb)
      
    # Подтверждение пользователю
    if set_onshift_result:
        await update.message.reply_text(
            f"✅ <b>Смена начата {mode_text}</b>\n\n"
            f"🕐 Время начала: {current_time}\n"
            f"📊 Статус: На смене",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"⚠️ <b>Смена начата {mode_text}</b>\n\n"
            f"🕐 Время начала: {current_time}\n"
            f"⚠️ Предупреждение: Возможны проблемы с установкой статуса",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
