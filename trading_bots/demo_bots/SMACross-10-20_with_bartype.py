import os
import time
import pandas as pd
import schedule
import numpy as np
from datetime import datetime, timedelta
import pandas_ta as ta
from apscheduler.schedulers.blocking import BlockingScheduler
import MetaTrader5 as mt
import login_info as li
import requests
import discord_info as di
import bot_functions as uf


symbol = uf.symbol_selector()  # "Volatility 75 Index"
tf = uf.timeframe_selector()  # mt.TIMEFRAME_M15


# Initialization of dataframe
def getData():

    df = uf.GetPriceData(symbol, tf)
    df = uf.ATRBullBear(df)

    return df


def BullBear(df1):

    length = len(df1)
    bartype = [0] * length

    open = list(df1["Open"])
    close = list(df1["Close"])

    for row in range(0, length):
        if open[row] > close[row]:
            bartype[row] = -1
        elif open[row] < close[row]:
            bartype[row] = 1

    return bartype


def SMACross(x):

    x["barType"] = BullBear(x)
    bartype = x["barType"].iloc[-2]
    sma1_prev = x.MA10.iloc[-3]
    sma2_prev = x.MA20.iloc[-3]
    sma1 = x.MA10.iloc[-2]
    sma2 = x.MA20.iloc[-2]
    atr = x.ATR.iloc[-2]
    bear_atr_mean = x["bearAVG"].iloc[-2]
    bull_atr_mean = x["bullAVG"].iloc[-2]

    if bear_atr_mean < 0:
        bear_atr_mean = 0
    if bull_atr_mean < 0:
        bull_atr_mean = 0

    if (
        not sma1_prev > sma2_prev
        and sma1 > sma2
        and bartype == 1
        and atr > bull_atr_mean
    ):
        return 1
    elif (
        not sma2_prev > sma1_prev
        and sma2 > sma1
        and bartype == -1
        and atr > bear_atr_mean
    ):
        return -1
    elif sma1 > sma2 and atr > bull_atr_mean and bartype == 1:
        return 2
    elif sma2 > sma1 and atr > bear_atr_mean and bartype == -1:
        return -2
    else:
        return 0


def CrossAlert():

    os.system("cls" if os.name == "nt" else "clear")
    print("@@@ STARTING SMA CROSS ALERT @@@")
    df = getData()

    signal = SMACross(df)

    if signal != 0:

        if signal == 1:
            msg = f"Bullish SMACROSS on {symbol}"
        elif signal == -1:
            msg = f"Bearish SMACROSS on {symbol}"
        elif signal == 2:
            msg = f"Bullish movements on {symbol}"
        elif signal == -2:
            msg = f"Bearish movements on {symbol}"

        print(f"\n{msg}")
        print("*" * 120)
        print(df.tail(3))
        print("*" * 120)
        uf.send_alert(msg)
        print("Sleeping for 1/2 an hour😴")
        time.sleep(1800)

    else:
        print("*" * 120)
        print(df.tail(3))
        print("*" * 120)
        print("NO definite movemnt")


schedule.every().second.do(CrossAlert)

while True:
    try:
        schedule.run_pending()
    except:
        print("*** WAITING FOR A CONNECTION RESTING FOR A MIN... ***")
        time.sleep(60)
