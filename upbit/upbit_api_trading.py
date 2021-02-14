import hashlib
import time
from urllib.parse import urlencode
import jwt
import requests
import uuid
import os
from apscheduler.schedulers.background import BackgroundScheduler
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import telegram_bot
import datetime
from dotenv import load_dotenv

load_dotenv(verbose=True,
            dotenv_path='~/.env')


sched = BackgroundScheduler()
ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')


server_url = 'https://api.upbit.com'
def get_coin_account(target):
    payload = {
    'access_key': ACCESS_KEY,
    'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, SECRET_KEY).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    res = requests.get(server_url + "/v1/accounts", headers=headers)

    for d in res.json():
        if d['currency'] == target:
            return d 
            
    


def getTradePrice(market):
    url = 'https://api.upbit.com/v1/candles/minutes/1'
    querystring = {"market": market, "count": "1"}

    response = requests.request("GET", url, params=querystring)
    print(response.json()[0])
    return response.json()[0]


def order(market, side, vol, price, types):
    query = {
    'market': market,
    'side': side,
    'volume': vol,
    'price': price,
    'ord_type': types,
    }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, SECRET_KEY).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    res = requests.post(server_url + "/v1/orders", params=query, headers=headers)

"""
- 매일 같은 시간 기준 (아침/저녁 9시)
- 원금 100만원 40분할 기준 1회 25000원 매수
- 25000원 기준 첫 매수 수량을 반복적으로 매수 --> ETH 0.01269036
- 평단 아래이면 매수 / 아니면 pass
- 매일 내 평단 대비 10%에 지정가매도
- 매도 되거나 원금을 모두 소진하면 다시 시작

"""

def main():
    target = "ETH"
    print(get_coin_account(target))
    current_avg_price = get_coin_account(target)['avg_buy_price']
    current_volume = get_coin_account(target)['balance']
    cash_left = get_coin_account("KRW")['balance']
    minute_close_price   = getTradePrice("KRW-"+target)['trade_price']
    print("Bot is Working!")
    if cash_left < '25000': # 잔고 없으면 (손절 or 목표도달 못한 익절)
        print(f"{datetime.datetime.now()} Sell all left")
        telegram_bot.send_message(
f"전체매도 \n\
매도 수량: {current_volume} ETH 개\n \
매도 평단: {get_coin_account('ETH')['avg_buy_price']}\n\
현금 잔고: {get_coin_account('KRW')['balance']} 원")
        order(market="KRW-"+target, side='ask', vol=current_volume, price=minute_close_price, types='limit')

    if current_volume < '0.0005': # 리셋 후 재매수 
        print(f"{datetime.datetime.now()} Restart Process..")
        order(market="KRW-"+target, side='bid', vol='0.01269036', price=minute_close_price, types='limit')
        telegram_bot.send_message(
f"매수 재시작 \n\
매수 수량: 0.01269036 ETH\n\
현재 수량: {current_volume} ETH 개\n \
현재 평단: {get_coin_account('ETH')['avg_buy_price']}\n\
현금 잔고: {float(get_coin_account('KRW')['balance']):.2f} 원")

    elif float(current_avg_price) > minute_close_price: # 평단보다 현재가격이 낮은 가격이면 매수
        print(f"{datetime.datetime.now()} Buy more ETH")
        order(market="KRW-"+target, side='bid', vol='0.01269036', price=minute_close_price, types='limit')
        telegram_bot.send_message(
f"추가 매수 \n\
매수 수량: 0.01269036 ETH\n\
현재 수량: {current_volume} ETH 개\n\
현재 평단: {get_coin_account('ETH')['avg_buy_price']}\n\
현금 잔고: {float(get_coin_account('KRW')['balance']):.2f} 원")

    elif float(current_avg_price) * 1.1 <= float(minute_close_price): # 평단 * 1.1 보다 현재 가격이 높으면 매도 
        print(f"{datetime.datetime.now()} Sold all ETH with benefit")
        telegram_bot.send_message(
f"상승으로 익절 \n\
매도 수량: {current_volume} ETH 개\n\
매도 평단: {get_coin_account('ETH')['avg_buy_price']}\n\
현금 잔고: {float(get_coin_account('KRW')['balance']):.2f} 원")
        order(market="KRW-"+target, side='ask', vol=current_volume, price=minute_close_price, types='limit') # 익절 작업
        order(market="KRW-"+target, side='bid', vol='0.01269036', price=minute_close_price, types='limit')   # 익절 후 재매수 
    else:
        print(f"{datetime.datetime.now()} Buy more ETH")
        order(market="KRW-"+target, side='bid', vol='0.01269036', price=minute_close_price, types='limit')
        telegram_bot.send_message(
f"추가 매수 \n\
매수 수량: 0.01269036 ETH\n\
현재 수량: {current_volume} ETH 개\n \
현재 평단: {get_coin_account('ETH')['avg_buy_price']}\n\
현금 잔고: {float(get_coin_account('KRW')['balance']):.2f} 원")

def logging():
    print(f"{datetime.datetime.now()} Bot is waiting...")

####################################################################

sched.add_job(main, 'cron', hour='9,21', minute='3', second='30', id="buy_1")
sched.add_job(logging, 'interval', hours=2)

sched.start()
telegram_bot.send_message("한무 매수 시작")

while True:
    time.sleep(1)

