from datetime import datetime, timedelta
import time
import MetaTrader5 as mt
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as ply
import matplotlib.pyplot as plt
import login_info as li
from scipy.stats import linregress

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
timeframe = mt.TIMEFRAME_D1
now = datetime.now()
today = datetime.today()
date_from = datetime(2019, 1, 1)
date_to = datetime(2025, 1, 1)

data = mt.copy_rates_range(symbol, timeframe, date_from, date_to)
df = pd.DataFrame(data)
df["time"] = pd.to_datetime(df["time"], unit="s")
df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)


df["ATR"] = df.ta.atr(length=1)
df["RSI"] = df.ta.rsi()
df["Avg"] = df.ta.midprice(length=1)
df["MA20"] = df.ta.sma(length=20)
df["MA40"] = df.ta.sma(length=40)
df["MA160"] = df.ta.sma(length=160)


def get_slope(array):
    y = np.array(array)
    x = np.arange(len(y))
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    return slope


backrollingN = 6

df["slopeMA20"] = df["MA20"].rolling(window=backrollingN).apply(get_slope, raw=True)
df["slopeMA40"] = df["MA40"].rolling(window=backrollingN).apply(get_slope, raw=True)
df["slopeMA160"] = df["MA160"].rolling(window=backrollingN).apply(get_slope, raw=True)
df["slopeAvg"] = df["Avg"].rolling(window=backrollingN).apply(get_slope, raw=True)
df["slopeRSI"] = df["RSI"].rolling(window=backrollingN).apply(get_slope, raw=True)


tickdiff = 21 * 1e3
RRraito = 3


def mytarget(barsupfront, df1):
    length = len(df1)
    high = list(df["high"])
    low = list(df["low"])
    close = list(df["close"])
    open = list(df["open"])
    trendcat = [None] * length

    for line in range(0, length - barsupfront - 2):
        valOpenLow = 0
        valOpenHigh = 0
        for i in range(1, barsupfront + 2):
            value1 = open[line + 1] - low[line + i]
            value2 = open[line + 1] - high[line + i]
            valOpenLow = max(value1, valOpenLow)
            valOpenHigh = min(value1, valOpenHigh)

            if (valOpenLow >= tickdiff) and (-valOpenHigh <= (tickdiff / RRraito)):
                trendcat[line] = 1  # downtrend
                break
            elif (valOpenLow <= (tickdiff / RRraito)) and (-valOpenHigh >= tickdiff):
                trendcat[line] = 2  # uptrend
                break
            else:
                trendcat[line] = 0  # no clear trend

    return trendcat


df["mytarget"] = mytarget(16, df)

# print(df.tail(10))

fig = plt.figure(figsize=(15, 20))
ax = fig.gca()
df_model = df[
    [
        "ATR",
        "RSI",
        "Avg",
        "MA20",
        "MA40",
        "MA160",
        "slopeMA20",
        "slopeMA40",
        "slopeMA160",
        "slopeAvg",
        "slopeRSI",
        "mytarget",
    ]
]

# df_model.hist(ax=ax)
# plt.show()

df_up = df.RSI[df["mytarget"] == 2]
df_down = df.RSI[df["mytarget"] == 1]
df_unclear = df.RSI[df["mytarget"] == 0]
plt.hist(df_unclear, bins=100, alpha=0.5, label="unclear")
plt.hist(df_down, bins=100, alpha=0.25, label="down")
plt.hist(df_up, bins=100, alpha=0.5, label="up")

plt.legend(loc="upper right")
plt.show()

# buy_wins = len(df[df["mytarget"] == 2])
# sell_wins = len(df[df["mytarget"] == 1])
# no_wins = len(df[df["mytarget"] == 0])
# total_wins = buy_wins + sell_wins + no_wins
# b_perc = round((buy_wins / total_wins) * 100, 2)
# s_perc = round((sell_wins / total_wins) * 100, 2)
# n_perc = round((no_wins / total_wins) * 100, 2)
# print(
#     f"Buys: {buy_wins} %{b_perc}, Sells: {sell_wins} %{s_perc}, None: {no_wins} %{n_perc}"
# )
