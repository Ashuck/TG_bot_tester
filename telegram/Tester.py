import sqlite3
import telebot
import configparser
from time import sleep
from task_processor import TaskWorker, Error, Result
from datetime import datetime

from pyrogram import Client


def send_message(chat_id, path):
    config = configparser.ConfigParser()
    config.read(path + "/config.ini")
    bot = telebot.TeleBot(config['MainBot']['TOKEN'])
    bot.send_message(chat_id, f'Тест окончен.')



def do_test(path, chat_id, path_db, num, task_files):
    for task_file in task_files:
        TW = TaskWorker()
        TW.load_config_from_yaml(f'{path}/tasks.d/{task_file}')
        app = Client(TW.task_name)
        app.start()

        for task in TW.tasks:
            print(TW.tasks)
            delta = 0
            if task.task_type == 'text':
                app.send_message('AV100_bot', task.command)
            elif task.task_type == 'call_back':
                if getattr(task, 'id_msg', False):
                    app.request_callback_answer("AV100_bot", task.id_msg, task.command)
                else:
                    TW.errors.append(
                        Error(
                            task.description,
                            f'',
                            "Не было найдено сообщение с данной кнопкой",
                            TW.description
                        )
                    )
                    continue
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
                result_flag = False
                for i, sub_tusk in enumerate(task.messages, 1):
                    try:
                        result = TW.check_task(sub_tusk, messages)
                    except Exception as ex:
                        # print(ex)
                        result = {'status': False, 'alert': 'Упал с ошибкой'}
                    if not result['status']:
                        result_flag = True
                        TW.errors.append(
                            Error(
                                task.description,
                                f'Подзадача №{i}',
                                result['alert'],
                                TW.description
                            )
                        )
                

            else:
                result = {'status': False, 'alert': 'Ответ не пришел за отведенное время'}
                TW.errors.append(
                    Error(
                        task.description,
                        '', 
                        result['alert'],
                        TW.description
                    )
                )
            TW.results.append(
                Result(
                    task.description,
                    "Провал" if result_flag else "Успех",
                    TW.description
                )
            )
        app.__exit__()
        conn = sqlite3.connect(path_db) 
        cursor = conn.cursor()

        for er in TW.errors:
            cursor.execute(f"""INSERT INTO errors VALUES ('{er.task}', '{er.sub_task}\n{er.alert}', {num}, '{er.description}')""")
        for res in TW.results:
            cursor.execute(f"""INSERT INTO results VALUES ('{res.task}', '{res.result}', {num}, '{res.description}')""")

        conn.commit()
        conn.close()


    for _ in range(3):
        try:
            send_message(chat_id, path)
            break
        except:
            sleep(1)
            


