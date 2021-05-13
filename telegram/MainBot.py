import configparser
import telebot
import os
import yaml
import sqlite3
from telebot import types
from multiprocessing import Process

from Tester import do_test

path_to_dir = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(path_to_dir + "/config.ini")
bot = telebot.TeleBot(config['MainBot']['TOKEN'])
path_to_db = path_to_dir.replace('telegram', 'video') + '/paths.db'
conn = sqlite3.connect(path_to_db) 
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS errors (task text, alert text, test int)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS tests (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, who text)""")
conn.commit()
conn.close()


# Клавиатура
def get_standart_keyboard():
    mm = types.ReplyKeyboardMarkup(row_width=1)
    btns = [
        'Начать тест',
        'Результаты',
        'Список тестов',
        'Статистика (не работает)',
        'Обновить клавиатуру'
    ]
    for text in btns:
        b = types.KeyboardButton(text)
        mm.add(b)
    
    return mm
    

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message, "Воспользуйтесь клавиатурой", 
        reply_markup=get_standart_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == 'Начать тест')
def start_test(msg):
    global test
    if not test.is_alive():
        conn = sqlite3.connect(path_to_db) 
        cursor = conn.cursor()
        cursor.execute(f"""INSERT INTO tests (who) VALUES ('{msg.chat.id}')""")
        conn.commit()
        cursor.execute("""SELECT * FROM tests ORDER BY id DESC LIMIT 1""")
        num = cursor.fetchone()[0]
        conn.close()
        args = (
            path_to_dir,
            bot,
            msg.chat.id,
            path_to_db,
            num
        )
        test = Process(target=do_test, args=args)
        test.start()
        bot.send_message(msg.chat.id, f"Тест №{num} начался")
    else:
        bot.send_message(msg.chat.id, "Тестирование еще идет")


@bot.message_handler(func=lambda msg: msg.text == 'Результаты')
def get_results(msg):
    conn = sqlite3.connect(path_to_db) 
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM tests ORDER BY id DESC LIMIT 1""")
    test = cursor.fetchone()
    if test:
        cursor.execute(f"""SELECT task, alert FROM errors WHERE test = {test[0]}""")
        text = ''
        for i in cursor.fetchall():
            text += i[0] + '\n' + i[1]
        if not text:
            text = f'В тесте №{test[0]} ошибки не обнаружены'
    else:
        text = 'В базе нет тестов'
    conn.close()
    bot.send_message(msg.chat.id, text)
        

@bot.message_handler(func=lambda msg: msg.text == 'Список тестов')
def get_tests(msg):
    with open(path_to_dir + '/tasks.yaml') as f:
        data = yaml.load(f)
    answer = ''
    for task in data['Tasks']:
        answer += task['command'] + '\n'
    bot.send_message(msg.chat.id, answer)


@bot.message_handler(func=lambda msg: msg.text == 'Обновить клавиатуру')
def refresh_kbr(msg):
    bot.reply_to(
        msg, "Клавиатура обновлена", 
        reply_markup=get_standart_keyboard()
    )


if __name__ == '__main__':
    test = Process(target=do_test)
    bot.polling()