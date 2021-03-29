import telegram_bot
import upbit_basic
import time
import logging
import math


"""
- 매일 같은 시간 기준 (아침/저녁 9시)
- 원금 100만원 40분할 기준 1회 25000원 매수
- 25000원 기준 첫 매수 수량을 반복적으로 매수 --> ETH 0.01269036
- 평단 아래이면 매수 / 아니면 pass
- 매일 내 평단 대비 10%에 지정가매도
- 매도 되거나 원금을 모두 소진하면 다시 시작

"""

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
        self.non_budget = float(upbit_basic.get_coin_account("KRW")['balance']) - self.budget
        self.minimum_order = self.budget // 40
        self.target = target
        self.profit = profit
        if upbit_basic.get_coin_account(self.target):
            # my_volume * avg_buy_price --> 매수 금액 
            total = float(upbit_basic.get_coin_account(self.target)['balance']) * float(upbit_basic.get_coin_account(self.target)['avg_buy_price'])
            # 매수 금액 // 최소주문금액 --> 현재 몇차매수까지 진행?
            self.num = (total // self.minimum_order)

    def infinite_bid(self):
        try:
            current_price = upbit_basic.get_trade_price("KRW-"+self.target, "minutes", "1", "1")[0]['trade_price'] # 현재가 1분봉
            order_vol = self.minimum_order / current_price

            my_avg_price = float(upbit_basic.get_coin_account(self.target)['avg_buy_price'])
            my_current_volume = float(upbit_basic.get_coin_account(self.target)['balance'])
            my_cash_left = float(upbit_basic.get_coin_account("KRW")['balance']) - self.non_budget
            
            # 잔고 없으면 (손절 or 목표도달 못한 익절)
            if my_cash_left < self.minimum_order:  
                logger.info(
                    f"전체매도\n"+
                    f"현재 평단: {upbit_basic.get_coin_account(self.target)['avg_buy_price']:,.2f}\n"+
                    f"매도 수량: {self.target} {my_current_volume:,.4f} 개\n"+
                    f"매도 가격: {my_avg_price}\n"+
                    f"실현 손익: {my_current_volume * current_price:,.2f} 원\n"+
                    "한사이클 끝!")
                upbit_basic.order(market="KRW-"+self.target, side='ask', vol=my_current_volume,
                    price=current_price, types='limit')
                self.num = 0

            # 현재 가격이 목표 가격보다 낮으면 추가 매수
            elif my_avg_price * (1.0 + self.profit) > current_price :  
                upbit_basic.order(market="KRW-"+self.target, side='bid', vol=order_vol, 
                    price=current_price, types='limit')
                self.num +=1

                time.sleep(30)
                avg_buy_after = float(upbit_basic.get_coin_account(self.target)['avg_buy_price'])
                logger.info(
                    f"{self.num}회차 매수\n"+
                    f"매수 수량: {order_vol:,.4f}\n"+
                    f"매수 가격: {current_price:,.2f}\n"+
                    f"현재 수량: {self.target} {my_current_volume:.4f} 개\n"+
                    f"현재 평단: {avg_buy_after:,.2f}\n"+
                    f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")

        except Exception as ex:
            logger.error("error on infinite_bid")
            logger.exception(ex)

        
    def sell_make_profit(self):
        try:
            current_price = upbit_basic.get_trade_price("KRW-"+self.target, "minutes", "1", "1")[0]['trade_price'] # 현재가 1분봉
            order_vol = self.minimum_order / current_price
            if not upbit_basic.get_coin_account(self.target): # target coin 보유 없으면
                upbit_basic.order("KRW-"+self.target, 'bid', order_vol, 'limit', current_price)
                self.num += 1

                time.sleep(30)
                my_avg_price = float(upbit_basic.get_coin_account(self.target)['avg_buy_price'])
                my_current_volume = float(upbit_basic.get_coin_account(self.target)['balance'])
                logger.info(
                    # 첫 매수
                    f"{self.num}회차 매수!\n"+
                    f"매수 수량: {self.target} {order_vol:,.4f} 개\n"+
                    f"매수 가격: {current_price:,.2f}\n"+
                    f"현재 수량: {self.target} {my_current_volume:.4f} 개\n"+
                    f"현재 평단: {my_avg_price:,.2f}\n"+
                    f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):,.2f} 원")

            else:
                my_avg_price = float(upbit_basic.get_coin_account(self.target)['avg_buy_price'])
                my_current_volume = float(upbit_basic.get_coin_account(self.target)['balance'])

                # 평단 * profit 보다 현재 가격이 높으면 매도
                if my_avg_price * (1.0 + self.profit) <= current_price:  
                    logger.info(
                        f"상승으로 익절\n"+
                        f"현재 평단: {my_avg_price:,.2f}\n"+
                        f"매도 수량: {self.target} {my_current_volume:,.4f} 개\n"+
                        f"매도 가격: {current_price}\n"+
                        f"실현 손익: {my_current_volume * current_price:,.2f} 원\n"+
                        "한사이클 끝!")
                    upbit_basic.order(market="KRW-"+self.target, side='ask', vol=my_current_volume,
                        price=current_price, types='limit')  # 익절 작업
                    self.num = 0

        except Exception as ex:
            logger.error("error on sell_make_profit")
            logger.exception(ex)

