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
df["atr"] = ta.atr(high=df.high, low=df.low, close=df.close, length=14)

# Prints the last x amount of rows of the df
# print(df.tail(20))


#!!! Support and Resistance functions
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


# Takes the values of df a puts them into separate lists
length = len(df)
high = list(df["high"])
low = list(df["low"])
close = list(df["close"])
open = list(df["open"])
bodydiff = [0] * length

# Defines varibles which will be used in the following functions
highdiff = [0] * length
lowdiff = [0] * length
ratio1 = [0] * length
ratio2 = [0] * length

# Volatility 75 set
mybodydiff = 1
mybodydiffmin = 3e2


#!!! Engulfing bar pattern function
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


#!!! Shooting star bar pattern function
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


#!!! Determines if a candle is close to a Resistance level
def closeResistance(l, levels, lim):
    if len(levels) == 0:
        return 0

    # lim = df.atr[l]/2

    # diff between high and closet level among levels
    c1 = abs(df.high[l] - min(levels, key=lambda x: abs(x - df.high[l]))) <= lim
    # diff between higher body and closest level to high
    c2 = (
        abs(
            max(df.open[l], df.close[l])
            - min(levels, key=lambda x: abs(x - df.high[l]))
        )
        <= lim
    )
    # min body less than closest level to high
    c3 = min(df.open[l], df.close[l]) < min(levels, key=lambda x: abs(x - df.high[l]))
    # low price less than closet level to high
    c4 = df.low[l] < min(levels, key=lambda x: abs(x - df.high[l]))

    if c1 or c2 and c3 and c4:
        return 1
    else:
        return 0


#!!! Determines if a candle is close to a Support level
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


# Variables needed for the functions above
n1 = 2
n2 = 2
backCandles = 3
signal = [0] * length

for row in range(backCandles, len(df) - n2):
    # list of the different levels
    ss = []
    rr = []

    for subrow in range(row - backCandles + n1, row + 1):
        # Adding the candle who meets the requirement to be a level
        if support(df, subrow, n1, n2):
            ss.append(df.low[subrow])
        if resistance(df, subrow, n1, n2):
            rr.append(df.high[subrow])

    # Checking if the current candle/row is a engulfing/star pattern and if it is close to a level then assigning a value to the signal list
    myclosedistance = 1e3
    print(ss, rr)
    if (
        isEngulfing(row) == 1
        or isStar(row) == 1
        and closeResistance(row, rr, myclosedistance)
    ):
        signal[row] == 1
    elif (
        isEngulfing(row) == 2
        or isStar(row) == 2
        and closeSupport(row, ss, myclosedistance)
    ):
        signal[row] == 2
    else:
        signal[row] == 0


df["signal"] = signal

# print(f"1:{df[df["signal"] == 1].count()} \n2:{df[df["signal"] == 2].count()}")
