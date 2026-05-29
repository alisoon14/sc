#  Диаграммы взаимодействия компонентов SmenaControl Bot

## Диаграмма 1: Общая архитектура системы

```

                      TELEGRAM USERS                              
              (Сотрудники техподдержки и администраторы)        

                               Отправляют сообщения
                               Нажимают кнопки
                              
                   
                     TELEGRAM BOT API    
                     (polling или webhook)
                   
                              
                              
                   
                       MAIN.PY           
                    - ApplicationBuilder 
                    - Handlers registry  
                    - Error handling     
                   
                              
        
                                                  
                                                  
                
     MIDDLEWARE          HANDLERS          SERVICES 
     (auth)                                         
                
                                                 
                
                                               
                                               
    
              DATABASE LAYER (db_operations)             
      - get_user_data()                                  
      - set_onshift()                                    
      - get_pending_reminders()                          
      - save_shift_note()                                
      - и другие DB операции                             
    
                                                   
                                                   
                      
     MySQL DB              MySQL 2        Telegram  
      #1                  ServiceDesk      API       
     (work_                                         
    schedule)                                       
                      
```

---

## Диаграмма 2: Поток обработки сообщения

```
Пользователь отправляет сообщение
            
            
  
   TELEGRAM BOT API получает   
   (polling проверяет каждые N
    миллисекунд)              
  
                 
                 
  
   Определяется тип сообщения: 
   - /command                  
   - Callback query (кнопка)   
   - Text message              
  
                 
        
                                                 
                                                 
          
  COMMAND        CALLBACK    TEXT         ERROR   
  HANDLER        QUERY       MESSAGE      HANDLER 
          
                                                 
       
                        
                        
  
   MIDDLEWARE: with_auth decorator    
   Проверяет авторизацию              
   1. check_user_access()             
   2. Если ошибка - отправить ответ  
   3. Если OK - продолжить            
  
                Авторизован 
               
  
   ОБРАБОТЧИК ВЫПОЛНЯЕТСЯ             
   - Получает данные от пользователя  
   - Вызывает функции из services     
   - Обновляет БД                     
   - Отправляет ответ пользователю    
  
               
               
  
   Отправляется ответ пользователю    
   - Текстовое сообщение              
   - Клавиатура (если есть)           
   - Уведомление в групповой чат      
  
```

---

## Диаграмма 3: Процесс "Заступить на смену"

```

 Пользователь нажимает кнопку        
 " Заступить на смену"              

                   
                   

 callback_handlers.py                
 handle_callback_query()             
 Проверяет: data == "start_shift"   

                   
                   

 shift_operations.py                 
 start_shift(tguser)                 

                   
        
                             
                             
    
   БД операции:      ServiceDesk API: 
                                      
   1. get_user_      1. perform_login 
      data()            _and_action() 
                                      
   2. set_onshift    2. transfer_     
                        requests()    
   3. update_                         
      start_shift    3. transfer_     
      _time()           tasks()       
                                      
    
                             
        
                       
                       
  
   Отправляются уведомления:              
                                          
   1. Личное сообщение пользователю       
       Смена началась!                   
       Кол-во заявок: X                 
                                          
   2. Сообщение в групповой чат           
      @username начал смену               
      Все заявки переведены на него       
                                          
   3. Уведомление в ServiceDesk чат       
      (опционально)                       
  
```

---

## Диаграмма 4: Процесс "Обмен смен"

```
Пользователь A инициирует обмен (выбирает Пользователя B и дату)
                                
                                
                    
                     shift_exchange_handler  
                     handle_shift_exchange   
                     _conversation()         
                    
                                 
                                 
                    
                     ВАЛИДАЦИЯ:              
                     - Смена существует?    
                     - Тип смены разрешен?  
                     - Пользователь B есть? 
                    
                                 
                    
                     Валидация НЕ пройдена    Валидация пройдена
                                            
                 
             Отправить ошибку      Сохранить в БД:      
             пользователю          - user_from: A       
                  - user_to: B         
                                     - status: 'pending'  
                                     - reason: ...        
                                    
                                               
                                               
                        
                         Отправить уведомление Lead       
                         Engineer (@wezersovvv):          
                                                          
                          Обмен смены:                   
                          Пользователь A                
                          Пользователь B                
                          Дата смены                    
                          Причина: ...                  
                                                          
                         [Одобрить] [Отклонить]          
                        
                                   
                    
                                                
            Lead отклонил      Lead одобрил
                                                
                                                
          
         В БД: status =         Отправить           
         'rejected'             уведомление Manager 
                                (@Electrowind):     
         Уведомление                                
         обоим пользователям     Согласовать      
                                обмен смины?        
          Обмен отклонен                          
           [Одобрить]         
                                   [Отклонить]        
                                  
                                             
                          
                                                          
                      Manager      Manager
                    отклонил       одобрил
                                                          
                                                          
                            
                   status =                   status =         
                   'rejected'                 'approved'       
                                                               
                   Уведомления                 Обмен успешен 
                   обоим                                       
                                              Смены обновлены  
                    Обмен                   в системе        
                   отклонен                                    
                             Уведомления      
                                                обоим            
                                               
```

---

## Диаграмма 5: Процесс "Удаленная работа"

```
Пользователь выбирает " Работать удаленно"
                                
                                
                    
                     remote_work_handler.py 
                     Выбор дата смены       
                     Ввод причины           
                    
                                 
                                 
                    
                     ПРОВЕРКА ЛИМИТА:       
                     get_user_available_    
                     remote_limit()         
                                            
                     Лимит: N дней в месяц  
                    
                                 
                
                                                 
            Лимит есть            Лимит исчерпан
                                                 
                                                 
                  
         Сохранить в БД            ТРЕБУЕТСЯ СОГЛАСОВАНИЕ 
                                                          
         status =                  Проверить:            
         'approved'                - пользователь в      
                                    REMOTE_NO_APPROVAL_ 
         (автоматически)              USERS?              
                                          
                                   
                                            
                          
                                                    
             Да-ут                                    
                             
                         Да      Нет         Нет, требу- 
                              ется согласо-
                                               вание        
                                              
                                      
                        Автоматич одобр                
                        (пропустить          
                         согласование)        Сохранить в БД   
                                              
                                               status = 'pend-  
                                               ing'             
                                                                
                                               approved_by_lead 
                  = 0              
                                                                 
                                                approved_by_man  
                           ager = 0         
                      Передать на              
                      ServiceDesk                        
                                                         
                      servicedesk_api.py     
                      transfer_requests()     Отправить        
                                              Lead Engineer    
                                          
                                               (callback handler)
                                              
                                                     
                                     
                                                               
                                 Lead                      Lead
                               отклонил                   одобрил
                                                               
                                                               
                                       
                                Сообщить          Отправить       
                                пользов-          Manager         
                               ателю об                          
                                отказе            (callback       
                                                  handler)        
                                       
                                                         
                                         
                                                                   
                                     Manager              Manager
                                   отклонил             одобрил
                                                                   
                                                                   
                                       
                                  Сообщить об        Передать на      
                                  отказе             ServiceDesk      
                                                                      
                                        transfer_        
                                                       requests()       
                                                                        
                                                      
                                                               
                              
                                                
                                                
                                    
                                     ФИНАЛЬНОЕ            
                                     УВЕДОМЛЕНИЕ          
                                     ПОЛЬЗОВАТЕЛЮ:        
                                                          
                                      или             
                                     + статус             
                                     + причина (если нужно)
                                    
```

---

## Диаграмма 6: Сервис напоминаний (фоновая задача)

```
ИНИЦИАЛИЗАЦИЯ:
       
       
   
    main.py -> app.post_init() 
                               
    asyncio.create_task(       
      reminder_checker()       
    )                          
   
                
                
   
    БЕСКОНЕЧНЫЙ ЦИКЛ:          
    reminder_checker()         
                               
    while True:                
      pending = get_pending    
                _reminders()   
      for r in pending:        
        process_reminder(r)    
      await sleep(30)          
                               
     Проверяет каждые 30 сек 
   
                
    
                           
                           
        
 Найдены           Напоминаний  
 напомина          не найдено   
 ния                            
        
                          
                          
    
 Для каждого         Ждем 30 сек 
 напоминания                     
 вызвать             Проверяем   
 process_            снова       
 reminder(r)        

         
         
   
    process_reminder():  
                         
    1. Сформировать     
       сообщение:       
       - Время          
       - Кто создал     
       - Текст          
                         
    2. Отправить в чат  
       send_reminder_   
       to_chat()        
                         
    3. Если успешно:    
       - mark_reminder_ 
         sent(id)       
       - Логировать     
       - is_sent = 1    
                         
    4. Если ошибка:     
       - Логировать     
       - Повторить      
         позже          
   
```

---

## Диаграмма 7: Таблица взаимодействий компонентов

```

 КОМПОНЕНТ         ВЗАИМОДЕЙСТВУЕТ С                                

 main.py            Все handlers                                   
                    ApplicationBuilder (Telegram API)               
                    reminder_service (фоновые задачи)              

 config.py          db_operations (DB параметры)                   
                    auth_middleware (roles, permissions)           
                    telegram_service (tokens, chat IDs)            
                    servicedesk_api (API параметры)                

 auth_middleware    db_operations (check_user_access)              
                    logger (логирование)                           

 command_handlers   db_operations (get_user_data)                  
                    telegram_service (отправка сообщений)          
                    keyboards (создание меню)                      
                    shift_operations (start_shift)                 
                    servicedesk_api (transfer_requests)            

 shift_exchange     db_operations (сохранение/получение)           
 _handler           telegram_service (уведомления)                 
                    logger (логирование)                           

 remote_work        db_operations (check limits)                   
 _handler           telegram_service (notifications)               
                    servicedesk_api (transfer requests)            
                    config (roles, approval users)                 

 reminder_handler   db_operations (save_reminder)                  
                    telegram_service (отправка)                    
                    keyboards (выбор даты/времени)                

 admin_handlers     db_operations (управление данными)             
                    reminder_service (restart)                     
                    telegram_service (test notifications)          
                    statistics (get stats)                         

 db_operations      MySQL DB (все операции)                        
                    shift_exchange (обмены смин)                   

 shift_exchange     MySQL DB (напрямую)                            
                    db_operations (helper функции)                 

 telegram_service   Telegram Bot API (HTTP requests)               
                    config (API tokens, chat IDs)                  

 servicedesk_api    ServiceDesk API (HTTP requests)                
                    config (API token, base URL)                   
                    db_operations (SD IDs)                         

 reminder_service   db_operations (get_pending_reminders)          
                    telegram_service (send_reminder)               
                    logger (логирование)                           

 statistics         db_operations (получить данные)                
                    servicedesk_api (получить метрики)            

 keyboards          Нет зависимостей (pure functions)             

 logger             Файловая система (логи)                        
                    datetime (временные метки)                     

 helpers            Нет зависимостей (pure functions)             

```

---

## Диаграмма 8: Матрица ролей и прав доступа

```

 Действие             User      Lead Eng.   Manager      

 Заступить на смену                                
 Обменять смену                                    
 Работать удаленно                                 
 Создать напоминание                               
 Смотреть статистику                               

 Согласовать обмен                                 
 Согласовать удалено                               
 Добавить удаленку                                 

 Проверить Tg IDs                                  
 Регистрировать ID                                 
 Статистика ремайнд                                
 Перезапуск ремайнд                                
 Тестирование                                      

```

---

## Диаграмма 9: Структура базы данных (ERD упрощенная)

```

      EMPLOYEES             

 id (PK)                    
 name                       
 tguser                     
 telegram_id                
 username (ПК username)     
 TechnitianIdSd             
 onshift                    
 grade                      
 web_role                   

               1:N relationship
             
    
                                                    
                                                    
       
 REMINDERS       REMOTE WORK   SHIFT EXC   ACTUAL SHIFT 
                 REQUESTS      HANGES      TIMES        
       
 id (PK)          id (PK)       id (PK)     id (PK)     
 tguser (FK)      tguser(FK)    user_from   tguser(FK)  
 reminder_text    shift_date    user_to     user_name   
 reminder_time    reason        status      actual_start
 is_sent          status        approved    shift_date  
 created_time     created_at    by_lead     created_at  
                  approved   
                    approved_     by_mng   
                    by_lead       created_ 
                    approved_     at       
                    by_manager   
                    created_at 
                   
```

---

*Диаграммы созданы: 06.05.2026*
