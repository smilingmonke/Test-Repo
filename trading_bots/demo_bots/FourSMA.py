import os
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


# Checks the validity of the signal
def smaSignal():

    df = uf.getData()[0]

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
            return 1
    except:
        print("Not enough data...")


#!!! Discord message
def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


def bot(signal):
    os.system("cls" if os.name == "nt" else "clear")
    print("\n🤖^^^Running SMA bot^^^🤖\n")
    time.sleep(3)

    exits = 0
    msg = ""
    df = uf.getData()[0]
    price = uf.getData()[1]
    atr_price = df["ATR"].iloc[-1]
    total_positions = 2

    while mt.positions_total() < total_positions:

        if signal == 1:
            sl = df["Close"].iloc[-1] - atr_price
            tp = df["Close"].iloc[-1] + (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            r = mt.Buy(SYMBOL, LOTS)
            print(f"B-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)
            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 (H1)-> 🟢BUY @{price}, SL = {sl}, TP = {tp}"

        if signal == -1:
            sl = df["Close"].iloc[-1] + atr_price
            tp = df["Close"].iloc[-1] - (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            r = mt.Sell(SYMBOL, LOTS)
            print(f"S-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)
            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 (H1)-> 🔴SELL @{price}, SL = {sl}, TP = {tp}"

    # send_alert(msg)

    print(df.tail(1))
    time.sleep(3)

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
            bot(signal)

        else:
            os.system("cls" if os.name == "nt" else "clear")
            print("❌NO SIGNAL❌")
            time.sleep(30)


schedule.every(1).seconds.do(run)
while True:
    try:
        schedule.run_pending()
    except:
        print("*** WAITING FOR A CONNECTION RESTING FOR A MIN... ***")
        time.sleep(60)
