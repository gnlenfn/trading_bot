import telegram_bot 
import upbit_basic
import datetime
import pandas as pd

# 9 13 17 21 01 05 4시간봉 갱신 시간
# 기준 시간 오후 9시 or 오전 1시로 ㄱㄱ
target = "KRW-BORA"
k = 0.5

# 24시간 일봉 및 현재 일봉 
past_24_price = upbit_basic.get_trade_price(target, "60", "24")


columns = ['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price']
df = pd.json_normalize(past_24_price)[columns]

# 변동성 계산 
high_price = max(df['high_price'])
low_price  = min(df['low_price'])
volatility = (high_price - low_price) * k
base_open_price = upbit_basic.get_trade_price(target)[0]['opening_price'] # 기준시각 시가

# 시가는 지속적으로 확인하면서 변동성 이상이면 매수

current_price = upbit_basic.get_trade_price("target")[0]['opening_price']
if current_price > base_open_price + volatility:
    upbit_basic.order(target, bid)
