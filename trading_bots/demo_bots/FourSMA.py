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


SYMBOL = uf.symbol_selector()
timeframe = uf.timeframe_selector()
ATR_F = 15
RISKREWARD = 1.5
LOTS = 0.01


#!!! Discord message
def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


# Buys and Sells determined on the dignal
def buySellBot(signal):

    os.system("cls" if os.name == "nt" else "clear")
    print("\n🤖^^^Running SMA bot^^^🤖\n")
    time.sleep(3)

    exits = 0
    msg = ""

    df = uf.getData4SMAs(symbol=SYMBOL, timeframe=timeframe)

    price = mt.symbol_tick_info(SYMBOL).ask

    atr_price = df["ATR"].iloc[-1]

    total_positions = 3
    positions = mt.positions_get(symbol=SYMBOL)

    while len(positions) < total_positions:

        if signal == 1:

            r = mt.Buy(SYMBOL, LOTS)

            print(f"B-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)

            sl = r.price - atr_price
            tp = r.price + (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 ({timeframe})-> 🟢BUY @{price}, SL = {sl}, TP = {tp}"

        if signal == -1:

            r = mt.Sell(SYMBOL, LOTS)

            print(f"S-price: {price}, sl{sl}, tp{tp}")
            print(r.comment)

            sl = r.price + atr_price
            tp = r.price - (atr_price * RISKREWARD)

            sl = round(sl, 2)
            tp = round(tp, 2)

            if r.retcode == mt.TRADE_RETCODE_DONE:
                msg = f"V75 ({timeframe})-> 🔴SELL @{price}, SL = {sl}, TP = {tp}"

    send_alert(msg)

    time.sleep(3)

    exits += uf.ATRClose(SYMBOL, atr_price)

    if exits > 0:
        print(f"Exited {exits} trades")
        uf.LossPause(1000)


def run():

    while True:

        df = uf.getData4SMAs(SYMBOL, timeframe)

        signal = uf.SMASignal(df)

        if signal != 0:
            buySellBot(signal)

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
