from strad_infinite import infinite_bid
from dotenv import load_dotenv
import datetime
import os
import sys
import time
from urllib.parse import urlencode

from apscheduler.schedulers.background import BackgroundScheduler
import strad_infinite
import upbit_basic

#sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import telegram_bot


load_dotenv(verbose=True,
            dotenv_path='../.env')


sched = BackgroundScheduler()
ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')


def logging():
    print(f"{datetime.datetime.now()} Bot is waiting...")

# 비트 가격알림
def BTCprice_alarm():
    data = upbit_basic.get_trade_price("KRW-BTC")
    open_p, low_p, high_p = data['opening_price'], data['low_price'], data['high_price']
    if open_p * 0.99 >= low_p:
        telegram_bot.send_massage(f"🚨🚨 BTC 폭락!! 🚨🚨\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

    elif open_p * 1.01 <= high_p:
        telegram_bot.send_massage(f"🚨🚨 BTC 폭등각? 🚨🚨\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

def target_price():
    data = upbit_basic.get_trade_price("KRW-ETH")
    telegram_bot.send_message("📈이더 가격 알리미\n"+
                            f"{data['trade_price']} 원\n"
                            )
####################################################################

# sched.add_job(strad_infinite.infinite_bid, 'cron', hour='9,21',
#               minute='30', second='3', id="buy_1")
# sched.add_job(logging, 'interval', hours=2)
# sched.add_job(BTCprice_alarm, 'interval', seconds=30)
# sched.add_job(target_price, 'interval', hours=4)

# sched.start()
# telegram_bot.send_message("한무 매수 시작")

# while True:
#     time.sleep(1)

upbit_basic.get_coin_account("ETH")