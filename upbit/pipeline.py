import time
from models.models import *
from apscheduler.schedulers.background import BackgroundScheduler
from service.upbit_basic import *


sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Seoul'})
sched.start()

def table_exists(name):
    ret = inspect(engine).has_table(name)
    return ret

def collect_price(tickers):    
    for coin in tickers:
        if coin not in Base.metadata.tables.keys():
            print(f"create {coin} table!")
            Crypto.for_symbol(coin)
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
        # 나의 자산 정보 update
        for coin in valid_account:
            tick = coin['currency']
            balance = coin['balance']
            avg = coin['avg_buy_price']
            if session.query(Account).filter(Account.ticker == tick).first():
                update_accounts(tick, float(balance), float(avg))
            else:
                insert_accounts(tick, float(balance), float(avg))
        
        # 매도 후 없는 자산 삭제
        coin_in_account = session.query(Account.ticker).all()
        for coin in [c[0] for c in coin_in_account]:
            if coin not in [crypto['currency'] for crypto in valid_account]:
                delete_on_account(coin)


if __name__ == "__main__":
    tickers = ['BTC', 'ETH', 'LINK']

    # sched.add_job(collect_price, 'cron', minute='0, 15, 30, 45', args=[tickers])
    # sched.add_job(collect_account, 'cron', minute='20')
    crypto = Crypto.for_symbol("LINK")
    s = session.query(crypto).all()
    q = session.query(crypto.price).order_by(crypto.time.desc()).first()[0]
    r = session.query(Account.ticker).all()
    
    #insert_accounts("ADA", 1., 2.)
    #delete_on_account("ADA")


