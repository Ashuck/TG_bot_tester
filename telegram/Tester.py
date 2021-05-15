import sqlite3
import telebot
import configparser
from time import sleep
from task_processor import TaskWorker, Error
from datetime import datetime

from pyrogram import Client


def send_message(chat_id, path, count):
    config = configparser.ConfigParser()
    config.read(path + "/config.ini")
    bot = telebot.TeleBot(config['MainBot']['TOKEN'])
    bot.send_message(chat_id, f'Тест окончен. Обнаружено ошибок - {count}')



def do_test(path, chat_id, path_db, num):
    app = Client('Test')
    app.start()
    TW = TaskWorker()
    TW.load_config_from_yaml(path + '/tasks.yaml')
    

    for task in TW.tasks:
        delta = 0
        if task.task_type == 'text':
            app.send_message('AV100_bot', task.command)
        elif task.task_type == 'call_back':
            if getattr(task, 'id_msg', False):
                app.request_callback_answer("AV100_bot", task.id_msg, task.command)
            else:
                TW.errors.append(
                    task.description,
                    f'',
                    "Не было найдено сообщение с данной кнопкой"
                )
        elif task.task_type == 'image':
            app.send_photo('AV100_bot', path + task.command)
            last_task = task.timeout
        elif task.task_type == 'result':
            delta = last_task
        else:
            continue

        command_time = datetime.now().timestamp() - 2 # Поправка на милисекунды
        command_time -=  delta # Костыль для проверки ответа на картинку

        sleep(task.timeout)
        messages = []
        while True:
            msg = app.get_history("AV100_bot", limit=1, offset=len(messages))[0]
            if command_time >= msg.date or msg.from_user.is_self:
                break
            else:
                messages.append(msg)
        
        if messages:
            for i, sub_tusk in enumerate(task.messages, 1):
                result = TW.check_task(sub_tusk, messages)
                if not result['status']:
                    
                    TW.errors.append(
                        Error(
                            task.description,
                            f'Подзадача №{i}',
                            result['alert']
                        )
                    )
        else:
            TW.errors.append(
                Error(
                    task.description,
                    '', 
                    'Ответ не пришел за отведенное время'
                )
            )

    for _ in range(3):
        try:
            send_message(chat_id, path, len(TW.errors))
            break
        except:
            sleep(1)
            

    conn = sqlite3.connect(path_db) 
    cursor = conn.cursor()

    for er in TW.errors:
        cursor.execute(f"""INSERT INTO errors VALUES ('{er.task}', '{er.sub_task}\n{er.alert}', {num})""")
    conn.commit()
    conn.close()

