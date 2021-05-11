from pyrogram import Client, filters
from time import sleep
from task_processor import TaskWorker, Error
from datetime import datetime


app = Client('Test')
TW = TaskWorker()
TW.load_config_from_yaml('tasks.yaml')

# print(TW.tasks)
prefix = {
    'text': "Текстовая команда пользователя ",
    'call_back': "Реакция на кнопку "
}

# @app.on_message()
# def mess(client, msg):
#     print(msg.text)
    


app.start()
# app.send_message("AV100_bot", '/reg')
# app.request_callback_answer("AV100_bot", callback_data='/message')
# msg = app.get_history("AV100_bot", limit=3)
# # for i in dir(msg[0]):
# #     print(i)

for task in TW.tasks:

    if task.task_type == 'text':
        app.send_message('AV100_bot', task.command)
    elif task.task_type == 'call_back':
        if getattr(task, 'id_msg', False):
            app.request_callback_answer("AV100_bot", task.id_msg, task.command)
        else:
            continue

    command_time = datetime.now().timestamp() - 2 # Поправка на милисекунды
    sleep(task.timeout)
    messages = []
    while True:
        msg = app.get_history("AV100_bot", limit=1, offset=len(messages))[0]
        if command_time >= msg.date or msg.from_user.is_self:
            break
        else:
            messages.append(msg)
    
    if messages:
        for i, m in enumerate(task.messages, 1):
            result = TW.check_task(m, messages)
            if not result['status']:
                
                TW.errors.append(
                    Error(
                        prefix[task.task_type] + task.command,
                        f'Подзадача №{i}',
                        result['alert']
                    )
                )
    else:
        TW.errors.append(
            Error(
                task.command,
                '', 
                'Ответ не пришел за отведенное время'
            )
        )

for er in TW.errors:
    print(er.task)
    print(er.sub_task)
    print(er.alert)
    print()

