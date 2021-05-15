from pyrogram import Client, filters
from time import sleep


app = Client('Test')
app.start()
# app.send_message('AV100_bot', '/help')
sleep(3)
msg = app.get_history("AV100_bot", limit=1, offset=1)

for m in msg:
    print(m)
