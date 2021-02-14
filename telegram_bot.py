import telegram
import os

token = os.getenv('TELEGRAM_TOKEN')
chad_id = os.getenv('CHAT_ID')

bot = telegram.Bot(token=token)


def send_message(message):
    bot.sendMessage(chat_id=chad_id, text=message)

