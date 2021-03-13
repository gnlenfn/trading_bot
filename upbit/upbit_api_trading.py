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
    now = datetime.datetime.now()
    print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} Bot is waiting...")

# 비트 가격알림
def BTCprice_alarm():
    data = upbit_basic.get_trade_price("KRW-BTC")[0]
    open_p, low_p, high_p = data['opening_price'], data['low_price'], data['high_price']
    if open_p * 0.99 >= low_p:
        telegram_bot.send_message(f"🔻🔻🔻 BTC 폭락!! 👎🔻🔻🔻\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

    elif open_p * 1.01 <= high_p:
        telegram_bot.send_message(f"🔺🔺🔺 BTC 폭등각? 👍🔺🔺🔺\n\
        현재가격: {data['trade_price']}")
        print("!! BTC alarm !!")

def target_price(target):
    print(f"Seaching {target} price...")
    data = upbit_basic.get_trade_price("KRW-"+target)[0]
    telegram_bot.send_message(f"📈{target} 가격 알리미\n"+
                            f"{data['trade_price']} 원\n"
                            )
####################################################################
    
def sell_make_profit(target, profit, min_order):
    now = datetime.datetime.now()
    minimum_order = min_order
    minute_close_price = upbit_basic.get_trade_price("KRW-"+target, "minutes", "1", "1")[0]['trade_price']
    order_vol = minimum_order / minute_close_price

    if not upbit_basic.get_coin_account(target):
        print(minute_close_price, order_vol)
        upbit_basic.order("KRW-"+target, 'bid', order_vol, 'limit', minute_close_price)
        print(f"{datetime.datetime.now()} First buying {target}")

        time.sleep(5)
        telegram_bot.send_message(
            f"첫 매수 시작\n"+
            f"매수 수량: {target} {order_vol:.8f} 개\n"+
            f"매수 평단: {upbit_basic.get_coin_account(target)['avg_buy_price']}\n"+
            f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")
    else:
        current_avg_price = float(upbit_basic.get_coin_account(target)['avg_buy_price'])
        current_volume = float(upbit_basic.get_coin_account(target)['balance'])
        #print(f"not for sale at {minute_close_price}")
        if current_avg_price * (1.0 + profit) <= float(minute_close_price):  # 평단 * target 보다 현재 가격이 높으면 매도
            print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} Sold all {target} with benefit")
            telegram_bot.send_message(
                f"상승으로 익절\n"+
                f"매도 수량: {target} {current_volume:.8f} 개\n"+
                f"매도 평단: {upbit_basic.get_coin_account(target)['avg_buy_price']:}\n"+
                f"실현 수익: {current_volume * minute_close_price} 원\n"+
                f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")
            upbit_basic.order(market="KRW-"+target, side='ask', vol=current_volume,
                price=minute_close_price, types='limit')  # 익절 작업



def main():
    parser = argparse.ArgumentParser(description="tutorial")
    parser.add_argument('--target-coin', type=str, help='a coin to buy')
    parser.add_argument('--profit', type=float, help='profit ratio for benefit')
    parser.add_argument('--min', type=float, help='minimum amount of KRW')
    args = parser.parse_args()

    buy_time = '4, 12, 20'
    ############### schedules ###############
    sched = BackgroundScheduler()
    sched.add_job(logging, 'interval', hours=2)
    sched.add_job(lambda: strad_infinite.infinite_bid(args.target_coin, args.profit, args.min), 
                'cron', hour=buy_time, id="buy_1")
    sched.add_job(BTCprice_alarm, 'interval', seconds=10)
    sched.add_job(lambda: target_price(args.target_coin), 'cron', hour='1, 9, 13, 17, 21')
    sched.add_job(lambda: sell_make_profit(args.target_coin, args.profit, args.min), 'interval', seconds=5)
    ##########################################

    sched.start()
    telegram_bot.send_message(f"{args.target_coin} 한무 매수 시작\n" +
                            f"매수 예정 시간 {buy_time}시")
    print(f"Bot Starts to trading {args.target_coin}")
    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    main()

