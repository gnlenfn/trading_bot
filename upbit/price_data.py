import time
from models.models import *
from apscheduler.schedulers.background import BackgroundScheduler
from upbit_basic import *


tickers = ['BTC', 'ETH', 'LINK']
sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Seoul'})

for coin in tickers:
    if coin not in Base.metadata.tables.keys():
        print(f"create {coin} table!")
        create_crypto_table(coin)
Base.metadata.create_all(bind=engine)


for coin in tickers:
    crypto_json = get_trade_price('KRW-'+coin)
    price = crypto_json['trade_price']
    sched.add_job(insert_crypto,'cron', second=1, args=[coin, price])
sched.start()


while True:
    time.sleep(1)