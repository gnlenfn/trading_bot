import telegram

bot = telegram.Bot(token='')


def send_message(message):
    bot.sendMessage(chat_id="", text=message)

