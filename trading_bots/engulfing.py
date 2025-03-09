import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")


# Identify engulfing pattern
def Revsignal1(df1):
    length = len(df1)
    high = list(df["high"])
    low = list(df["low"])
    close = list(df["close"])
    open = list(df["open"])
    signal = [0] * length
    bodydiff = [0] * length

    for row in range(1, length):
        bodydiff[row] = abs(open[row] - close[row])
        bodydiffmin = 100

        if (
            bodydiff[row] > bodydiffmin
            and bodydiff[row - 1] > bodydiffmin
            and open[row - 1] < close[row - 1]
            and open[row] > close[row]
            and (open[row] - close[row]) >= +1000
            and close[row] < open[row - 1]
        ):
            signal[row] = 1
        elif (
            bodydiff[row] > bodydiffmin
            and bodydiff[row - 1] > bodydiffmin
            and open[row - 1] > close[row - 1]
            and open[row] < close[row]
            and (open[row] - close[row]) <= -1000
            and close[row] > open[row - 1]
        ):
            signal[row] = 2
        else:
            signal[row] = 0

    return signal


df["signal1"] = Revsignal1(df)
# print(df[df["signal1"] == 2].count())


def mytarget(barsupfront, df1):
    length = len(df1)
    high = list(df["high"])
    low = list(df["low"])
    close = list(df["close"])
    open = list(df["open"])
    trendcat = [None] * length

    ticklim = 7000

    for line in range(0, length - 1 - barsupfront):
        for i in range(1, barsupfront + 1):
            if (high[line + i] - max(close[line], open[line])) > ticklim and (
                min(close[line], open[line]) - low[line + i]
            ) > ticklim:
                trendcat[line] = 3  # no trend
            elif (min(close[line], open[line]) - low[line + i]) > ticklim:
                trendcat[line] = 1  # downtrend
                break
            elif (high[line + i] - max(close[line], open[line])) > ticklim:
                trendcat[line] = 2  # uptrend
                break
            else:
                trendcat[line] = 0  # no clear trend

    return trendcat


df["trend"] = mytarget(3, df)

conditions = [
    (df["trend"] == 1) & (df["signal1"] == 1),
    (df["trend"] == 2) & (df["signal1"] == 2),
]
values = [1, 2]
df["result"] = np.select(conditions, values)

trendId = 1
print(
    f"For Id={trendId} %{df[df["result"] == trendId].result.count() / df[df["signal1"] == trendId].signal1.count()}"
)
# print(
#     df[(df["result"] != trendId) & (df["signal1"] == trendId)].head(10)
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
