import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest


df = pd.read_csv("trading_bots\\v75_H_1_2019-2025.csv")


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


length = len(df)
open = list(df["open"])
high = list(df["high"])
low = list(df["low"])
close = list(df["close"])
bodydiff = [0] * length
highdiff = [0] * length
lowdiff = [0] * length
ratio1 = [0] * length
ratio2 = [0] * length


def isEngulfing(l):

    row = l
    bodydiff[row] = abs(open[row] - close[row])
    if bodydiff[row] < 100:
        bodydiff[row] = 100

    bodydiffmin = 300
    if (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] < close[row - 1]
        and open[row] > close[row]
        and (open[row] - close[row]) >= -1e-2
        and close[row] < open[row - 1]
    ):
        return 1
    elif (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and open[row - 1] > close[row - 1]
        and open[row] < close[row]
        and (open[row] - close[row]) <= +1e-2
        and close[row] > open[row - 1]
    ):
        return 2
    else:
        return 0


def isStar(l):
    bodydiffmin = 100
    row = l
    highdiff[row] = high[row] - max(open[row], close[row])
    lowdiff[row] = min(open[row], close[row]) - low[row]
    bodydiff[row] = abs(open[row] - close[row])
    if bodydiff[row] < 100:
        bodydiff[row] = 100
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
        and highdiff[row] < 0.2 * highdiff[row]
        and bodydiff[row] > bodydiffmin
    ):
        return 2
    else:
        return 0


def closeResistance(l, levels, lim):
    if len(levels) == 0:
        return 0

    c1 = abs(df.high[l] - min(levels, key=lambda x: abs(x - df.high[l]))) <= lim
    c2 = (
        abs(
            max(df.open[l], df.close[l])
            - min(levels, key=lambda x: abs(x - df.high[l]))
        )
        <= lim
    )
    c3 = min(df.open[l], df.close[l]) < min(levels, key=lambda x: abs(x - df.high[l]))
    c4 = df.low[l] < min(levels, key=lambda x: abs(x - df.high[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


def closeSupport(l, levels, lim):
    if len(levels) == 0:
        return 0

    c1 = abs(df.low[l] - min(levels, key=lambda x: abs(x - df.low[l]))) <= lim
    c2 = (
        abs(
            max(df.open[l], df.close[l]) - min(levels, key=lambda x: abs(x - df.low[l]))
        )
        <= lim
    )
    c3 = min(df.open[l], df.close[l]) > min(levels, key=lambda x: abs(x - df.low[l]))
    c4 = df.high[l] > min(levels, key=lambda x: abs(x - df.low[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


n1 = 2
n2 = 2
backCandles = 2
signal = [0] * length

for row in range(backCandles, len(df) - n2):
    ss = []
    rr = []

    for subrow in range(row - backCandles + n1, row + 1):
        if support(df, subrow, n1, n2):
            ss.append(df.low[subrow])
        if resistance(df, subrow, n1, n2):
            rr.append(df.high[subrow])

    if (isEngulfing(row) == 1 or isStar(row) == 1) and closeResistance(row, rr, 3e3):
        signal[row] = 1
    elif (isEngulfing(row) == 2 or isStar(row) == 2) and closeSupport(row, ss, 3e3):
        signal[row] = 2
    else:
        signal[row] = 0


df["signal"] = signal

# print(df[df["signal"] == 1].count())
# print(df[df["signal"] == 2].count())

RRRatio = 1  # 2
df.columns = ["Local Time", "Open", "High", "Low", "Close", "signal"]
# print(df)
df = df.iloc[:]


def SIGNAL():
    return df.signal


class MyCandlesStrat(Strategy):
    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)

    def next(self):
        super().next()
        if self.signal1 == 2:
            sl1 = self.data.Close[-1] - 7e3
            tp1 = self.data.Close[-1] + 7e3
            self.buy(sl=sl1, tp=tp1, size=0.001)
        elif self.signal1 == 1:
            sl1 = self.data.Close[-1] + 7e3
            tp1 = self.data.Close[-1] - 7e3
            self.sell(sl=sl1, tp=tp1, size=0.001)


bt = Backtest(df, MyCandlesStrat, cash=1_000_000, commission=0.002, margin=0.000001)
stats = bt.run()
# print(stats)


def mytarget(barsupfront, df1):

    length = len(df1)
    high = list(df1["high"])
    low = list(df1["low"])
    open = list(df1["open"])
    close = list(df1["close"])
    signal = list(df1["signal"])
    trendcat = [0] * length
    amount = [0] * length

    SL = 0
    TP = 0
    for line in range(backCandles, length - barsupfront - n2):

        if signal[line] == 1:
            SL = max(high[line - 1 : line + 1])
            TP = close[line] - RRRatio * (SL - close[line])

            for i in range(1, barsupfront + 1):
                if low[line + i] <= TP and high[line + i] >= SL:
                    trendcat[line] = 3
                    break
                elif low[line + i] <= TP:
                    trendcat[line] = 1
                    amount[line] = close[line] - low[line + i]
                    break
                elif high[line + i] >= SL:
                    trendcat[line] = 2
                    amount[line] = close[line] - high[line + i]
                    break

        elif signal[line] == 2:
            SL = min(low[line - 1 : line + 1])
            TP = close[line] + (RRRatio * (close[line] - SL))

            for i in range(1, barsupfront + 1):
                if high[line + i] >= TP and low[line + i] <= SL:
                    trendcat[line] = 3
                    break
                elif high[line + i] >= TP:
                    trendcat[line] = 2
                    amount[line] = high[line + i] - close[line]
                    break
                elif low[line + i] <= SL:
                    trendcat[line] = 1
                    amount[line] = low[line + i] - close[line]
                    break

    return trendcat, amount


# df["trend"] = mytarget(16, df)[0]
# df["amount"] = mytarget(16, df)[1]


# df[df["amount"] != 0]
# print(f"For RR: {RRRatio} P&L/y = ${df["amount"].sum() / 6:,.2f}")
# conditions = [
#     (df["trend"] == 1) & (df["signal"] == 1),
#     (df["trend"] == 2) & (df["signal"] == 2),
# ]
# values = [1, 2]
# df["result"] = np.select(conditions, values)


# trendId = 1
# print(
#     df[df["result"] == trendId].result.count()
#     / df[df["signal"] == trendId].signal.count()
# )
# trendId = 2
# print(
#     df[df["result"] == trendId].result.count()
#     / df[df["signal"] == trendId].signal.count()
# )
# print(df[(df["trend"] != trendId) & (df["trend"] != 3) & (df["signal"] == trendId)])
# s, e = 0, 200
# dfpl = df[s:e]

# fig = go.Figure(
#     data=[
#         go.Candlestick(
#             x=dfpl.index,
#             open=dfpl["open"],
#             high=dfpl["high"],
#             low=dfpl["low"],
#             close=dfpl["close"],
#         )
#     ]
# )

# fig.show()
# print(df)
