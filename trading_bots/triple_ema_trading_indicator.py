import json
import smtplib
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest
from apscheduler.schedulers.blocking import BlockingScheduler
import email_info as ei

# Reads csv and coverts it pandas dataframe/df
# df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")

# # Implements the MAs into the df
# df["ma20"] = ta.ema(df.Close, length=20)
# df["ma30"] = ta.ema(df.Close, length=30)
# df["ma60"] = ta.ema(df.Close, length=60)

# # print(df.tail(20))


# #!!! Determines if the signal conditions are met
def mysig(x):
    if x.ma20 < x.ma30 < x.ma60:
        return -1
    elif x.ma20 > x.ma30 > x.ma60:
        return 1
    else:
        return 0


# # Adds a signal column using the result from the function
# df["signal"] = df.apply(mysig, axis=1)

# dfpl = df[100:1000]

# # draws the figure
# fig = go.Figure(
#     data=[
#         go.Candlestick(
#             x=dfpl.index,
#             open=dfpl["Open"],
#             high=dfpl["High"],
#             low=dfpl["Low"],
#             close=dfpl["Close"],
#         ),
#         go.Scatter(
#             x=dfpl.index, y=dfpl.ma20, line=dict(color="green", width=1), name="EMA20"
#         ),
#         go.Scatter(
#             x=dfpl.index, y=dfpl.ma30, line=dict(color="blue", width=2), name="EMA30"
#         ),
#         go.Scatter(
#             x=dfpl.index, y=dfpl.ma60, line=dict(color="purple", width=3), name="EMA60"
#         ),
#     ]
# )
# fig.add_scatter(x=dfpl.index, y=dfpl["pointpos"], mode="markers", marker=dict(size=5, color="yellow", name="pivot"))
# fig.update_layout(xaxis_rangeslider_visible=False)

# fig.show()


gmail_user = ei.email
gmail_password = ei.password
sent_from = gmail_user
to = [ei.email]
subject = "info signal"

import MetaTrader5 as mt
import login_info as li

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
    df_live = pd.DataFrame(data)
    df_live["time"] = pd.to_datetime(df_live["time"], unit="s")
    df_live.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
    df_live.columns = ["Local time", "Open", "High", "Low", "Close"]

    df_live["ma20"] = ta.ema(df_live.Close, length=20)
    df_live["ma30"] = ta.ema(df_live.Close, length=30)
    df_live["ma60"] = ta.ema(df_live.Close, length=60)

    df_live["signal"] = df_live.apply(mysig, axis=1)

    if df_live.iloc[-1]["signal"] == 1 and df_live.iloc[-2]["signal"] != 1:
        msg = str(f"SELL {df_live.Close.iloc[-1]}")
        print(msg)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, msg)
        server.close()
    elif df_live.iloc[-1]["signal"] == -1 and df_live.iloc[-2]["signal"] != -1:
        msg = str(f"BUY {df_live.Close.iloc[-1]}")
        print(msg)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, msg)
        server.close()


scheduler = BlockingScheduler(job_defaults={"misfire_grace_time": 15 * 60})
scheduler.add_job(alert, "cron", hour="*/1", minute=5)
scheduler.start()
