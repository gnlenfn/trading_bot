import telegram
import os, sys
from dotenv import load_dotenv

load_dotenv(verbose=True,
            dotenv_path='./.env',
            override=True)

token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('CHAT_ID')
bot = telegram.Bot(token=token)


def send_message(message):
    bot.send_message(chat_id=chat_id, text=message)
