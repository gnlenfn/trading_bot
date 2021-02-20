from dotenv import load_dotenv
import hashlib
import os
import sys
import uuid
from urllib.parse import urlencode

import jwt
import requests
from apscheduler.schedulers.background import BackgroundScheduler


load_dotenv(verbose=True,
            dotenv_path='../.env')


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


def get_trade_price(market, time='1', count='1'):
    url = 'https://api.upbit.com/v1/candles/minutes/' + time
    querystring = {"market": market, "count": count}

    response = requests.request("GET", url, params=querystring)
    # print(response.json()[0])
    return response.json()


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

    res = requests.post(server_url + "/v1/orders",
                        params=query, headers=headers)