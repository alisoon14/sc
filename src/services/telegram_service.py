"""
Модуль для работы с Telegram API
Содержит функции для отправки сообщений
"""

import requests
from src.config import TELEGRAM_API_BASE, TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID_TB, THREAD_ID, REMOTE_NOTIFICATIONS


def send_telegram_message(message):
    """Отправляет сообщение в основной чат"""
    # Проверяем настройки уведомлений
    if not REMOTE_NOTIFICATIONS["send_to_main_chat"]:
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print("[DEBUG] Отправка в основной чат отключена в настройках")
        return True
    
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print(f"[DEBUG] Сообщение в основной чат отправлено. Response Code: {response.status_code}")
        return response.ok
    except Exception as e:
        print(f"[ERROR] send_telegram_message: {e}")
        return False


def send_telegram_message_tb(message_tb):
    """Отправляет сообщение в техподдержку"""
    # Проверяем настройки уведомлений
    if not REMOTE_NOTIFICATIONS["send_to_tb_chat"]:
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print("[DEBUG] Отправка в TB чат отключена в настройках")
        return True
    
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID_TB,
        'message_thread_id': THREAD_ID,
        'text': message_tb,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print(f"[DEBUG] Сообщение в TB чат отправлено. Response Code: {response.status_code}")
        print("Response Code:", response.status_code)
        print("Response JSON:", response.json())
        return response.ok
    except Exception as e:
        print(f"[ERROR] send_telegram_message_tb: {e}")
        return False


def send_shift_start_notification_to_groups(message):
    """ТОЛЬКО для уведомлений о начале смены - отправляет в группы принудительно"""
    # Отправляем в основной чат
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print(f"[DEBUG] Уведомление о начале смены отправлено в основной чат. Response Code: {response.status_code}")
        return response.ok
    except Exception as e:
        print(f"[ERROR] send_shift_start_notification_to_groups: {e}")
        return False


def send_shift_start_notification_to_tb(message_tb):
    """ТОЛЬКО для уведомлений о начале смены - отправляет в TB принудительно"""
    # Отправляем в TB чат
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID_TB,
        'message_thread_id': THREAD_ID,
        'text': message_tb,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        if REMOTE_NOTIFICATIONS["debug_mode"]:
            print(f"[DEBUG] Уведомление о начале смены отправлено в TB чат. Response Code: {response.status_code}")
        print("Response Code:", response.status_code)
        print("Response JSON:", response.json())
        return response.ok
    except Exception as e:
        print(f"[ERROR] send_shift_start_notification_to_tb: {e}")
        return False


def perform_login_and_action(phone):
    """Выполняет логин и действие с номером телефона"""
    from src.config import LOGIN_URL, ACTION_URL
    
    with requests.Session() as session:
        # Шаг 1: Выполняем логин и получаем куки, заголовки и другие данные
        login_payload = 'number=4997540778&pin=9645&check=1&logtype=dnis'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            login_response = session.post(LOGIN_URL, headers=headers, data=login_payload)
            
            if login_response.ok:
                print("[INFO] Успешный вход. PHPSESSID сохранен в сессии.")
            else:
                print("[ERROR] Ошибка при логине.")
                return False
            
            # Шаг 2: Используем ту же сессию для выполнения второго запроса
            action_payload = f'number=4997540778&pin=9645&check=1&logtype=dnis&b=1&o1=1&o2=1&p={phone}&d=40&upd='
            action_response = session.post(ACTION_URL, headers=headers, data=action_payload)
            
            return action_response.ok
            
        except Exception as e:
            print(f"[ERROR] perform_login_and_action: {e}")
            return False
