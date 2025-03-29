import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest


df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")

ma_length = 101

df["atr"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
df["ma"] = ta.sma(df.Close, length=ma_length)


#!!! Determines if candles are above or below the MA's curve
def MAsig(df1, l, backcandles):
    sigup = 2
    sigdn = 1
    for i in range(l - backcandles, l + 1):
        if df1.Low[i] <= df1.ma[i]:
            sigup = 0
        if df1.High[i] >= df1.ma[i]:
            sigdn = 0

    if sigup:
        return sigup
    elif sigdn:
        return sigdn
    else:
        return 0


# Plots chart with MA
# dfpl = df[120:300]
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
#             x=dfpl.index, y=dfpl.ma, line=dict(color="DarkBlue", width=1), name="MA"
#         ),
#     ]
# )
# fig.show()

MAbackcandles = 9

# Applies the signal to the df
MAsignal = [0] * len(df)
for row in range(MAbackcandles, len(df)):
    MAsignal[row] = MAsig(df, row, MAbackcandles)

df["MAsignal"] = MAsignal
# print(df[122:150])

HLbc = 9

df["mins"] = df["Low"].rolling(window=HLbc).min()
df["maxs"] = df["High"].rolling(window=HLbc).max()


def HLsig(x):
    if x.MAsignal == 1 and x.High >= x.maxs:
        return 1
    if x.MAsignal == 2 and x.Low <= x.mins:
        return 2
    else:
        return 0


df["HLsig"] = df.apply(HLsig, axis=1)

# print(df[df["HLsig"] == 2].count())


def pointpos(x):
    if x["HLsig"] == 1:
        return x["High"] + 1e3
    elif x["HLsig"] == 2:
        return x["Low"] - 1e3
    else:
        return np.nan


df["pointpos"] = df.apply(lambda row: pointpos(row), axis=1)

# Plots chart with MA and points
dfpl = df[444:950]
fig = go.Figure(
    data=[
        go.Candlestick(
            x=dfpl.index,
            open=dfpl["Open"],
            high=dfpl["High"],
            low=dfpl["Low"],
            close=dfpl["Close"],
        ),
        go.Scatter(
            x=dfpl.index, y=dfpl.ma, line=dict(color="DarkBlue", width=1), name="MA"
        ),
    ]
)
fig.add_scatter(
    x=dfpl.index,
    y=dfpl["pointpos"],
    mode="markers",
    marker=dict(color="purple", size=6),
    name="Sig",
)
fig.show()
