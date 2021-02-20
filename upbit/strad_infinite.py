import telegram_bot
import upbit_basic
import datetime


"""
- 매일 같은 시간 기준 (아침/저녁 9시)
- 원금 100만원 40분할 기준 1회 25000원 매수
- 25000원 기준 첫 매수 수량을 반복적으로 매수 --> ETH 0.01269036
- 평단 아래이면 매수 / 아니면 pass
- 매일 내 평단 대비 10%에 지정가매도
- 매도 되거나 원금을 모두 소진하면 다시 시작

"""


def infinite_bid():
    target = "ETH"
    print(upbit_basic.get_coin_account(target))
    current_avg_price = float(upbit_basic.get_coin_account(target)['avg_buy_price'])
    current_volume = float(upbit_basic.get_coin_account(target)['balance'])
    cash_left = float(upbit_basic.get_coin_account("KRW")['balance'])
    minute_close_price = upbit_basic.getTradePrice("KRW-"+target, "1", "1")[0]['trade_price']
    order_vol = 100000 / minute_close_price
    print("Bot is Working!")
    if cash_left < 25000:  # 잔고 없으면 (손절 or 목표도달 못한 익절)
        print(f"{datetime.datetime.now()} Sell all left")
        telegram_bot.send_message(
            f"전체매도\n"+
            f"매도 수량: {current_volume} ETH 개\n"+
            f"매도 평단: {upbit_basic.get_coin_account('ETH')['avg_buy_price']}\n"+
            f"현금 잔고: {upbit_basic.get_coin_account('KRW')['balance']} 원")
        upbit_basic.order(market="KRW-"+target, side='ask', vol=current_volume,
              price=minute_close_price, types='limit')

    if current_volume < 0.0005:  # 리셋 후 재매수
        print(f"{datetime.datetime.now()} Restart Process..")
        upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol,
              price=minute_close_price, types='limit')
        telegram_bot.send_message(
            f"매수 재시작\n"+
            f"매수 수량: {order_vol}\n"+
            f"현재 수량: {current_volume} ETH 개\n"+
            f"현재 평단: {upbit_basic.get_coin_account('ETH')['avg_buy_price']}\n"+
            f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):.2f} 원")

    elif current_avg_price > minute_close_price:  # 평단보다 현재가격이 낮은 가격이면 매수
        print(f"{datetime.datetime.now()} Buy more ETH")
        upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, #'0.01269036',
              price=minute_close_price, types='limit')
        telegram_bot.send_message(
            f"추가 매수\n"+
            f"매수 수량: {order_vol}\n"+
            f"현재 수량: {current_volume} ETH 개\n"+
            f"현재 평단: {upbit_basic.get_coin_account('ETH')['avg_buy_price']}\n"+
            f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):.2f} 원")

    elif current_avg_price * 1.1 <= float(minute_close_price):  # 평단 * 1.1 보다 현재 가격이 높으면 매도
        print(f"{datetime.datetime.now()} Sold all ETH with benefit")
        telegram_bot.send_message(
            f"상승으로 익절\n"+
            f"매도 수량: {current_volume} ETH 개\n"+
            f"매도 평단: {upbit_basic.get_coin_account('ETH')['avg_buy_price']}\n"+
            f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):.2f} 원")
        upbit_basic.order(market="KRW-"+target, side='ask', vol=current_volume,
              price=minute_close_price, types='limit')  # 익절 작업
        upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, #'0.01269036',
              price=minute_close_price, types='limit')   # 익절 후 재매수
    else:
        print(f"{datetime.datetime.now()} Buy more ETH")
        upbit_basic.order(market="KRW-"+target, side='bid', vol=order_vol, #'0.01269036',
              price=minute_close_price, types='limit')
        telegram_bot.send_message(
            f"추가 매수"+
            f"매수 수량: {order_vol}\n"+
            f"현재 수량: {current_volume} ETH 개\n"+
            f"현재 평단: {upbit_basic.get_coin_account('ETH')['avg_buy_price']}\n"+
            f"현금 잔고: {float(upbit_basic.get_coin_account('KRW')['balance']):.2f} 원")
