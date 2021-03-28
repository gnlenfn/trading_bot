import os
import time
import argparse
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

#import strad_infinite
from strad_infinite import infinite
from price_alarm import alarm
import telegram_bot


load_dotenv(verbose=True,
            dotenv_path='../.env')

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
    parser = argparse.ArgumentParser(description="tutorial")
    parser.add_argument('--target-coin', type=str, help='a coin to buy')
    parser.add_argument('--profit', type=float, help='profit ratio for benefit')
    parser.add_argument('--budget', type=int, help='total budget for infinite_bid')
    args = parser.parse_args()

    buy_time = '4, 12, 20'

    my_strategy = infinite(args.budget, args.target_coin, args.profit)
    my_alarm = alarm(args.target_coin)

    ############### schedules ###############
    sched = BackgroundScheduler()
    # strategies
    sched.add_job(my_strategy.infinite_bid, 'cron', second=buy_time, id="buy_1")
    sched.add_job(my_strategy.sell_make_profit, 'interval', seconds=10, id="sell_1")
    # alarms
    sched.add_job(my_alarm.BTCprice_alarm, 'cron', second=1)
    sched.add_job(my_alarm.target_price, 'cron', hour='1, 9, 13, 17, 21')
    ##########################################

    logger.info(f"{args.target_coin} 한무 매수 시작\n" +
                            f"매수 예정 시간 {buy_time}시")

    sched.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

