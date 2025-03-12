import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt

df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")


def support(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.low[i] > df1.low[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.low[i] < df1.low[i - 1]:
            return 0
    return 1


def resistance(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.high[i] < df1.high[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.high[i] > df1.high[i - 1]:
            return 0

    return 1


n1 = 2
n2 = 2
ss = []
rr = []

for row in range(n1, len(df) - n2):
    if support(df, row, n1, n2):
        ss.append((row, df.low[row]))
    if resistance(df, row, n1, n2):
        rr.append((row, df.high[row]))


for i in range(0, len(ss) - 1):
    for j in range(0, len(ss) - 1 - i):
        if ss[j][1] > ss[j + 1][1]:
            ss[j], ss[j + 1] = ss[j + 1], ss[j]

for i in range(0, len(rr) - 1):
    for j in range(0, len(rr) - 1 - i):
        if rr[j][1] > rr[j + 1][1]:
            rr[j], rr[j + 1] = rr[j + 1], rr[j]

for i in range(0, len(ss) - 1):
    for j in range(0, len(ss) - 1 - i):
        if j >= len(ss) - 1 - i:
            break
        if abs(ss[j][1] - ss[j + 1][1]) <= 3e4:
            del ss[j]

for i in range(0, len(rr) - 1):
    for j in range(0, len(rr) - 1 - i):
        if j >= len(rr) - 1 - i:
            break
        if abs(rr[j][1] - rr[j + 1][1]) <= 3e4:
            del rr[j]


s = 0
e = len(df)
dfpl = df[s:e]

fig = go.Figure(
    data=[
        go.Candlestick(
            x=dfpl.index,
            open=dfpl["open"],
            high=dfpl["high"],
            low=dfpl["low"],
            close=dfpl["close"],
        )
    ]
)

c = 0
while 1:
    if c > len(ss) - 1:
        break
    fig.add_shape(
        type="line",
        x0=ss[c][0] - 3,
        y0=ss[c][1],
        x1=e,
        y1=ss[c][1],
        line=dict(color="Purple", width=3),
    )
    c += 1

c = 0
while 1:
    if c > len(rr) - 1:
        break
    fig.add_shape(
        type="line",
        x0=rr[c][0] - 3,
        y0=rr[c][1],
        x1=e,
        y1=rr[c][1],
        line=dict(color="RoyalBlue", width=2),
    )
    c += 1

fig.show()
