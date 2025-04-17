import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest


df = pd.read_csv("trading_bots\\CSV\\EURUSD_H_1_2019-2025.csv")

ma_length = 200
# ma_length = 100 5497 signals
# ma_length = 200 7314 signals
df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
df["SMA"] = ta.sma(df.Close, length=ma_length)


#!!! Determines if candles are above or below the SMA's curve
def MAsig(df1, l, backcandles):
    sigup = 2
    sigdn = 1
    for i in range(l - backcandles, l + 1):
        if df1.Low[i] <= df1.SMA[i]:
            sigup = 0
        if df1.High[i] >= df1.SMA[i]:
            sigdn = 0

    if sigup:
        return sigup
    elif sigdn:
        return sigdn
    else:
        return 0


# Plots chart with SMA
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
#             x=dfpl.index, y=dfpl.SMA, line=dict(color="DarkBlue", width=1), name="SMA"
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

HLBackCandles = 9

df["mins"] = df["Low"].rolling(window=HLBackCandles).min()
df["maxs"] = df["High"].rolling(window=HLBackCandles).max()


def HLSignal(x):
    if x.MAsignal == 1 and x.High >= x.maxs:
        return 1
    if x.MAsignal == 2 and x.Low <= x.mins:
        return 2
    else:
        return 0


df["HLSignal"] = df.apply(HLSignal, axis=1)

print(df[df["HLSignal"] == 2].count())
print(df[df["HLSignal"] == 1].count())


def pointpos(x):
    if x["HLSignal"] == 1:
        return x["High"] + 1e3
    elif x["HLSignal"] == 2:
        return x["Low"] - 1e3
    else:
        return np.nan


df["pointpos"] = df.apply(lambda row: pointpos(row), axis=1)

# Plots chart with SMA and points
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
            x=dfpl.index, y=dfpl.SMA, line=dict(color="DarkBlue", width=1), name="SMA"
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
# fig.show()


def SIGNAL():
    return df.HLSignal


# ATR Trailing SL


class MyStrat(Strategy):
    atr_f = 1.0

    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)

    def next(self):
        super().next()
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

        if self.signal1 == 2 and len(self.trades) <= 0:  # trades number change!
            sl1 = self.data.Close[-1] - self.data.ATR[-1] / self.atr_f
            self.buy(sl=sl1)
        elif self.signal1 == 1 and len(self.trades) <= 0:  # trades number change!
            sl1 = self.data.Close[-1] + self.data.ATR[-1] / self.atr_f
            self.sell(sl=sl1)


# ATR Fixed SL & TP
# class MyStrat(Strategy):
#     atr_f = 0.5
#     TPSLR = 2.0

#     def init(self):
#         super().init()
#         self.signal1 = self.I(SIGNAL)

#     def next(self):
#         super().next()

#         if self.signal1 == 2:
#             sl1 = self.data.Close[-1] - self.data.ATR[-1] / self.atr_f
#             tp1 = self.data.Close[-1] + self.data.ATR[-1] * self.TPSLR / self.atr_f
#             self.buy(sl=sl1, tp=tp1)
#         elif self.signal1 == 1:
#             sl1 = self.data.Close[-1] + self.data.ATR[-1] / self.atr_f
#             tp1 = self.data.Close[-1] - self.data.ATR[-1] * self.TPSLR / self.atr_f
#             self.sell(sl=sl1, tp=tp1)


# print(df)
bt = Backtest(df, MyStrat, cash=10_000_000_000, commission=0.0, margin=0.001)
stats = bt.run()
print(stats)
# bt.plot()
