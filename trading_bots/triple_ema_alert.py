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


#!!! Determines if the signal conditions are met
def mysig(x):
    if x.ma20 < x.ma30 < x.ma60:
        return -1
    elif x.ma20 > x.ma30 > x.ma60:
        return 1
    else:
        return 0


if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")


def send_alert(msg):
    payload = {"content": msg}
    response = requests.post(di.URL, payload, headers=di.headers)


def alert():
    symbol = "Volatility 75 Index"
    timeframe = mt.TIMEFRAME_M1
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    today = datetime.today()
    date_from = today - timedelta(days=12)
    date_to = datetime(2025, 1, 1)

    data = mt.copy_rates_range(symbol, timeframe, yesterday, now)
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
    df.columns = ["Local time", "Open", "High", "Low", "Close"]

    df["atr"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
    df["ma20"] = ta.ema(df.Close, length=20)
    df["ma30"] = ta.ema(df.Close, length=30)
    df["ma60"] = ta.ema(df.Close, length=60)

    df["signal"] = df.apply(mysig, axis=1)

    latest_close = df.Close.iloc[-1]
    latest_atr = df.atr.iloc[-1]
    SLTPRatio = 1

    # 1 = BUY, -1 = SELL
    if df.iloc[-1]["signal"] == 1 and df.iloc[-2]["signal"] != 1:
        sl = round(latest_close - latest_atr, 2)
        tp = round(latest_close + (latest_atr * SLTPRatio), 2)
        msg = str(f"@{symbol}, BUY:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)
        send_alert(msg)

    elif df.iloc[-1]["signal"] == -1 and df.iloc[-2]["signal"] != -1:
        sl = round(latest_close + latest_atr, 2)
        tp = round(latest_close - (latest_atr * SLTPRatio), 2)
        msg = str(f"@{symbol}, SELL:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)
        send_alert(msg)


# scheduler = BlockingScheduler(job_defaults={"misfire_grace_time": 15 * 60})
# scheduler.add_job(alert, "cron", minute=5)
# scheduler.start()


# different scheduler

schedule.every(1).minutes.do(alert)

while True:
    try:
        schedule.run_pending()
    except:
        print("*** WAITING FOR A CONNECTION RESTING FOR A MIN... ***")
        time.sleep(60)
