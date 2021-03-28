import datetime
import os
import time
import argparse
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

#import strad_infinite
from strad_infinite import infinite
import telegram_bot
import upbit_basic

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

# 가격알림
class alarm:
    # 비트가격 알람
    def BTCprice_alarm(self):
        data = upbit_basic.get_trade_price("KRW-BTC")[0]
        open_p, low_p, high_p = data['opening_price'], data['low_price'], data['high_price']
        if open_p * 0.99 >= low_p:
            logger.info(f"🔽🔽🔽 BTC 폭락!! 👎🔽🔽🔽\n\
            현재가격: {data['trade_price']}")

        elif open_p * 1.01 <= high_p:
            logger.info(f"🔺🔺🔺 BTC 폭등각? 👍🔺🔺🔺\n\
            현재가격: {data['trade_price']}")

    def target_price(self, target):
        data = upbit_basic.get_trade_price("KRW-"+target)[0]
        logger.info(f"📈{target} 가격 알리미\n"+
                                f"{data['trade_price']} 원\n"
                                )
####################################################################



def main():
    parser = argparse.ArgumentParser(description="tutorial")
    parser.add_argument('--target-coin', type=str, help='a coin to buy')
    parser.add_argument('--profit', type=float, help='profit ratio for benefit')
    #parser.add_argument('--min', type=float, help='minimum amount of KRW')
    parser.add_argument('--budget', type=int, help='total budget for infinite_bid')
    args = parser.parse_args()

    buy_time = '4, 12, 20'

    my_strategy = infinite()
    my_alarm = alarm()
    ############### schedules ###############
    sched = BackgroundScheduler()
    # strategies
    sched.add_job(lambda: my_strategy.infinite_bid(args.target_coin, args.min), 
                'cron', hour=buy_time, id="buy_1")
    sched.add_job(lambda: my_strategy.sell_make_profit(args.target_coin, args.profit, args.min), 'interval', seconds=10)
    # alarms
    sched.add_job(my_alarm.BTCprice_alarm, 'interval', minutes=1)
    sched.add_job(lambda: my_alarm.target_price(args.target_coin), 'cron', hour='1, 9, 13, 17, 21')
    ##########################################
    logger.info(f"{args.target_coin} 한무 매수 시작\n" +
                            f"매수 예정 시간 {buy_time}시")

    sched.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

