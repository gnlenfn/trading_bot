import telegram_bot
import upbit_basic
import datetime
import time
import logging


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


def infinite_bid(target, profit, min_order):
    try:
        now = datetime.datetime.now()
        minimum_order = min_order
        non_budget = float(upbit_basic.get_coin_account("KRW")['balance']) - 4_000_000.0
        minute_close_price = upbit_basic.get_trade_price("KRW-"+target, "minutes", "1", "1")[0]['trade_price']
        order_vol = minimum_order / minute_close_price

        if not upbit_basic.get_coin_account(target): # target coin 보유 없으면
            upbit_basic.order("KRW-"+target, 'bid', order_vol, 'limit', minute_close_price)

            time.sleep(5)
            avg_buy_after = upbit_basic.get_coin_account(target)['avg_buy_price']
            logger.info(
                f"첫 매수 시작1\n"+
                f"{now.strftime('%Y-%m-%d %H:%M:%S')}\n"+
                f"매수 수량: {target} {order_vol:.8f} 개\n"+
                f"매수 가격: {minute_close_price}\n"+
                f"매수 평단: {avg_buy_after}\n"+
                f"현금 잔고: {upbit_basic.get_coin_account('KRW')['balance']} 원")
        else:
            current_avg_price = float(upbit_basic.get_coin_account(target)['avg_buy_price'])
            current_volume = float(upbit_basic.get_coin_account(target)['balance'])
            cash_left = float(upbit_basic.get_coin_account("KRW")['balance']) - non_budget
            
            if cash_left < minimum_order:  # 잔고 없으면 (손절 or 목표도달 못한 익절)
                logger.info(
                    f"전체매도\n"+
                    f"현재 평단: {upbit_basic.get_coin_account(target)['avg_buy_price']:.2f}\n"+
                    f"매도 수량: {target} {current_volume:.8f} 개\n"+
                    f"매도 가격: {current_avg_price}\n"+
                    f"실현 손익: {current_volume * minute_close_price} 원\n"+
                    f"현금 잔고: {upbit_basic.get_coin_account('KRW')['balance']:.2f} 원")
                upbit_basic.order(market="KRW-"+target, side='ask', vol=current_volume,
                    price=minute_close_price, types='limit')
                
                time.sleep(5)
                upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol,
                    price=minute_close_price, types='limit')

                time.sleep(5)
                avg_buy_after = upbit_basic.get_coin_account(target)['avg_buy_price']
                logger.info(
                    f"매도 후 1회차 매수 시작\n"+
                    f"매수 수량: {order_vol}\n"+
                    f"매수 가격: {minute_close_price}\n"+
                    f"현재 수량: {target} {current_volume:.8f} 개\n"+
                    #f"현재 평단: {upbit_basic.get_coin_account(target)['avg_buy_price']}\n"+
                    f"현재 평단: {avg_buy_after}\n"+
                    f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")


            elif current_avg_price > minute_close_price:  # 평단보다 현재가격이 낮은 가격이면 매수
                upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, 
                    price=minute_close_price, types='limit')

                time.sleep(5)
                avg_buy_after = upbit_basic.get_coin_account(target)['avg_buy_price']
                logger.info(
                    f"추가 매수\n"+
                    f"매수 수량: {order_vol}\n"+
                    f"매수 가격: {minute_close_price}\n"+
                    f"현재 수량: {target} {current_volume:.8f} 개\n"+
                    f"현재 평단: {avg_buy_after}\n"+
                    f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")

            # elif current_avg_price * (1.0 + profit) <= float(minute_close_price):  # 평단 * 1.1 보다 현재 가격이 높으면 매도
            #     # print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} Sold all {target} with benefit")
            #     logger.info(
            #         f"상승으로 익절\n"+
            #         f"현재 평단: {upbit_basic.get_coin_account(target)['avg_buy_price']:}\n"+
            #         f"매도 수량: {target} {current_volume:.8f} 개\n"+
            #         f"매도 가격: {current_avg_price}\n"+
            #         f"실현 수익: {current_volume * minute_close_price} 원\n"+
            #         f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")
            #     upbit_basic.order(market="KRW-"+target, side='ask', vol=current_volume,
            #         price=minute_close_price, types='limit')  # 익절 작업

            #     time.sleep(5)
            #     upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, #'0.01269036',
            #         price=minute_close_price, types='limit')   # 익절 후 재매수
                
            else:
                upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, 
                    price=minute_close_price, types='limit')

                time.sleep(5)
                avg_buy_after = upbit_basic.get_coin_account(target)['avg_buy_price']
                logger.info(
                    f"추가 매수\n"+
                    f"매수 수량: {order_vol}\n"+
                    f"매수 가격: {minute_close_price}\n"+
                    f"현재 수량: {target} {current_volume:.8f} 개\n"+
                    f"현재 평단: {avg_buy_after}\n"+
                    f"현금 잔고: {round(float(upbit_basic.get_coin_account('KRW')['balance']), 3)} 원")
    
    except Exception as ex:
        logger.error("error on infinite_bid")
        logger.exception(ex)

