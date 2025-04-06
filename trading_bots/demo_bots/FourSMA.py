import requests
import MetaTrader5 as mt
import login_info as li
from datetime import datetime, timedelta
import pandas_ta as ta
import time
import pandas as pd
import schedule
import discord_info as di
import bot_functions as uf


SYMBOL = "Volatility 75 Index"

ATR_F = 15
RISKREWARD = 1.5
LOTS = 0.01


# Retrieves price info and ask price then puts it into a dataframe
def getData():
    if not mt.initialize():
        print(f"failed to initialize {mt.last_error()}")
    else:
        if not mt.login(login=li.login_id, password=li.password, server=li.server):
            print(f"Failed to login to Account #{li.login_id}")

    timeframe = mt.TIMEFRAME_H1
    now = datetime.now()
    date_from = now - timedelta(days=21)

    ask = mt.symbol_info_tick(SYMBOL).ask

    data = mt.copy_rates_range(SYMBOL, timeframe, date_from, now)
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
    df.columns = ["Local time", "Open", "High", "Low", "Close"]

    # Indicators
    df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
    df["MA10"] = ta.sma(close=df.Close, length=10)
    df["MA20"] = ta.sma(close=df.Close, length=20)
    df["MA100"] = ta.sma(close=df.Close, length=100)
    df["MA200"] = ta.sma(close=df.Close, length=200)
    df["ATRMean"] = df["ATR"].rolling(12).mean()

    return df, ask


# Checks the validity of the signal
def smaSignal():

    df = getData()[0]

    try:
        if (
            df["MA10"].iloc[-1]
            < df["MA20"].iloc[-1]
            < df["MA100"].iloc[-1]
            < df["MA200"].iloc[-1]
        ):
            return -1
        elif (
            df["MA10"].iloc[-1]
            > df["MA20"].iloc[-1]
            > df["MA100"].iloc[-1]
            > df["MA200"].iloc[-1]
        ):
            return 1
        else:
            return 0
    except:
        print("Not enough data...")


#!!! Discord message
def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


def bot(signal):

    print("\n🤖Running SMA bot...🤖\n")

    exits = 0

    df = getData()[0]
    price = getData()[1]
    atr_price = df["ATR"].iloc[-1]

    if mt.positions_total() < 2:

        if signal == 1:
            sl = df["Close"].iloc[-1] - atr_price
            tp = df["Close"].iloc[-1] + (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            r = mt.Buy(SYMBOL, LOTS)
            print(f"B-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)
            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 -> 🟢BUY @{price}, SL = {sl}, TP = {tp}"
                send_alert(msg)

        if signal == -1:
            sl = df["Close"].iloc[-1] + atr_price
            tp = df["Close"].iloc[-1] - (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            r = mt.Sell(SYMBOL, LOTS)
            print(f"S-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)
            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 -> 🔴SELL @{price}, SL = {sl}, TP = {tp}"
                send_alert(msg)

    else:
        exits += uf.ATRClose(SYMBOL, atr_price)

    if exits > 0:
        print(f"Exited {exits} trades")
        uf.LossPause(1000)
    # print(df.tail(20))


# bot()


def run():
    while True:
        signal = smaSignal()
        if signal != 0:
            uf.KillSwitch(SYMBOL)
            bot(signal)

        else:
            print("❌NO SIGNAL❌")
            time.sleep(30)


schedule.every(1).seconds.do(run)
while True:
    try:
        schedule.run_pending()
    except:
        print("*** WAITING FOR A CONNECTION RESTING FOR A MIN... ***")
        time.sleep(60)
