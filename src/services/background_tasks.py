"""
Фоновые задачи для бота
Содержит периодические задачи, такие как проверка напоминаний
"""

import asyncio
from src.database.db_operations import get_pending_reminders, mark_reminder_sent, get_telegram_id_by_tguser
from src.config import TELEGRAM_BOT_TOKEN
from telegram import Bot


async def reminder_checker():
    """Периодическая проверка и отправка напоминаний"""
    while True:
        try:
            reminders = get_pending_reminders()
            
            for r in reminders:
                message = f"""<b>🔔 Напоминание</b>

<b>Дата/Время:</b> {r['reminder_time'].strftime('%d.%m.%Y %H:%M')}
<b>Создано:</b> {r['name']}

{r['reminder_text']}"""
                
                # Получаем Telegram ID пользователя
                user_id = get_telegram_id_by_tguser(r['tguser'])
                
                if user_id:
                    try:
                        # Отправляем напоминание в личку пользователю
                        bot = Bot(token=TELEGRAM_BOT_TOKEN)
                        await bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        
                        # Помечаем как отправленное
                        mark_reminder_sent(r['id'])
                        print(f"[INFO] Reminder {r['id']} sent successfully to user {r['tguser']} (ID: {user_id})")
                    except Exception as e:
                        print(f"[ERROR] Failed to send reminder {r['id']} to user {r['tguser']}: {e}")
                else:
                    print(f"[ERROR] Telegram ID not found for user {r['tguser']}, reminder {r['id']}")
                    
        except Exception as e:
            print(f"[ERROR] Reminder checker failed: {e}")

        # Ждем 30 секунд перед следующей проверкой
        await asyncio.sleep(30)
