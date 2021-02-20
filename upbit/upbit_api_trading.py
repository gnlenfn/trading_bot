import datetime
import os
import time
import argparse

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

import strad_infinite
import telegram_bot
import upbit_basic

load_dotenv(verbose=True,
            dotenv_path='../.env')

ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')


def logging():
    print(f"{datetime.datetime.now()} Bot is waiting...")

# 비트 가격알림
def BTCprice_alarm():
    data = upbit_basic.get_trade_price("KRW-BTC")[0]
    open_p, low_p, high_p = data['opening_price'], data['low_price'], data['high_price']
    if open_p * 0.99 >= low_p:
        telegram_bot.send_massage(f"🚨🚨 BTC 폭락!! 🚨🚨\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

    elif open_p * 1.01 <= high_p:
        telegram_bot.send_massage(f"🚨🚨 BTC 폭등각? 🚨🚨\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

def target_price(target):
    print(f"Seaching {target} price...")
    data = upbit_basic.get_trade_price("KRW-"+target)[0]
    telegram_bot.send_message(f"📈{target} 가격 알리미\n"+
                            f"{data['trade_price']} 원\n"
                            )
####################################################################
    
def main():
    parser = argparse.ArgumentParser(description="tutorial")
    parser.add_argument('--target-coin', type=str, help='a coin to buy')
    parser.add_argument('--profit', type=int, help='profit ratio for benefit')
    args = parser.parse_args()

    ############### schedules ###############
    sched = BackgroundScheduler()
    sched.add_job(logging, 'interval', hours=2)
    sched.add_job(lambda: strad_infinite.infinite_bid(args.target_coin, args.profit), 
                'cron', hour='1,13', second='3', id="buy_1")
    #sched.add_job(BTCprice_alarm, 'interval', seconds=30)
    sched.add_job(lambda: target_price(args.target_coin), 'cron', hour='1, 9, 13, 17, 21')
    ##########################################

    sched.start()
    telegram_bot.send_message(f"{args.target_coin} 한무 매수 시작")
    print(f"Bot Starts to trading {args.target_coin}")
    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    main()

