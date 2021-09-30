from models.models import *
from service import telegram_bot
from service import upbit_basic
import time
import logging


# logging
logger = logging.getLogger('ordering')
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


class infinite:
    def __init__(self, budget, target, profit):
        self.num = 0
        self.budget = budget
        self.minimum_order = self.budget // 40
        self.target = target
        self.profit = profit
        if session.query(Account).filter(Account.ticker == self.target).first():
            # 매수 금액 // 최소주문금액 --> 현재 몇차매수까지 진행?
            total = session.query(Account.balance * Account.avg_buy_price).filter(Account.ticker == self.target).first()[0]
            self.num = total // self.minimum_order


    # 전략에 따라 계속 매수
    def infinite_bid(self):
        try:
            crypto = Crypto.for_symbol(self.target)         # price table of self.target
            current_price = session.query(crypto.price).order_by(crypto.time.desc()).first()[0]  # current price = order_by time last one
            my_avg_price = session.query(Account.avg_buy_price).filter(Account.ticker == self.target).first()[0]
            my_current_volume = session.query(Account.balance).filter(Account.ticker == self.target).first()[0]
            order_vol = self.minimum_order / current_price

            # 첫 매수 (보유한 self.target 없을 때)
            if not session.query(Account).filter(Account.ticker == self.target).first():
                upbit_basic.order("KRW-"+self.target, 'bid', order_vol, 'limit', current_price)
                self.num += 1

                time.sleep(30)
                insert_records(ticker=self.target, order='buy', avg=my_avg_price,
                                    num=order_vol, price=current_price,
                                    holds=my_current_volume,
                                    rounds=self.num, cycle=self.num // 40 + 1)

                logger.info(
                    f"{self.num % 40}회차 매수!\n"+
                    f"매수 수량: {self.target} {order_vol:,.4f} 개\n"+
                    f"매수 가격: {current_price:,.2f}\n"+
                    f"현재 수량: {self.target} {my_current_volume:.4f} 개\n"+
                    f"현재 평단: {my_avg_price:,.2f}\n"+
                    f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):,.2f} 원")
            #else:
            # KRW 잔고 없으면 or 40회 매수 마치면 (손절 or 목표도달 못한 익절)
            if self.num == 40:  
                insert_records(ticker=self.target, order='sell', avg=my_avg_price,
                                num=order_vol, price=current_price,
                                holds=0,
                                rounds=self.num, cycle=self.num // 40 + 1)
                logger.info(
                    f"{self.num % (40)}회 도달 전체매도\n"+
                    f"매도 수량: {self.target} {my_current_volume:,.4f} 개\n"+
                    f"매도 가격: {my_avg_price}\n"+
                    f"실현 손익: {my_current_volume * current_price - 40 * self.minimum_order:,.2f} 원\n"+
                    "한사이클 끝!")
                upbit_basic.order(market="KRW-"+self.target, side='ask', vol=my_current_volume,
                    price=current_price, types='limit')


            # 현재 가격이 목표 가격보다 낮으면 추가 매수
            elif my_avg_price * (1.0 + self.profit) > current_price :  
                upbit_basic.order(market="KRW-"+self.target, side='bid', vol=order_vol, 
                    price=current_price, types='limit')
                self.num += 1

                time.sleep(30)
                
                insert_records(ticker=self.target, order='buy', avg=my_avg_price,
                                num=order_vol, price=current_price,
                                holds=my_current_volume,
                                rounds=self.num, cycle=self.num // 40 + 1)

                avg_buy_after = session.query(Account.avg_buy_price).filter(Account.ticker == self.target).first()[0]

                logger.info(
                    f"{self.num % 40}회차 매수\n"+
                    f"매수 수량: {order_vol:,.4f}\n"+
                    f"매수 가격: {current_price:,.2f}\n"+
                    f"현재 수량: {self.target} {my_current_volume:.4f} 개\n"+
                    f"현재 평단: {avg_buy_after:,.2f}\n"+
                    f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):,.2f} 원")

        except Exception as ex:
            logger.error("error on infinite_bid")
            logger.exception(ex)

    
    # 목표가에 도달하면 매도하기
    def sell_make_profit(self):
        try:
            current_price = upbit_basic.get_trade_price("KRW-"+self.target, "minutes", "1", "1")['trade_price'] # 현재가 1분봉
            if not session.query(Account).filter(Account.ticker == self.target).first():
                pass
            else:
                my_avg_price = session.query(Account.avg_buy_price).filter(Account.ticker == self.target).first()[0]
                my_current_volume = session.query(Account.balance).filter(Account.ticker == self.target).first()[0]
                
                # 평단 * profit 보다 현재 가격이 높으면 매도
                if my_avg_price * (1.0 + self.profit) <= current_price:  
                    logger.info(
                        f"상승으로 익절\n"+
                        f"{self.num}회차 매수 후 매도\n"+
                        f"현재 평단: {my_avg_price:,.2f}\n"+
                        f"매도 수량: {self.target} {my_current_volume:,.4f} 개\n"+
                        f"매도 가격: {current_price}\n"+
                        f"실현 손익: {my_current_volume * current_price - self.num * self.minimum_order:,.2f} 원\n"+
                        "한사이클 끝!")
                    upbit_basic.order(market="KRW-"+self.target, side='ask', vol=my_current_volume,
                        price=current_price, types='limit')  # 익절 작업
                    
                    time.sleep(30)
                    insert_records(ticker=self.target, order='sell', avg=my_avg_price,
                                        num=my_current_volume, price=current_price,
                                        holds=0,
                                        rounds=self.num, cycle=self.num // 40 + 1)

        except Exception as ex:
            logger.error("error on sell_make_profit")
            logger.exception(ex)

