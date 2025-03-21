import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest


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
df_test = df.iloc[:]


def SIGNAL():
    return df_test.signal


class MyCandlesStrat(Strategy):
    sltr = 3e3

    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)

    def next(self):
        super().next()
        sltr = self.sltr
        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(trade.sl or -np.inf, self.data.Close[-1] - sltr)
                if self.signal1 == 1:
                    trade.close()
            else:
                trade.sl = min(trade.sl or np.inf, self.data.Close[-1] + sltr)
                if self.signal1 == 2:
                    trade.close()

        if (
            self.signal1 == 2 and len(self.trades) == 0
        ):  # indicates the trade number has changed
            sl1 = self.data.Close[-1] - sltr
            self.buy(sl=sl1, size=1)
        elif (
            self.signal1 == 1 and len(self.trades) == 0
        ):  # indicates the trade number has changed
            sl1 = self.data.Close[-1] + sltr
            self.sell(
                sl=sl1,
                size=1,
            )


bt = Backtest(df_test, MyCandlesStrat, cash=1_000_000, commission=0.001, margin=1)  #
stats = bt.run()
print(stats)

bt.plot(show_legend=False)
