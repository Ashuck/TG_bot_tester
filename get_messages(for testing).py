from pyrogram import Client, filters


app = Client('Test')
app.start()
msg = app.get_history("AV100_bot", limit=1)

for m in msg:
    print(m.reply_markup)
    'https://av100.ru/pay?chatid=458850721&tariff=planform3501&userid=1457195'