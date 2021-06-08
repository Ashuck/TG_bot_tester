from pyrogram import Client
from task_processor import TaskWorker
import configparser
import os

path_to_dir = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(path_to_dir + "/config.ini")
task_files = config['MainBot']['Task_files'].split(',')

for f in task_files:
    TW = TaskWorker()
    TW.load_config_from_yaml(f'{path_to_dir}/tasks.d/{f}')
    app = Client(TW.task_name)
    app.start()
    print('Client', TW.task_name, '- OK')
    app.__exit__()