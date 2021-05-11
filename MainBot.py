import configparser
from multiprocessing import Process

import telebot
import Tester


config = configparser.ConfigParser()
config.read("config.ini")

bot = telebot.TeleBot(config['MainBot']['TOKEN'])


@bot.message_handler(commands=['start_test'])
def process_start_command(message):
    Process(target=Tester.do_test).start()
    bot.reply_to(message, "testing end")
    


@bot.message_handler(commands=['test'])
def testing(message):
    bot.reply_to(message, "Проверка еще идет")


if __name__ == '__main__':
    bot.polling()