from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import pymysql
import datetime
import os
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()
load_dotenv(verbose=True, dotenv_path='/home/gnlenfn/pipe/trading_bot/.env')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv("PORT")

engine = create_engine(f'mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/upbit')
connect = engine.connect()
session = Session(bind=engine)
metadata = MetaData()
Base = declarative_base(bind=engine)


def create_crypto_table(name):
    class Crypto(Base):
        __tablename__ = name.upper()
        id = Column(Integer, primary_key=True)
        time = Column(DateTime, default=datetime.datetime.now())
        ticker = Column(String(10))
        price = Column(Float)
        volume = Column(Float)
    return Crypto()


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10))
    balance = Column(Float)
    avg_buy_price = Column(Float)
    value = Column(Float)


class Records(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, default=datetime.datetime.now())
    ticker = Column(String(10))
    avg_purchase_price = Column(Float) # 평단
    num_of_purchase = Column(Float)    # 매수 수량
    purchase_price = Column(Float)     # 매수 가격
    holdings = Column(Float)           # 보유 수량
    round = Column(Integer)            # 회차
    cycle = Column(Integer)            # 몇 번째 싸이클?


def insert_crypto(table_name, price, volume): # 매 분 가격 기록
    target = Base.metadata.tables[table_name]
    t = insert(target).values(time=datetime.datetime.now(), ticker=table_name, price=price, volume=volume)
    connect.execute(t)


def insert_records(ticker, avg, num, price, holds, round, cycle):
    target = Base.metadata.tables['records']
    rec = insert(target).values(time=datetime.datetime.now(),
            ticker=ticker,
            avg_purchase_price=avg,
            num_of_purchase=num,
            purchase_price=price,
            holdings=holds,
            round=round, cycle=cycle)
    connect.execute(rec)


def insert_accounts(tick, balance, avg):
    if tick == 'KRW':
        status = insert(Account).values(ticker=tick,
                                balance=balance,
                                avg_buy_price=avg,
                                value=balance*1)
    else:
        status = insert(Account).values(ticker=tick,
                                    balance=balance,
                                    avg_buy_price=avg,
                                    value=balance*avg)
    connect.execute(status)


def update_accounts(tick, balance, avg):
    if tick == 'KRW':
        status = update(Account).values(ticker=tick,
                                balance=balance,
                                avg_buy_price=avg,
                                value=balance*1).\
                            where(Account.ticker==tick)
    else:
        status = update(Account).values(ticker=tick,
                                    balance=balance,
                                    avg_buy_price=avg,
                                    value=balance*avg).\
                                where(Account.ticker==tick)
    connect.execute(status)


def delete_table(table_name):
    target = Base.metadata.tables[table_name]
    target.drop(engine)


if __name__ == "__main__":
    eth = create_crypto_table('ETH')
    btc = create_crypto_table('BTC')
    account = Account()
    records = Records()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    insert_crypto('ETH', 2000.0, 11)
    # delete_table('BTC')
    insert_records('LINK', 33684.59, 1.8388, 29910, 70.9905, 36, 1)
    insert_accounts(tick='LINK', balance=1.5, avg=2000000.0)
    update_accounts(tick='LINK', balance=0.5, avg=1000000.0)