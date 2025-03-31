import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest

# Reads csv and coverts it pandas dataframe/df
df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")

# Adds the atr indicator to the df
df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)

# Prints the last x amount of rows of the df
# print(df.tail(20))


#!!! Support and Resistance functions
def support(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.Low[i] > df1.Low[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.Low[i] < df1.Low[i - 1]:
            return 0
    return 1


def resistance(df1, l, n1, n2):
    for i in range(l - n1 + 1, l + 1):
        if df1.High[i] < df1.High[i - 1]:
            return 0

    for i in range(l + 1, l + n2 + 1):
        if df1.High[i] > df1.High[i - 1]:
            return 0
    return 1


length = len(df)
Open = list(df["Open"])
High = list(df["High"])
Low = list(df["Low"])
Close = list(df["Close"])
bodydiff = [0] * length
highdiff = [0] * length
lowdiff = [0] * length
ratio1 = [0] * length
ratio2 = [0] * length


def isEngulfing(l):

    row = l
    bodydiff[row] = abs(Open[row] - Close[row])
    if bodydiff[row] < 100:
        bodydiff[row] = 100

    bodydiffmin = 300
    if (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and Open[row - 1] < Close[row - 1]
        and Open[row] > Close[row]
        and (Open[row] - Close[row]) >= -1e-2
        and Close[row] < Open[row - 1]
    ):
        return 1
    elif (
        bodydiff[row] > bodydiffmin
        and bodydiff[row - 1] > bodydiffmin
        and Open[row - 1] > Close[row - 1]
        and Open[row] < Close[row]
        and (Open[row] - Close[row]) <= +1e-2
        and Close[row] > Open[row - 1]
    ):
        return 2
    else:
        return 0


def isStar(l):
    bodydiffmin = 100
    row = l
    highdiff[row] = High[row] - max(Open[row], Close[row])
    lowdiff[row] = min(Open[row], Close[row]) - Low[row]
    bodydiff[row] = abs(Open[row] - Close[row])
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

    c1 = abs(df.High[l] - min(levels, key=lambda x: abs(x - df.High[l]))) <= lim
    c2 = (
        abs(
            max(df.Open[l], df.Close[l])
            - min(levels, key=lambda x: abs(x - df.High[l]))
        )
        <= lim
    )
    c3 = min(df.Open[l], df.Close[l]) < min(levels, key=lambda x: abs(x - df.High[l]))
    c4 = df.Low[l] < min(levels, key=lambda x: abs(x - df.High[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


def closeSupport(l, levels, lim):
    if len(levels) == 0:
        return 0

    c1 = abs(df.Low[l] - min(levels, key=lambda x: abs(x - df.Low[l]))) <= lim
    c2 = (
        abs(
            max(df.Open[l], df.Close[l]) - min(levels, key=lambda x: abs(x - df.Low[l]))
        )
        <= lim
    )
    c3 = min(df.Open[l], df.Close[l]) > min(levels, key=lambda x: abs(x - df.Low[l]))
    c4 = df.High[l] > min(levels, key=lambda x: abs(x - df.Low[l]))

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
            ss.append(df.Low[subrow])
        if resistance(df, subrow, n1, n2):
            rr.append(df.High[subrow])

    if (isEngulfing(row) == 1 or isStar(row) == 1) and closeResistance(row, rr, 3e3):
        signal[row] = 1
    elif (isEngulfing(row) == 2 or isStar(row) == 2) and closeSupport(row, ss, 3e3):
        signal[row] = 2
    else:
        signal[row] = 0


df["signal"] = signal
# print(f"1:{df[df["signal"] == 1].count()} \n2:{df[df["signal"] == 2].count()}")

df.columns = ["Local time", "Open", "High", "Low", "Close", "ATR", "signal"]


def SIGNAL():
    return df.signal


def ATR():
    return df.ATR


#!!!!!!! Fixed sl and tp return %171
# class MyCandlesStrat(Strategy):
#     def init(self):
#         super().init()
#         self.signal1 = self.I(SIGNAL)

#     def next(self):
#         super().next()
#         if self.signal1 == 2:
#             sl1 = self.data.Close[-1] - 9e3
#             tp1 = self.data.Close[-1] + 9.9e3
#             self.buy(sl=sl1, tp=tp1)
#         elif self.signal1 == 1:
#             sl1 = self.data.Close[-1] + 9e3
#             tp1 = self.data.Close[-1] - 9.9e3
#             self.sell(sl=sl1, tp=tp1)


#!!!!!!! atr sl and tp return %1158
class ATRFixed(Strategy):
    atr_f = 1
    ratio_f = 1.5

    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)
        self.atr1 = self.I(ATR)

    def next(self):
        super().next()
        if self.signal1 == 2:
            sl1 = self.data.Close[-1] - self.data.ATR[-1] / self.atr_f
            tp1 = self.data.Close[-1] + self.data.ATR[-1] * self.ratio_f / self.atr_f
            self.buy(sl=sl1, tp=tp1)
        elif self.signal1 == 1:
            sl1 = self.data.Close[-1] + self.data.ATR[-1] / self.atr_f
            tp1 = self.data.Close[-1] - self.data.ATR[-1] * self.ratio_f / self.atr_f
            self.sell(sl=sl1, tp=tp1)


#!!!!!!! fixed sl and tp with trailing stop return %439 w/ no limit on trades %388 w/ limit on number of trades
# class MyCandlesStrat(Strategy):
#     sltr = 9e3

#     def init(self):
#         super().init()
#         self.signal1 = self.I(SIGNAL)

#     def next(self):
#         super().next()
#         sltr = self.sltr
#         for trade in self.trades:
#             if trade.is_long:
#                 trade.sl = max(trade.sl or -np.inf, self.data.Close[-1] - sltr)
#             else:
#                 trade.sl = min(trade.sl or np.inf, self.data.Close[-1] + sltr)

#         if self.signal1 == 2:  # and len(self.trades) == 0
#             sl1 = self.data.Close[-1] - sltr
#             self.buy(sl=sl1)
#         elif self.signal1 == 1:  # and len(self.trades) == 0
#             sl1 = self.data.Close[-1] + sltr
#             self.sell(sl=sl1)


#!!!!!!! atr sl with trailing stop
class MyCandlesStrat(Strategy):
    atr_f = 1

    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)
        self.atr1 = self.I(ATR)
        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(
                    trade.sl or -np.inf,
                    self.data.Close[-1] - self.data.ATR[-1] / self.atr_f,
                )
            else:
                trade.sl = min(
                    trade.sl or np.inf,
                    self.data.Close[-1] + self.data.ATR[-1] / self.atr_f,
                )

    def next(self):
        super().next()
        if self.signal1 == 2:  # and len(self.trades) == 0
            sl1 = self.data.Close[-1] - self.data.ATR[-1] / self.atr_f
            self.buy(sl=sl1)
        elif self.signal1 == 1:  # and len(self.trades) == 0
            sl1 = self.data.Close[-1] + self.data.ATR[-1] / self.atr_f
            self.sell(sl=sl1)


bt = Backtest(df, ATRFixed, cash=100_000_000, commission=0.0, margin=1)
stats = bt.run()
print(stats)
# print(df)
