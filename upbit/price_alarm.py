import logging
import telegram_bot
import upbit_basic

# logging
logger = logging.getLogger("alarm")
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
    def __init__(self, target):
        self.target = target

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

    def target_price(self):
        data = upbit_basic.get_trade_price("KRW-"+self.target)[0]
        logger.info(f"📈{self.target} 가격 알리미\n"+
                                f"{data['trade_price']} 원\n"
                                )
