import telegram_bot
import upbit_basic
import time
import datetime
import pandas as pd
import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler

def get_target_price(ticker):
    df = pd.json_normalize(upbit_basic.get_trade_price("KRW-"+ticker, 'days', "5"))
    yesterday = df.loc[1]

    today_open = yesterday['trade_price']
    yesterday_high = yesterday['high_price']
    yesterday_low = yesterday['low_price']
    target = today_open + (yesterday_high - yesterday_low) * 0.5

    now = datetime.datetime.now()
    telegram_bot.send_message(
                f"{now.strftime('%Y-%m-%d %H:%M:%S')} 변동성 돌파 매수\n"+
                f"{ticker}\n"+
                f"오늘 시가: {yesterday['trade_price']} 원\n"+
                f"{target} 원 이상이면 매수\n")
    return target


def check_orderbook(ticker):
    url = "https://api.upbit.com/v1/trades/ticks"
    querystring = {"market": "KRW-"+ticker, "count":"1"}
    response = requests.request("GET", url, params=querystring)

    return response.json()[0]['trade_price']


def buy_volatility_break(ticker, target_price, r):
    now = datetime.datetime.now()
    current_price = check_orderbook(ticker)

    #if float(upbit_basic.get_coin_account("KRW")):
    vol = float(upbit_basic.get_coin_account("KRW")['balance']) * r / current_price
    upbit_basic.order("KRW-"+ticker, 'bid', vol, current_price, 'limit')

    telegram_bot.send_message(
            f"{now.strftime('%Y-%m-%d %H:%M:%S')} 돌파 매수 성공\n"+
            f"매수가: {current_price} 원\n")


def sell_volatility_break(ticker):
    vol = float(upbit_basic.get_coin_account(ticker)['balance'])
    if vol:
        upbit_basic.order("KRW-"+ticker, 'ask', vol, 'market', price=None)
        telegram_bot.send_message(
                f"{now.strftime('%Y-%m-%d %H:%M:%S')} 시장가 매도\n"+
                f"매도 가격: {check_orderbook(ticker)} 원\n"+
                f"매도 수량: {vol}")

def logging():
    now = datetime.datetime.now()
    print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} Bot is on a mission...")


sched = BackgroundScheduler()
sched.add_job(logging, 'interval', minutes=20)
sched.start()

target_price = get_target_price("ADA")
now = datetime.datetime.now()
#mid = datetime.datetime.now()+ datetime.timedelta(minutes=1)
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
"""
기준시각 정해야함 mid -->  hour 변수 넣으면됨

"""
print(now, mid)
print("Bot started to perform strategy...")
while True:
    try:
        now = datetime.datetime.now()
        if mid < now < mid + datetime.timedelta(seconds=10):
            print("mid night!")
            now = datetime.datetime.now()
            mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
            print(f"다음 매도 시간: {mid}")
            sell_volatility_break("ADA")

        current_price = check_orderbook("ADA")
        if current_price > target_price:
            print("buy!")
            buy_volatility_break("ADA", target_price, 0.2)
    except:
        print("ERROR!!")
        telegram_bot.send_message(
                "🚨🚨돌파 매수 실패🚨🚨\n에러발생")

    time.sleep(0.5)