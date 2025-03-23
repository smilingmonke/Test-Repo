import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pandas_ta as ta
from apscheduler.schedulers.blocking import BlockingScheduler
import MetaTrader5 as mt
import login_info as li
import discord
from discord.ext import commands
import discord_bot_info as dbi

BOT_TOKEN = dbi.TOKEN
CHANNEL_ID = dbi.CHANNEL_ID
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())


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


def alert():
    symbol = "Volatility 75 Index"
    timeframe = mt.TIMEFRAME_H1
    now = datetime.now()
    today = datetime.today()
    date_from = today - timedelta(days=12)
    date_to = datetime(2025, 1, 1)

    data = mt.copy_rates_range(symbol, timeframe, date_from, now)
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

    if df.iloc[-1]["signal"] == 1 and df.iloc[-2]["signal"] != 1:
        sl = latest_close + latest_atr
        tp = latest_close - (latest_atr * SLTPRatio)
        msg = str(f"@{symbol}, SELL:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)

        @bot.event
        async def on_ready():

            channel = bot.get_channel(CHANNEL_ID)
            await channel.send(msg)

        bot.run(BOT_TOKEN)

    elif df.iloc[-1]["signal"] == -1 and df.iloc[-2]["signal"] != -1:
        sl = latest_close - latest_atr
        tp = latest_close + (latest_atr * SLTPRatio)
        msg = str(f"@{symbol}, BUY:{df.Close.iloc[-1]} SL:{sl}, TP:{tp}")
        print(msg)

        @bot.event
        async def on_ready():

            channel = bot.get_channel(CHANNEL_ID)
            await channel.send(msg)

        bot.run(BOT_TOKEN)


scheduler = BlockingScheduler(job_defaults={"misfire_grace_time": 15 * 60})
scheduler.add_job(alert, "cron", hour="*/1", minute=5)
scheduler.start()
