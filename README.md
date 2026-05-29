ветка для показа третьей практики
Практика 3 — Обмен сменами и административная часть

Цель: реализовать административные процессы, согласования и внешнюю интеграцию.

Включает:
- shift_exchange_handler.py
- admin_handlers.py
- shift_exchange.py
- servicedesk_api.py
- logger.py
- дополнительные роли и права из config.py

Функционал:
- обмен сменами между сотрудниками
- проверки прав lead_engineer / manager
- API-запросы к ServiceDesk
- логирование в shift_exchange_YYYYMMDD.log
- админские команды /addremoteshift, /registertelegramid, /reminderstats

Это самый сложный этап: workflow, external API, админка, продвинутая логика.
