import time
from models.models import *
from apscheduler.schedulers.background import BackgroundScheduler
from upbit_basic import *


sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Seoul'})
sched.start()

def table_exists(name):
    ret = inspect(engine).has_table(name)
    return ret

def collect_price(tickers):    

    for coin in tickers:
        if coin not in Base.metadata.tables.keys():
            print(f"create {coin} table!")
            create_crypto_table(coin)
            Base.metadata.create_all(bind=engine)


    for coin in tickers:
        crypto_json = get_trade_price('KRW-'+coin)
        price = crypto_json['trade_price']
        vol = crypto_json['candle_acc_trade_volume']
        insert_crypto(coin, price, vol)
    

def collect_account():
    data = get_coin_account()
    # 평가액이 5000원 이상인 코인만 볼 것
    valid_account = [coin for coin in data if float(coin['balance']) * float(coin['avg_buy_price']) >= 5000] # 
    valid_account.append(data[0]) # add KRW

    if not table_exists('account'):
        # account table이 없으면 만들기
        account = Account()
        Base.metadata.create_all(engine)

    else:
        for coin in valid_account:
            tick = coin['currency']
            balance = coin['balance']
            avg = coin['avg_buy_price']

            if not session.query(Account).filter(Account.ticker == tick).first():
                insert_accounts(tick, float(balance), float(avg))
        
        for coin in valid_account:
            tick = coin['currency']
            balance = coin['balance']
            avg = coin['avg_buy_price']
            update_accounts(tick, float(balance), float(avg))


if __name__ == "__main__":
    tickers = ['BTC', 'ETH', 'LINK']

    sched.add_job(collect_price, 'cron', minute='0, 15, 30, 45', args=[tickers])
    sched.add_job(collect_account, 'cron', minute='10')

    while True:
        time.sleep(1)
