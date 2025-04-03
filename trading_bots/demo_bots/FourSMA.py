import requests
import MetaTrader5 as mt
import login_info as li
from datetime import datetime, timedelta
import pandas_ta as ta
import time
import pandas as pd
import schedule
import discord_info as di


#!!! Determines whether the SMA signal is valid
def SMASignal(x):
    if x.MA10 < x.MA20 < x.MA100 < x.MA200:
        return -1
    elif x.MA10 > x.MA20 > x.MA100 > x.MA200:
        return 1
    else:
        return 0


#!!! Discord message
def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


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

# Indicators
df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.CLos, length=14)
df["MA10"] = ta.sma(close=df.CLose, length=10)
df["MA20"] = ta.sma(close=df.CLose, length=20)
df["MA100"] = ta.sma(close=df.CLose, length=100)
df["MA200"] = ta.sma(close=df.CLose, length=200)

df["SMAsig"] = df.apply(SMASignal, axis=1)
