import telegram
import os, sys
from dotenv import load_dotenv
import requests
from logging import Handler, Formatter
import logging
import datetime

load_dotenv(verbose=True,
            dotenv_path='../.env',
            override=True)

token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('CHAT_ID')
bot = telegram.Bot(token=token)


def send_message(message):
    bot.send_message(chat_id=chat_id, text=message)

class RequestsHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        payload = {
			'chat_id': chat_id,
			'text': log_entry,
			'parse_mode': 'HTML'
		}
        return requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=token),
							data=payload).content


class LogstashFormatter(Formatter):
	def __init__(self):
		super(LogstashFormatter, self).__init__()

	def format(self, record):
		t = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

		return "<i>{datetime}</i><pre>\n{message}</pre>".format(message=record.msg, datetime=t)


