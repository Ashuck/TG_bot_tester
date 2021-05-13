import configparser
from multiprocessing import Process, Pool

import telebot
import Tester


config = configparser.ConfigParser()
config.read("config.ini")
test = Process(target=Tester.do_test)

bot = telebot.TeleBot(config['MainBot']['TOKEN'])

@bot.message_handler(commands=['start_test'])
def process_start_command(message):
    global test
    if not test.is_alive():
        test = Process(target=Tester.do_test)
        test.start()
        bot.reply_to(message, "Тест начался")
    else:
        bot.reply_to(message, "Тестирование еще идет")
        

@bot.message_handler(commands=['test'])
def testing(message):
    bot.reply_to(message, "Проверка еще идет")


if __name__ == '__main__':
    bot.polling()