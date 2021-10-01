from sqlalchemy import *
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
import pymysql
import datetime
import os
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()
load_dotenv(verbose=True, dotenv_path='../../.env')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv("PORT")

engine = create_engine(f'mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/upbit')
connect = engine.connect()
session = Session(bind=engine)
metadata = MetaData()
Base = declarative_base(bind=engine)


class Crypto(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, default=datetime.datetime.now())
    ticker = Column(String(10))
    price = Column(Float)
    volume = Column(Float)

    def __repr__(self):
        return "Crypto(symbol=%r, price=%r)" % (self.symbol, self.price)

    _symbols = {}

    @classmethod
    def for_symbol(cls, symbol):
        if symbol in cls._symbols:
            return cls._symbols[symbol]

        cls._symbols[symbol] = crypto_cls = type(
        "%s_Crypto" % symbol,
        (cls, ),
        {
        "__tablename__": "%s" % symbol,
        "symbol": symbol
        }
        )

        return crypto_cls


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, default=datetime.datetime.now())
    ticker = Column(String(10))
    balance = Column(Float)
    avg_buy_price = Column(Float)
    current_price = Column(Float)
    current_value = Column(Float)
    bought_value = Column(Float)


class Records(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, default=datetime.datetime.now())
    ticker = Column(String(10))
    order = Column(String(5))          # 거래 타입
    avg_purchase_price = Column(Float) # 평단
    num_of_trade = Column(Float)       # 거래 수량
    trade_price = Column(Float)        # 거래 가격
    holdings = Column(Float)           # 거래 후 보유 수량
    round = Column(Integer)            # 회차
    cycle = Column(Integer)            # 몇 번째 싸이클?


def insert_crypto(table_name, price, volume): # 매 분 가격 기록
    target = Base.metadata.tables[table_name]
    t = insert(target).values(time=datetime.datetime.now(), ticker=table_name, price=price, volume=volume)
    connect.execute(t)


def insert_records(ticker, order, avg, num, price, holds, rounds, cycle):
    target = Base.metadata.tables['records']
    rec = insert(target).values(time=datetime.datetime.now(),
            ticker=ticker,
            order=order,
            avg_purchase_price=avg,
            num_of_trade=num,
            trade_price=price,
            holdings=holds,
            round=rounds, cycle=cycle)
    connect.execute(rec)


def insert_accounts(tick, balance, avg):
    if session.query(Account).filter(Account.ticker == tick).first():
        return

    table = Crypto.for_symbol(tick)
    if tick == 'KRW':
        status = insert(Account).values(ticker=tick,
                                time=datetime.datetime.now(),
                                balance=balance,
                                avg_buy_price=avg,
                                current_price=1,
                                current_value=balance * 1,
                                bought_value=balance * 1)
    else:
        q = session.query(table.price).all()[-1][0]
        status = insert(Account).values(ticker=tick,
                                    time=datetime.datetime.now(),
                                    balance=balance,
                                    avg_buy_price=avg,
                                    current_price=q,
                                    current_value=balance * q,
                                    bought_value=balance * avg)
    connect.execute(status)


def update_accounts(tick, balance, avg):
    table = Crypto.for_symbol(tick)
    if tick == 'KRW':
        status = update(Account).values(ticker=tick,
                                time=datetime.datetime.now(),
                                balance=balance,
                                avg_buy_price=avg,
                                current_price=1,
                                current_value=balance * 1,
                                bought_value=balance * 1).\
                            where(Account.ticker==tick)
    else:
        q = session.query(table.price).all()[-1][0]
        status = update(Account).values(ticker=tick,
                                    time=datetime.datetime.now(),
                                    balance=balance,
                                    avg_buy_price=avg,
                                    current_price=q,
                                    current_value=balance * q,
                                    bought_value=balance * avg).\
                                where(Account.ticker==tick)
    connect.execute(status)


def delete_on_account(ticker):
    ticker = ticker.upper()
    status = delete(Account).where(Account.ticker == ticker)
    connect.execute(status)


def delete_table(table_name):
    target = Base.metadata.tables[table_name]
    target.drop(engine)


def reset_db(engine=engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)