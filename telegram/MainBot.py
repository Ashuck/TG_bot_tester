import configparser
import telebot
import os
import yaml
import csv
import io
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
acc_list = list(int(i) for i in config['acc_list'])


# Клавиатура
def get_standart_keyboard():
    mm = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btns = [
        ('Начать тест', 'Результаты'),
        ('Список тестов', 'Статистика'),
        ('Обновить клавиатуру',)
    ]
    for text in btns:
        mm.add(
            *[types.KeyboardButton(t) for t in text]
        )
    
    return mm
    

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message, "Воспользуйтесь клавиатурой", 
        reply_markup=get_standart_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == 'Начать тест' and msg.chat.id in acc_list)
def start_test(msg):
    global test_proc
    if not test_proc.is_alive():
        conn = sqlite3.connect(path_to_db) 
        cursor = conn.cursor()
        cursor.execute(f"""INSERT INTO tests (who) VALUES ('{msg.chat.id}')""")
        conn.commit()
        cursor.execute("""SELECT * FROM tests ORDER BY id DESC LIMIT 1""")
        num = cursor.fetchone()[0]
        conn.close()
        args = (
            path_to_dir,
            msg.chat.id,
            path_to_db,
            num
        )
        test_proc = Process(target=do_test, args=args)
        test_proc.start()
        bot.send_message(msg.chat.id, f"Тест №{num} начался")
    else:
        bot.send_message(msg.chat.id, "Тестирование еще идет")


@bot.message_handler(func=lambda msg: msg.text == 'Результаты' and (msg.chat.id in acc_list))
def get_results(msg):
    conn = sqlite3.connect(path_to_db) 
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM tests ORDER BY id DESC LIMIT 1""")
    test = cursor.fetchone()

    if not test_proc.is_alive():
        if test:
            cursor.execute(f"""SELECT task, alert FROM errors WHERE test = {test[0]}""")
            text = ''
            for i in cursor.fetchall():
                text += '\n' + i[0] + '\n' + i[1]
            if not text:
                text = f'В тесте №{test[0]} ошибки не обнаружены'
            else:
                text = f"Результаты теста №{test[0]}:\n" + text
        else:
            text = 'В базе нет тестов'
        conn.close()
    else:
        text = f'Тест №{test[0]} еще не закончен'
    bot.send_message(msg.chat.id, text)
        

@bot.message_handler(func=lambda msg: msg.text == 'Список тестов' and msg.chat.id in acc_list)
def get_tests(msg):
    with open(path_to_dir + '/tasks.yaml') as f:
        data = yaml.load(f)
    answer = ''
    for task in data['Tasks']:
        answer += '  - ' + task['description'] + '\n'
    bot.send_message(msg.chat.id, answer)


@bot.message_handler(func=lambda msg: msg.text == 'Статистика' and msg.chat.id in acc_list)
def get_stats(msg):
    conn = sqlite3.connect(path_to_db) 
    cursor = conn.cursor()
    cursor.execute("""SELECT result, COUNT(*) FROM paths GROUP BY result;""")
    count = 0
    text = ""
    for i in cursor.fetchall():
        count += i[1]
        if i[0] == "":
            text += f"Успешно обработано - {i[1]}\n"
        elif i[0] == "4":
            text += f"Не удалось распознать - {i[1]}\n"   
        else:
            text += f"Другие ошибки - {i[1]}\n"
    with open(path_to_dir + '/statistic.csv', "w") as out_file:
        cursor.execute("""SELECT * FROM paths WHERE result != '';""")
        writer = csv.writer(out_file, delimiter=';')
        stats = cursor.fetchall()
        writer.writerows(stats)
        text = f"Всего обработано - {count}\n" + text
        conn.close()
        bot.send_message(msg.chat.id, text)
    if stats:
        with open(path_to_dir + '/statistic.csv', "rb") as file:
            bot.send_document(msg.chat.id, file)
        


@bot.message_handler(func=lambda msg: msg.text == 'Обновить клавиатуру' and msg.chat.id in acc_list)
def refresh_kbr(msg):
    bot.reply_to(
        msg, "Клавиатура обновлена", 
        reply_markup=get_standart_keyboard()
    )


if __name__ == '__main__':
    test_proc = Process(target=do_test)

    bot.polling(none_stop=True)



    