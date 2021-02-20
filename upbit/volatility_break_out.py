import telegram_bot 
import upbit_basic
import datetime
import pandas as pd
import time

#time.sleep(5) 시간 텀 두기

# 9 13 17 21 01 05 4시간봉 갱신 시간
# 기준 시간 오후 9시 or 오전 1시로 ㄱㄱ
target = "KRW-BORA"

# 24시간 일봉 및 현재 일봉 
def get_24_price():
    past_24_price = upbit_basic.get_trade_price(target, "60", "24")
    columns = ['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price']
    df = pd.json_normalize(past_24_price)[columns]
    return df

def calc_base_price(k):
    # 변동성 계산 
    df = get_24_price()
    high_price = max(df['high_price'])
    low_price  = min(df['low_price'])
    volatility = (high_price - low_price) * k
    base_open_price = upbit_basic.get_trade_price(target)[0]['opening_price'] # 기준시각 시가
    return high_price, low_price, base_open_price, volatility 

high_price, low_price, base_open_price, volatility  = calc_base_price(0.5)

# 시가는 지속적으로 확인하면서 변동성 이상이면 매수
def check_breakout(r): # r: 현금대비 투자비율 
    current_price = upbit_basic.get_trade_price("target")[0]['opening_price']
    cash_balance = float(upbit_basic.get_coin_account("KRW")['balance'])
    order_volume = round(cash_balance * r / current_price, 8)
    if current_price > base_open_price + volatility:
        upbit_basic.order(target, 'bid', order_volume , current_price, 'limit')
    
def end_of_the_day():
    close_price = upbit_basic.get_trade_price(target, "60")[0]['trade_price']
    current_vol = upbit_basic.get_coin_account(target)['balance']
    upbit_basic.order(target, 'ask', current_vol, close_price, 'limit')

