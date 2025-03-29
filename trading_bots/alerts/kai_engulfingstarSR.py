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

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
timeframe = mt.TIMEFRAME_H1
now = datetime.now()
yesterday = now - timedelta(days=1)
today = datetime.today()
date_from = today - timedelta(days=31)
date_to = datetime(2025, 1, 1)

data = mt.copy_rates_range(symbol, timeframe, date_from, now)
df = pd.DataFrame(data)
df["time"] = pd.to_datetime(df["time"], unit="s")
df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
df.columns = ["Local time", "Open", "High", "Low", "Close"]


def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


def support(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.Low[i] > df1.Low[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.Low[i] < df1.Low[i - 1]:
            return 0
    return 1


def resistance(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.High[i] < df1.High[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.High[i] > df1.High[i - 1]:
            return 0
    return 1


length = len(df)
Open = list(df["Open"])
High = list(df["High"])
Low = list(df["Low"])
Close = list(df["Close"])
bodydiff = [0] * length
Highdiff = [0] * length
Lowdiff = [0] * length
ratio1 = [0] * length
ratio2 = [0] * length


def isEngulfing(l):

    row = l
    bodydiff[row] = abs(Open[row] - Close[row])
    if bodydiff[row] < 100:
        bodydiff[row] = 100

    bodydiffmin = 300
    if (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and Open[row - 1] < Close[row - 1]
        and Open[row] > Close[row]
        and (Open[row] - Close[row]) >= -1e-2
        and Close[row] < Open[row - 1]
    ):
        return 1
    elif (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and Open[row - 1] > Close[row - 1]
        and Open[row] < Close[row]
        and (Open[row] - Close[row]) <= +1e-2
        and Close[row] > Open[row - 1]
    ):
        return 2
    else:
        return 0


def isStar(l):
    bodydiffmin = 100
    row = l
    Highdiff[row] = High[row] - max(Open[row], Close[row])
    Lowdiff[row] = min(Open[row], Close[row]) - Low[row]
    bodydiff[row] = abs(Open[row] - Close[row])
    if bodydiff[row] < 100:
        bodydiff[row] = 100
    ratio1[row] = Highdiff[row] / bodydiff[row]
    ratio2[row] = Lowdiff[row] / bodydiff[row]

    if (
        ratio1[row] > 1
        and Lowdiff[row] < 0.2 * Highdiff[row]
        and bodydiff[row] > bodydiffmin
    ):
        return 1
    elif (
        ratio2[row] > 1
        and Highdiff[row] < 0.2 * Highdiff[row]
        and bodydiff[row] > bodydiffmin
    ):
        return 2
    else:
        return 0


def CloseResistance(l, levels, lim):
    if len(levels) == 0:
        return 0

    c1 = abs(df.High[l] - min(levels, key=lambda x: abs(x - df.High[l]))) <= lim
    c2 = (
        abs(
            max(df.Open[l], df.Close[l])
            - min(levels, key=lambda x: abs(x - df.High[l]))
        )
        <= lim
    )
    c3 = min(df.Open[l], df.Close[l]) < min(levels, key=lambda x: abs(x - df.High[l]))
    c4 = df.Low[l] < min(levels, key=lambda x: abs(x - df.High[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


def CloseSupport(l, levels, lim):
    if len(levels) == 0:
        return 0

    c1 = abs(df.Low[l] - min(levels, key=lambda x: abs(x - df.Low[l]))) <= lim
    c2 = (
        abs(
            max(df.Open[l], df.Close[l]) - min(levels, key=lambda x: abs(x - df.Low[l]))
        )
        <= lim
    )
    c3 = min(df.Open[l], df.Close[l]) > min(levels, key=lambda x: abs(x - df.Low[l]))
    c4 = df.High[l] > min(levels, key=lambda x: abs(x - df.Low[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


def levelsort(list):

    for i in range(0, len(list) - 1):
        for j in range(0, len(list) - 1 - i):
            if list[j] > list[j + 1]:
                list[j], list[j + 1] = list[j + 1], list[j]

    return list


def levelopt(list):
    for i in range(0, len(list) - 1):
        for j in range(0, len(list) - 1 - i):
            if j >= len(list) - 1 - i:
                break
            if abs(list[j] - list[j + 1]) <= 1e3:
                del list[j]

    return list


n1 = 2
n2 = 2
backCandles = 2
signal = [0] * length


def alert():
    symbol = "Volatility 75 Index"
    timeframe = mt.TIMEFRAME_H1
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    today = datetime.today()
    date_from = today - timedelta(days=31)
    date_to = datetime(2025, 1, 1)

    data = mt.copy_rates_range(symbol, timeframe, date_from, now)
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
    df.columns = ["Local time", "Open", "High", "Low", "Close"]

    df["atr"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)

    for row in range(backCandles, len(df) - n2):
        ss = []
        rr = []

        for subrow in range(row - backCandles + n1, row + 1):
            if support(df, subrow, n1, n2):
                ss.append(df.Low[subrow])
            if resistance(df, subrow, n1, n2):
                rr.append(df.High[subrow])

        ss = levelsort(ss)
        rr = levelsort(rr)
        ss = levelopt(ss)
        rr = levelopt(rr)

        if (isEngulfing(row) == 1 or isStar(row) == 1) and CloseResistance(
            row, rr, 3e3
        ):
            signal[row] = 1
        elif (isEngulfing(row) == 2 or isStar(row) == 2) and CloseSupport(row, ss, 3e3):
            signal[row] = 2
        else:
            signal[row] = 0

    df["signal"] = signal
    # print(df[df["signal"] == 1].count())
    print(df.tail(20))

    latest_close = df.Close.iloc[-1]
    latest_atr = df.atr.iloc[-1]
    SLTPRatio = 1

    if df.iloc[-1]["signal"] == 2:
        sl = round(latest_close - latest_atr, 2)
        tp = round(latest_close + (latest_atr * SLTPRatio), 2)
        msg = str(f"@{symbol}, BUY:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)
        send_alert(msg)

    elif df.iloc[-1]["signal"] == 1:
        sl = round(latest_close + latest_atr, 2)
        tp = round(latest_close - (latest_atr * SLTPRatio), 2)
        msg = str(f"@{symbol}, SELL:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)
        send_alert(msg)


schedule.every().hour.do(alert)

while True:
    try:
        schedule.run_pending()
    except:
        print("*** WAITING FOR A CONNECTION RESTING FOR A MIN... ***")
        time.sleep(60)
