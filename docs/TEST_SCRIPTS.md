#  Скрипты для тестирования SmenaControl Bot

Файл со всеми готовыми скриптами для проверки и тестирования проекта.

---

##  Как использовать

1. **Скопируйте нужный скрипт** из раздела ниже
2. **Создайте файл** в корне проекта (например `test_db.py`)
3. **Запустите**: `python test_db.py`

---

## 1⃣ Проверка системы (verify_setup.py)

```python
#!/usr/bin/env python
"""
Полная проверка настройки SmenaControl Bot
Запуск: python verify_setup.py
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("1⃣  Python версия...")
    try:
        if sys.version_info < (3, 7):
            print(f"    Python {sys.version.split()[0]} (нужно 3.7+)")
            return False
        print(f"    Python {sys.version.split()[0]}")
        return True
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n2⃣  Проверка зависимостей...")
    dependencies = {
        'telegram': 'python-telegram-bot',
        'pymysql': 'PyMySQL',
        'requests': 'requests',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"    {name}")
        except ImportError:
            print(f"    {name} (НЕ УСТАНОВЛЕН)")
            missing.append(module)
    
    if missing:
        print(f"\n     Установите: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Проверка файла .env"""
    print("\n3⃣  Проверка файла .env...")
    if not Path('.env').exists():
        print("    .env не найден")
        print("    Создайте файл .env в корне проекта")
        return False
    print("    .env найден")
    return True

def check_config():
    """Проверка конфигурации"""
    print("\n4⃣  Проверка конфигурации...")
    try:
        from src.config import TELEGRAM_BOT_TOKEN, DB_HOST, DB_NAME
        
        if not TELEGRAM_BOT_TOKEN:
            print("    TELEGRAM_BOT_TOKEN пуст")
            return False
        print(f"    TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...")
        
        if not DB_HOST:
            print("    DB_HOST пуст")
            return False
        print(f"    DB_HOST: {DB_HOST}")
        
        if not DB_NAME:
            print("    DB_NAME пуст")
            return False
        print(f"    DB_NAME: {DB_NAME}")
        
        return True
    except Exception as e:
        print(f"    Ошибка: {e}")
        return False

def check_db_connection():
    """Проверка подключения к БД"""
    print("\n5⃣  Проверка подключения БД...")
    try:
        from src.database.db_operations import get_db_connection
        conn = get_db_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM Employees")
            result = cursor.fetchone()
            count = result['count']
        
        conn.close()
        print(f"    БД подключена")
        print(f"    Пользователей в БД: {count}")
        return True
    except Exception as e:
        print(f"    Ошибка подключения: {e}")
        return False

def main():
    print("="*50)
    print(" ПРОВЕРКА НАСТРОЙКИ SmenaControl Bot")
    print("="*50 + "\n")
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_config(),
        check_db_connection()
    ]
    
    print("\n" + "="*50)
    if all(checks):
        print(" ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("="*50)
        print("\n Вы готовы запустить проект:\n   python main.py\n")
        return 0
    else:
        print(" НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("="*50)
        print("\nПожалуйста, исправьте ошибки выше.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Запуск:**
```bash
python verify_setup.py
```

---

## 2⃣ Проверка подключения к БД (test_db_connection.py)

```python
#!/usr/bin/env python
"""
Проверка подключения к базе данных
Запуск: python test_db_connection.py
"""

import sys
from src.database.db_operations import get_db_connection, get_db_connection_2

def test_db1():
    """Проверка первой БД"""
    print("1⃣  Проверка первой БД (основная)...")
    try:
        conn = get_db_connection()
        
        with conn.cursor() as cursor:
            # Простой запрос
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Получить количество таблиц
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)
            tables = cursor.fetchone()['count']
            
            # Получить количество пользователей
            cursor.execute("SELECT COUNT(*) as count FROM Employees")
            users = cursor.fetchone()['count']
        
        conn.close()
        print("    БД #1 подключена успешно")
        print(f"    Таблиц: {tables}")
        print(f"    Пользователей: {users}\n")
        return True
        
    except Exception as e:
        print(f"    Ошибка БД #1: {e}\n")
        return False

def test_db2():
    """Проверка второй БД"""
    print("2⃣  Проверка второй БД (ServiceDesk)...")
    try:
        conn = get_db_connection_2()
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        conn.close()
        print("    БД #2 подключена успешно\n")
        return True
        
    except Exception as e:
        print(f"     БД #2 недоступна: {e}")
        print("   ℹ  Это нормально, если вторая БД еще не настроена\n")
        return False

def main():
    print("="*50)
    print("  ПРОВЕРКА БД ПОДКЛЮЧЕНИЙ")
    print("="*50 + "\n")
    
    results = {
        'db1': test_db1(),
        'db2': test_db2()
    }
    
    print("="*50)
    if results['db1']:
        print(" Основная БД работает!")
    else:
        print(" Ошибка основной БД!")
        return 1
    
    if results['db2']:
        print(" Обе БД готовы!")
    else:
        print("  Основная БД готова (вторая БД опциональна)")
    
    print("="*50 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Запуск:**
```bash
python test_db_connection.py
```

---

## 3⃣ Проверка операций с БД (test_db_operations.py)

```python
#!/usr/bin/env python
"""
Тестирование операций с базой данных
Запуск: python test_db_operations.py
"""

from src.database.db_operations import (
    get_user_data,
    get_today_shifts,
    get_pending_reminders,
    get_telegram_id_by_tguser
)

def test_get_user_data():
    """Тест: получение данных пользователя"""
    print("1⃣  Получение данных пользователя...")
    try:
        user = get_user_data("testuser")
        if user:
            name, phone, grade = user
            print(f"    Пользователь найден: {name}")
            print(f"      Телефон: {phone}")
            print(f"      Грейд: {grade}\n")
            return True
        else:
            print("   ℹ  Пользователь 'testuser' не найден\n")
            return True  # Не ошибка
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def test_get_today_shifts():
    """Тест: получение смен на сегодня"""
    print("2⃣  Получение смен на сегодня...")
    try:
        shifts = get_today_shifts()
        if shifts:
            print(f"    Смены найдены: {len(shifts)}")
            for shift in shifts[:3]:  # Первые 3
                print(f"      • {shift.get('name', '?')}")
            print()
        else:
            print("   ℹ  Смены на сегодня не найдены\n")
        return True
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def test_get_pending_reminders():
    """Тест: получение невыполненных напоминаний"""
    print("3⃣  Получение невыполненных напоминаний...")
    try:
        reminders = get_pending_reminders()
        if reminders:
            print(f"    Напоминания найдены: {len(reminders)}")
            for r in reminders[:2]:  # Первые 2
                print(f"      • ID: {r['id']}, От: {r.get('tguser', '?')}")
            print()
        else:
            print("   ℹ  Невыполненных напоминаний нет\n")
        return True
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def test_get_telegram_id():
    """Тест: получение Telegram ID"""
    print("4⃣  Получение Telegram ID...")
    try:
        tg_id = get_telegram_id_by_tguser("testuser")
        if tg_id:
            print(f"    Telegram ID найден: {tg_id}\n")
        else:
            print("   ℹ  Telegram ID не установлен\n")
        return True
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def main():
    print("="*50)
    print(" ТЕСТИРОВАНИЕ ОПЕРАЦИЙ С БД")
    print("="*50 + "\n")
    
    tests = [
        test_get_user_data(),
        test_get_today_shifts(),
        test_get_pending_reminders(),
        test_get_telegram_id()
    ]
    
    print("="*50)
    if all(tests):
        print(" ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
```

**Запуск:**
```bash
python test_db_operations.py
```

---

## 4⃣ Проверка Telegram API (test_telegram_api.py)

```python
#!/usr/bin/env python
"""
Проверка подключения к Telegram API
Запуск: python test_telegram_api.py
"""

import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_API_BASE

def test_telegram_connection():
    """Проверка подключения к Telegram"""
    print("1⃣  Проверка подключения к Telegram API...")
    
    try:
        # Получить информацию о боте
        url = f"{TELEGRAM_API_BASE}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print("    Подключение успешно")
                print(f"    Bot username: @{bot_info.get('username', '?')}")
                print(f"    Bot name: {bot_info.get('first_name', '?')}")
                print(f"    Bot ID: {bot_info.get('id', '?')}\n")
                return True
            else:
                error = data.get('description', 'Unknown error')
                print(f"    Ошибка: {error}\n")
                return False
        else:
            print(f"    HTTP ошибка {response.status_code}\n")
            return False
            
    except requests.exceptions.Timeout:
        print("    Timeout (проверьте интернет)\n")
        return False
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def test_send_message(chat_id):
    """Тест отправки сообщения"""
    print("2⃣  Попытка отправить тестовое сообщение...")
    
    try:
        from src.services.telegram_service import send_telegram_message
        
        message = " Тестовое сообщение от SmenaControl Bot"
        success = send_telegram_message(message)
        
        if success:
            print("    Сообщение отправлено успешно\n")
            return True
        else:
            print("    Ошибка отправки\n")
            return False
            
    except Exception as e:
        print(f"    Ошибка: {e}\n")
        return False

def main():
    print("="*50)
    print(" ПРОВЕРКА TELEGRAM API")
    print("="*50 + "\n")
    
    results = {
        'connection': test_telegram_connection(),
        'message': test_send_message(None)
    }
    
    print("="*50)
    if results['connection']:
        print(" Telegram подключен!")
    else:
        print(" Ошибка подключения к Telegram!")
    
    if results['message']:
        print(" Отправка сообщений работает!")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
```

**Запуск:**
```bash
python test_telegram_api.py
```

---

## 5⃣ Полный тест конфигурации (test_all_config.py)

```python
#!/usr/bin/env python
"""
Полный тест всех параметров конфигурации
Запуск: python test_all_config.py
"""

from src.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_CHAT_ID_TB,
    DB_HOST,
    DB_USER,
    DB_PASS,
    DB_NAME,
    DB_HOST_2,
    DB_NAME_2,
    LOGIN_URL,
    ACTION_URL,
    SD_API_TOKEN,
    ADMIN_ROLES,
    FORBIDDEN_SHIFT_TYPES
)

def check_config():
    """Проверить все параметры конфигурации"""
    print("="*50)
    print("  ПРОВЕРКА КОНФИГУРАЦИИ")
    print("="*50 + "\n")
    
    configs = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "TELEGRAM_CHAT_ID_TB": TELEGRAM_CHAT_ID_TB,
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_NAME": DB_NAME,
        "DB_HOST_2": DB_HOST_2,
        "DB_NAME_2": DB_NAME_2,
    }
    
    optional_configs = {
        "LOGIN_URL": LOGIN_URL,
        "ACTION_URL": ACTION_URL,
        "SD_API_TOKEN": SD_API_TOKEN,
    }
    
    # Обязательные параметры
    print(" ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ:")
    missing = []
    for key, value in configs.items():
        if value:
            print(f"    {key}: {str(value)[:30]}...")
        else:
            print(f"    {key}: НЕ УСТАНОВЛЕН")
            missing.append(key)
    
    # Опциональные параметры
    print("\n ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ:")
    for key, value in optional_configs.items():
        if value:
            print(f"    {key}: {str(value)[:30]}...")
        else:
            print(f"     {key}: не установлен (опционально)")
    
    # Роли и константы
    print("\n РОЛИ И КОНСТАНТЫ:")
    print(f"    ADMIN_ROLES: {ADMIN_ROLES}")
    print(f"    FORBIDDEN_SHIFT_TYPES: {FORBIDDEN_SHIFT_TYPES}")
    
    print("\n" + "="*50)
    if missing:
        print(f" ОТСУТСТВУЮТ: {', '.join(missing)}")
        print("Установите их в файле .env")
    else:
        print(" ВСЕ ПАРАМЕТРЫ УСТАНОВЛЕНЫ")
    print("="*50 + "\n")

if __name__ == "__main__":
    check_config()
```

**Запуск:**
```bash
python test_all_config.py
```

---

##  Как использовать все скрипты сразу

**Создайте файл `run_all_tests.py`:**

```python
#!/usr/bin/env python
"""
Запустить все тесты подряд
Запуск: python run_all_tests.py
"""

import subprocess
import sys

tests = [
    ("verify_setup.py", "Проверка системы"),
    ("test_db_connection.py", "Подключение БД"),
    ("test_db_operations.py", "Операции с БД"),
    ("test_all_config.py", "Конфигурация"),
    ("test_telegram_api.py", "Telegram API"),
]

def run_tests():
    print("\n" + "="*60)
    print(" ЗАПУСК ВСЕХ ТЕСТОВ")
    print("="*60 + "\n")
    
    failed = []
    
    for script, name in tests:
        print(f"\n{'='*60}")
        print(f"  {name}...")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=False
            )
            
            if result.returncode != 0:
                failed.append(name)
                
        except FileNotFoundError:
            print(f" Файл не найден: {script}\n")
            failed.append(name)
        except Exception as e:
            print(f" Ошибка: {e}\n")
            failed.append(name)
    
    # Итоги
    print("\n" + "="*60)
    print(" ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    if failed:
        print(f"\n ТЕСТЫ НЕ ПРОЙДЕНЫ ({len(failed)}):")
        for test in failed:
            print(f"   • {test}")
    else:
        print("\n ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    
    print("="*60 + "\n")
    
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(run_tests())
```

**Запуск всех тестов:**
```bash
python run_all_tests.py
```

---

##  Рекомендуемый порядок запуска

```bash
# 1. Проверка системы
python verify_setup.py

# 2. Проверка БД
python test_db_connection.py

# 3. Операции с БД
python test_db_operations.py

# 4. Конфигурация
python test_all_config.py

# 5. Telegram API
python test_telegram_api.py

# ИЛИ все сразу:
python run_all_tests.py
```

---

*Скрипты актуальны на: 06.05.2026*
*Версия: 1.0*
