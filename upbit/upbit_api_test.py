import hashlib
import time
from urllib.parse import urlencode
import jwt
import requests
import uuid
import os
import schedule

#ACCESS_KEY = os.environ['UPBIT_ACCESS_KEY']
#SECRET_KEY = os.environ['UPBIT_SECRET_KEY']
ACCESS_KEY = 'LMnaUA1eX1VsGlk75HkQYsuV2dckQHCJVraW8f9F'
SECRET_KEY = 'qQvV2VJPp3xiy9Xde0D1PBc1kF4Rx6nkIZwZ2nTX'


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
            balance = d['balance']
            break
    
    return d #balance


def getTradePrice(market):
    url = 'https://api.upbit.com/v1/candles/minutes/1'
    querystring = {"market": market, "count": "1"}

    response = requests.request("GET", url, params=querystring)
    #print(response.json())
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
- 매일 같은 시간 기준 (아침 9시)
- 원금 100만원 40분할 기준 1회 25000원 매수
- 25000원 기준 첫 매수 수량을 반복적으로 매수 --> ETH 0.01269036
- 평단 아래이면 매수 / 아니면 pass
- 매일 내 평단 대비 10%에 지정가매도
- 매도 되거나 원금을 모두 소진하면 다시 시작

"""

def main():
    current_avg_price = get_coin_account("ETH")['avg_buy_price']
    current_volume = get_coin_account("ETH")['balance']
    cash_left = get_coin_account("KRW")['balance']
    minute_close_price   = getTradePrice("KRW-ETH")['trade_price']
    
    if cash_left < 25000: # 잔고 없으면 (손절 or 목표도달 못한 익절)
        order(market="KRW-ETH", side='ask', vol=current_volume, price=minute_close_price, types='limit')

    if current_volume < 0.0005: # 리셋 후 재매수 
        order(market="KRW-ETH", side='bid', vol='0.01269036', price=minute_close_price, types='limit')

    elif current_avg_price > minute_close_price: # 평단보다 현재가격이 낮은 가격이면 매수
        order(market="KRW-ETH", side='bid', vol='0.01269036', price=minute_close_price, types='limit')
    
    elif current_avg_price * 1.1 <= minute_close_price: # 평단 * 1.1 보다 현재 가격이 높으면 매도 
        order(market="KRW-ETH", side='ask', vol=current_volume, price=minute_close_price, types='limit') # 익절 작업
        order(market="KRW-ETH", side='bid', vol='0.01269036', price=minute_close_price, types='limit')   # 익절 후 재매수 


####################################################################

schedule.every().day.at("09:01").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)