"""
Модуль для работы с ServiceDesk API
Содержит функции для получения данных о заявках и задачах
"""

import json
import requests
from datetime import datetime, timedelta
from src.config import SD_API_TOKEN, SD_REQUESTS_URL, SD_TASKS_URL, SD_CHANGES_URL, ALLOWED_WORKLOG_OWNERS

# Глобальные переменные для хранения назначенных заявок и задач при начале смены
SHIFT_START_REQUESTS = []  # Список ID заявок, назначенных на техника при начале смены
SHIFT_START_TASKS = []     # Список ID задач, назначенных на техника при начале смены
SHIFT_START_USER = None    # Username пользователя, для которого сохранены списки
SHIFT_START_TIME = None    # Время начала смены


def get_request_ids_and_technicians(status_id, technician_ids):
    """Получает ID заявок и техников по статусу"""
    headers = {"authtoken": SD_API_TOKEN}
    
    input_data = {
        "list_info": {
            "start_index": 1,
            "row_count": 100,
            "search_criteria": [
                {
                    "field": "status",
                    "condition": "is",
                    "value": {"id": status_id}
                }
            ],
            "fields_required": ["id", "subject", "requester", "description", "technician"]
        }
    }
    
    params = {"input_data": json.dumps(input_data)}
    
    try:
        response = requests.get(SD_REQUESTS_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            request_ids = []
            technician_names = []
            
            for item in data.get('requests', []):
                technician = item.get("technician", {})
                if technician and technician.get("id") in technician_ids:
                    request_ids.append(item['id'])
                    technician_names.append(technician.get("name", "Не указан"))
            
            return request_ids, technician_names
        else:
            print(f"[ERROR] get_request_ids_and_technicians: {response.status_code}")
            return [], []
            
    except Exception as e:
        print(f"[ERROR] get_request_ids_and_technicians: {e}")
        return [], []


def get_task_ids_and_technicians(status_id, technician_ids):
    """Получает ID задач и техников по статусу"""
    headers = {"authtoken": SD_API_TOKEN}
    
    input_data = {
        "list_info": {
            "start_index": 1,
            "row_count": 100,
            "search_criteria": [
                {
                    "field": "status",
                    "condition": "is",
                    "value": {"id": status_id}
                }
            ],
            "fields_required": ["id", "title", "description", "owner"]
        }
    }
    
    params = {"input_data": json.dumps(input_data)}
    
    try:
        response = requests.get(SD_TASKS_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            task_ids = []
            owner_names = []
            
            for item in data.get('tasks', []):
                owner = item.get("owner", {})
                if owner and owner.get("id") in technician_ids:
                    task_ids.append(item['id'])
                    owner_names.append(owner.get("name", "Не указан"))
            
            return task_ids, owner_names
        else:
            print(f"[ERROR] get_task_ids_and_technicians: {response.status_code}")
            return [], []
            
    except Exception as e:
        print(f"[ERROR] get_task_ids_and_technicians: {e}")
        return [], []


def get_current_requests_and_tasks():
    """
    Получает актуальные данные о заявках и задачах при каждом вызове
    Возвращает кортеж (allrequests, alltasks)
    """
    from src.database.db_operations import get_technician_ids_from_db
    
    try:
        technician_ids = get_technician_ids_from_db()
        print(f"[DEBUG] Получены Tech ID's: {technician_ids}")

        # Получаем заявки по статусам
        print("[DEBUG] Получение заявок...")
        statuses = ["1", "5", "6", "901", "601"]  # Различные статусы заявок
        all_requests = []
        
        for status in statuses:
            request_ids, _ = get_request_ids_and_technicians(status, technician_ids)
            all_requests.extend(request_ids)

        # Получаем задачи по статусам
        print("[DEBUG] Получение задач...")
        all_tasks = []
        
        for status in statuses:
            task_ids, _ = get_task_ids_and_technicians(status, technician_ids)
            all_tasks.extend(task_ids)

        print(f"[DEBUG] Найдено заявок: {len(all_requests)}, задач: {len(all_tasks)}")
        return all_requests, all_tasks
        
    except Exception as e:
        print(f"[ERROR] get_current_requests_and_tasks: {e}")
        return [], []


def transfer_requests(username, request_ids):
    """Переназначает заявки на указанного техника"""
    from src.database.db_operations import get_sdid_name_from_db
    
    technician_id = get_sdid_name_from_db(username)
    if not technician_id:
        print(f"[ERROR] No technician ID found for username {username}")
        return

    headers = {"authtoken": SD_API_TOKEN}
    
    for request_id in request_ids:
        url = f"{SD_REQUESTS_URL}/{request_id}"
        
        input_data = json.dumps({
            "request": {
                "technician": {"id": technician_id},
                "group": {"id": 3901}
            }
        })
        
        try:
            response = requests.put(url, headers=headers, data={'input_data': input_data}, verify=False)
            
            if response.status_code == 200:
                print(f"Request {request_id} updated successfully.")
            else:
                print(f"Failed to update request {request_id}. Status: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] transfer_requests for {request_id}: {e}")


def transfer_tasks(username, task_ids):
    """Переназначает задачи на указанного техника"""
    from src.database.db_operations import get_sdid_name_from_db
    
    technician_id = get_sdid_name_from_db(username)
    if not technician_id:
        print(f"[ERROR] No owner ID found for username {username}")
        return

    headers = {"authtoken": SD_API_TOKEN}
    
    for task_id in task_ids:
        url = f"{SD_TASKS_URL}/{task_id}"
        
        input_data = json.dumps({
            "task": {
                "owner": {"id": technician_id}
            }
        })
        
        try:
            response = requests.put(url, headers=headers, data={'input_data': input_data}, verify=False)
            
            if response.status_code == 200:
                print(f"Task {task_id} updated successfully.")
            else:
                print(f"Failed to update task {task_id}. Status: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] transfer_tasks for {task_id}: {e}")


def check_upcoming_changes():
    """Проверяет предстоящие плановые работы"""
    headers = {"authtoken": SD_API_TOKEN}
    
    input_data = {
        "list_info": {
            "row_count": 10,
            "start_index": 1,
            "get_total_count": True,
            "sort_fields": [{"field": "id", "order": "desc"}]
        }
    }
    
    params = {'input_data': json.dumps(input_data)}
    
    try:
        response = requests.get(SD_CHANGES_URL, headers=headers, params=params, verify=False)
        
        if not response.ok:
            return "Нет данных о плановых работах."
        
        changes = response.json().get("changes", [])
        now = datetime.now()
        deadline = now + timedelta(hours=24)
        
        lines = []
        for change in changes:
            try:
                # timestamp приходит в миллисекундах
                ts = int(change["scheduled_start_time"]["value"]) / 1000
                start_dt = datetime.fromtimestamp(ts)
                
                # фильтрация по ближайшим 24 часам
                if now <= start_dt <= deadline:
                    start_str = start_dt.strftime("%d.%m.%Y %H:%M")
                    
                    lines.append(
                        f"<b>🛠 Запланированная работа:</b> {change.get('title', 'Undefined')}\n"
                        f"<b>🕒 Время начала:</b> {start_str}\n"
                    )
            except Exception as e:
                print(f"[WARNING] Error processing change: {e}")
                continue
        
        if not lines:
            return "Нет работ в течение следующих 24 часов."
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"[ERROR] check_upcoming_changes: {e}")
        return "Ошибка при получении данных о плановых работах."


def get_worklog_for_request(request_id):
    """Получает информацию о рабочих журналах для заявки"""
    url = f"{SD_REQUESTS_URL}/{request_id}/worklogs"
    headers = {
        "authtoken": SD_API_TOKEN,
        "accept": "application/vnd.manageengine.sdp.v3+json"
    }
    
    input_data = '''{
        "list_info": {
            "row_count": "10",
            "get_total_count": "true",
            "start_index": "1"
        }
    }'''
    
    params = {'input_data': input_data}
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        if response.status_code == 200:
            response_data = response.json()
            
            if 'worklogs' not in response_data:
                return 0, 0, 0
            
            worklogs = response_data['worklogs']
            total_time_spent = 0
            total_worklogs = 0
            resolved_worklogs = 0
            
            for worklog in worklogs:
                try:
                    owner_name = worklog['owner']['name']
                    worklog_type = worklog['type']['name']
                except Exception:
                    owner_name = "undefined"
                    worklog_type = "undefined"
                
                if owner_name in ALLOWED_WORKLOG_OWNERS:
                    hours = int(worklog['time_spent']['hours'])
                    minutes = int(worklog['time_spent']['minutes'])
                    total_time_spent += hours * 3600 + minutes * 60
                    total_worklogs += 1
                    
                    if worklog_type == "Заявка. Решена":
                        resolved_worklogs += 1
            
            return total_time_spent, total_worklogs, resolved_worklogs
            
        elif response.status_code == 404:
            return 0, 0, 0
        else:
            print(f"[ERROR] get_worklog_for_request {request_id}: {response.status_code}")
            return 0, 0, 0
            
    except Exception as e:
        print(f"[ERROR] get_worklog_for_request {request_id}: {e}")
        return 0, 0, 0


def save_shift_start_assignments(username, request_ids, task_ids):
    """Сохраняет список назначенных заявок и задач при начале смены"""
    global SHIFT_START_REQUESTS, SHIFT_START_TASKS, SHIFT_START_USER, SHIFT_START_TIME
    
    # Очищаем предыдущие данные при начале новой смены
    SHIFT_START_REQUESTS = request_ids.copy() if request_ids else []
    SHIFT_START_TASKS = task_ids.copy() if task_ids else []
    SHIFT_START_USER = username
    SHIFT_START_TIME = datetime.now()
    
    print(f"[INFO] Сохранены списки для {username}: заявки {len(SHIFT_START_REQUESTS)} шт., задачи {len(SHIFT_START_TASKS)} шт.")


def get_request_worklogs(request_id):
    """Получает журналы работ для заявки"""
    url = f"https://support.center2m.com/api/v3/requests/{request_id}/worklogs"
    headers = {
        "authtoken": SD_API_TOKEN,
        "accept": "application/vnd.manageengine.sdp.v3+json",
        "PORTALID": "1"
    }
    input_data = ''
    params = {'input_data': input_data}
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] get_request_worklogs {request_id}: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"[ERROR] get_request_worklogs {request_id}: timeout")
        return None
    except Exception as e:
        print(f"[ERROR] get_request_worklogs {request_id}: {e}")
        return None


def get_task_worklogs(task_id):
    """Получает журналы работ для задачи"""
    url = f"https://support.center2m.com/api/v3/tasks/{task_id}/worklogs"
    headers = {
        "authtoken": SD_API_TOKEN,
        "accept": "application/vnd.manageengine.sdp.v3+json",
        "PORTALID": "1"
    }
    input_data = ''
    params = {'input_data': input_data}
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] get_task_worklogs {task_id}: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"[ERROR] get_task_worklogs {task_id}: timeout")
        return None
    except Exception as e:
        print(f"[ERROR] get_task_worklogs {task_id}: {e}")
        return None


def generate_shift_report():
    """Формирует отчет по выполненным работам с предыдущей смены за последние 12 часов"""
    global SHIFT_START_REQUESTS, SHIFT_START_TASKS
    
    if not SHIFT_START_REQUESTS and not SHIFT_START_TASKS:
        return "Нет данных о предыдущей смене."
    
    # Временная граница - 12 часов назад
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    twelve_hours_ago_timestamp = int(twelve_hours_ago.timestamp() * 1000)  # в миллисекундах
    
    report_lines = []
    
    print(f"[DEBUG] Генерация отчета по предыдущей смене: {len(SHIFT_START_REQUESTS)} заявок, {len(SHIFT_START_TASKS)} задач")
    
    # Проверяем заявки (ограничиваем количество)
    for i, request_id in enumerate(SHIFT_START_REQUESTS[:10]):  # Максимум 10 заявок
        try:
            print(f"[DEBUG] Проверка заявки {request_id} ({i+1}/{min(len(SHIFT_START_REQUESTS), 10)})")
            worklogs_data = get_request_worklogs(request_id)
            if worklogs_data and 'worklogs' in worklogs_data and worklogs_data['worklogs']:
                # Есть журналы - проверяем время
                work_types = []
                print(f"[DEBUG] Найдено {len(worklogs_data['worklogs'])} журналов для заявки {request_id}")
                print(f"[DEBUG] Граница времени: {twelve_hours_ago_timestamp} ({twelve_hours_ago.strftime('%d.%m.%Y %H:%M:%S')})")
                
                for j, worklog in enumerate(worklogs_data['worklogs']):
                    try:
                        # Проверяем время создания журнала работ
                        worklog_time_raw = worklog.get('created_time', {}).get('value', '0')
                        worklog_time = int(worklog_time_raw) if worklog_time_raw else 0
                        work_type = worklog.get('type', {}).get('name', 'undefined')
                        
                        if worklog_time:
                            worklog_datetime = datetime.fromtimestamp(worklog_time / 1000)
                            print(f"[DEBUG] Журнал {j+1}: время={worklog_datetime.strftime('%d.%m.%Y %H:%M:%S')}, тип={work_type}")
                            print(f"[DEBUG] Timestamp: {worklog_time} >= {twelve_hours_ago_timestamp}? {worklog_time >= twelve_hours_ago_timestamp}")
                        else:
                            print(f"[DEBUG] Журнал {j+1}: время не указано, тип={work_type}")
                            
                        if worklog_time >= twelve_hours_ago_timestamp:
                            work_types.append(work_type)
                    except Exception as e:
                        print(f"[DEBUG] Ошибка обработки журнала {j+1}: {e}")
                        continue
                
                if work_types:
                    work_summary = ', '.join(set(work_types))  # Убираем дубликаты
                    report_lines.append(f"✅ Заявка {request_id} → {work_summary}")
                else:
                    report_lines.append(f"🔴 Заявка {request_id} → Нет работ за последние 12 часов")
            else:
                # Нет журналов вообще
                report_lines.append(f"❌ Заявка {request_id} → По заявке никакой работы не проводилось")
        except Exception as e:
            print(f"[ERROR] generate_shift_report request {request_id}: {e}")
            report_lines.append(f"⚠️ Заявка {request_id} → undefined")
    
    # Проверяем задачи (ограничиваем количество)
    for i, task_id in enumerate(SHIFT_START_TASKS[:10]):  # Максимум 10 задач
        try:
            print(f"[DEBUG] Проверка задачи {task_id} ({i+1}/{min(len(SHIFT_START_TASKS), 10)})")
            worklogs_data = get_task_worklogs(task_id)
            if worklogs_data and 'worklogs' in worklogs_data and worklogs_data['worklogs']:
                # Есть журналы - проверяем время
                work_types = []
                print(f"[DEBUG] Найдено {len(worklogs_data['worklogs'])} журналов для задачи {task_id}")
                print(f"[DEBUG] Граница времени: {twelve_hours_ago_timestamp} ({twelve_hours_ago.strftime('%d.%m.%Y %H:%M:%S')})")
                
                for j, worklog in enumerate(worklogs_data['worklogs']):
                    try:
                        # Проверяем время создания журнала работ
                        worklog_time_raw = worklog.get('created_time', {}).get('value', '0')
                        worklog_time = int(worklog_time_raw) if worklog_time_raw else 0
                        work_type = worklog.get('type', {}).get('name', 'undefined')
                        
                        if worklog_time:
                            worklog_datetime = datetime.fromtimestamp(worklog_time / 1000)
                            print(f"[DEBUG] Журнал {j+1}: время={worklog_datetime.strftime('%d.%m.%Y %H:%M:%S')}, тип={work_type}")
                            print(f"[DEBUG] Timestamp: {worklog_time} >= {twelve_hours_ago_timestamp}? {worklog_time >= twelve_hours_ago_timestamp}")
                        else:
                            print(f"[DEBUG] Журнал {j+1}: время не указано, тип={work_type}")
                            
                        if worklog_time >= twelve_hours_ago_timestamp:
                            work_types.append(work_type)
                    except Exception as e:
                        print(f"[DEBUG] Ошибка обработки журнала {j+1}: {e}")
                        continue
                
                if work_types:
                    work_summary = ', '.join(set(work_types))  # Убираем дубликаты
                    report_lines.append(f"✅ Задача {task_id} → {work_summary}")
                else:
                    report_lines.append(f"🔴 Задача {task_id} → Нет работ за последние 12 часов")
            else:
                # Нет журналов вообще
                report_lines.append(f"❌ Задача {task_id} → По задаче никакой работы не проводилось")
        except Exception as e:
            print(f"[ERROR] generate_shift_report task {task_id}: {e}")
            report_lines.append(f"⚠️ Задача {task_id} → undefined")
    
    print(f"[DEBUG] Отчет сформирован: {len(report_lines)} строк")
    
    if report_lines:
        if len(SHIFT_START_REQUESTS) > 10 or len(SHIFT_START_TASKS) > 10:
            report_lines.append("(показаны первые 10 элементов)")
        return "\n".join(report_lines)
    else:
        return "Нет выполненных работ по предыдущей смене за последние 12 часов."
