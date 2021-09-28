import os
import time
import argparse
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from service.strad_infinite import infinite
from service import telegram_bot
from pipeline import *


load_dotenv(verbose=True,
            dotenv_path='../../.env')

ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# logging
logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.INFO)
logger.propagate = False
# bot message log
bot_handler = telegram_bot.RequestsHandler()
message_formatter = telegram_bot.LogstashFormatter()
bot_handler.setFormatter(message_formatter)
logger.addHandler(bot_handler)
# streaming log
stream_handler = logging.StreamHandler()
a = "=" * 30
stream_formatter = logging.Formatter(f'[%(asctime)s]:%(levelname)s\n{a}\n%(message)s\n')
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


def main():
    parser = argparse.ArgumentParser(description="bot trading and make data pipeline with upbit API")
    parser.add_argument('--target', type=str, help='a ticker of coin to buy')
    parser.add_argument('--budget', type=int, help='total budget for strategy')
    parser.add_argument('--profit', type=float, default=0.2, help='profit ratio for benefit')
    parser.add_argument('--time', type=str, default='4,12,20' ,help='set an ordering time')
    parser.add_argument('--watch', type=str, default='BTC ETH LINK', help='tickers to save price on database')
    args = parser.parse_args()

    order_time = args.time
    my_strategy = infinite(args.budget, args.target, args.profit)

    ############### schedules ###############
    sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Seoul'})
    # strategies
    sched.add_job(my_strategy.infinite_bid, 'cron', hour=order_time, minute='5', id="buy_1")
    sched.add_job(my_strategy.sell_make_profit, 'interval', seconds=15, id="sell_1")
    # pipeline
    tickers = args.watch.split()
    sched.add_job(collect_price, 'cron', second='0', args=[tickers], id='collect price')
    sched.add_job(collect_account, 'cron', second='3', id='check account')
    ##########################################


    logger.info(f"{my_strategy.target} 한무 매수 시작\n" +
                f"매수 예정 시간 {order_time}시\n"+
                f"1회 매수금액: {my_strategy.minimum_order:,.2f}\n"+
                f"총 매수금액: {my_strategy.budget:,d} 원\n"+
                f"목표 수익률 : {my_strategy.profit * 100}%\n"+
                f"{int(my_strategy.num):#02d}회 매수 함"
                )
                
    sched.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

