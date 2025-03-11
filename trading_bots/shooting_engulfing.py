import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

df = pd.read_csv("trading_bots\\v75_M_15_2023-2025.csv")

df["atr"] = df.ta.atr(length=1)
df["rsi"] = df.ta.rsi()
df["atr_avg"] = df["atr"].rolling(window=48).mean()
# print(df.tail())

length = len(df)
high = list(df["high"])
low = list(df["low"])
close = list(df["close"])
open = list(df["open"])
bodydiff = [0] * length

highdiff = [0] * length
lowdiff = [0] * length
ratio1 = [0] * length
ratio2 = [0] * length


def isEngulfing(l):
    row = l
    bodydiff[row] = abs(open[row] - close[row])
    if bodydiff[row] < 1:
        bodydiff[row] = 1

    bodydiffmin = 1e2
    if (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] < close[row - 1]
        and open[row] > close[row]
        and (open[row] - close[row]) >= 1e2
        and close[row] < open[row - 1]
    ):
        return 1
    elif (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] > close[row - 1]
        and open[row] < close[row]
        and (open[row] - close[row]) <= -1e2
        and close[row] > open[row - 1]
    ):
        return 2
    else:
        return 0


def isEngulfingStrong(l):
    row = l
    bodydiff[row] = abs(open[row] - close[row])
    if bodydiff[row] < 1.0:
        bodydiff[row] = 1.0

    bodydiffmin = 1e2
    if (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] < close[row - 1]
        and open[row] > close[row]
        and (open[row] - close[row - 1]) >= 1e2
        and close[row] < low[row - 1]
    ):
        return 1
    elif (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] > close[row - 1]
        and open[row] < close[row]
        and (open[row] - close[row - 1]) <= -1e2
        and close[row] > high[row - 1]
    ):
        return 2
    else:
        return 0


def isStar(l):
    bodydiffmin = 1e2

    row = l

    highdiff[row] = high[row] - max(open[row], close[row])
    lowdiff[row] = min(open[row], close[row]) - low[row]
    bodydiff[row] = abs(open[row] - close[row])

    if bodydiff[row] < 1:
        bodydiff[row] = 1

    ratio1[row] = highdiff[row] / bodydiff[row]
    ratio2[row] = lowdiff[row] / bodydiff[row]

    if (
        ratio1[row] > 1
        and lowdiff[row] < 0.2 * highdiff[row]
        and bodydiff[row] > bodydiffmin
    ):
        return 1
    elif (
        ratio2[row] > 1
        and highdiff[row] < 0.2 * lowdiff[row]
        and bodydiff[row] > bodydiffmin
    ):
        return 2
    else:
        return 0


def direction(l):
    if open[l] > close[l]:
        return 1
    elif open[l] < close[l]:
        return 2
    else:
        return 0


# identifying the candle signal


def Revsignal1():
    signal = [0] * length

    for row in range(1, length):

        if isEngulfing(row) == 1 or isStar(row) == 1:  # and df.rsi[row] < 30
            signal[row] = 1
        elif (
            isEngulfing(row) == 2 or isStar(row) == 2
        ):  #  df.atr[row] > df.atr_avg[row] and df.rsi[row] > 70
            signal[row] = 2
        else:
            signal[row] = 0

    return signal


df["signal"] = Revsignal1()

# print(df[df["signal"] == 1].count())


def mytarget(df1, barsupfront):
    length = len(df1)
    high = list(df1["high"])
    low = list(df1["low"])
    close = list(df1["close"])
    open = list(df1["open"])
    trendcat = [None] * length

    ticklim = 1e3
    for line in range(0, length - 1 - barsupfront):
        for i in range(1, barsupfront + 1):
            if ((high[line + i] - close[line]) > ticklim) and (
                (close[line] - low[line + i]) > ticklim
            ):
                trendcat[line] = 3  # no trend
                break
            elif (close[line] - low[line + i]) > ticklim:
                trendcat[line] = 1  # -1 downtrend
                break
            elif (high[line + i] - close[line]) > ticklim:
                trendcat[line] = 2  # uptrend
                break
            else:
                trendcat[line] = 0  # no clear trend
    return trendcat


df["trend"] = mytarget(df, 10)
# print(df.head(30))

conditions = [
    (df["trend"] == 1) & (df["signal"] == 1),
    (df["trend"] == 2) & (df["signal"] == 2),
]  # | (df["trend"] == 3)
values = [1, 2]
df["result"] = np.select(conditions, values)
trendId = 2
print(
    f"For Id= {trendId}  {df[df["result"] == trendId].result.count() / df[df["signal"] == trendId].signal.count()}"
)
# print(
#     df[(df["result"] != trendId) & (df["signal"] == trendId)].head(10)
# )  # false positives

dfpl = df[50:100]

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

# fig.show()
