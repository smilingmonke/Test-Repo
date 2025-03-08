import pandas as pd
import numpy as np
import pandas_ta as ta


df = pd.read_csv("v75_D_1_2019-2025.csv")
df["atr"] = df.ta.atr(length=10)
df["rsi"] = df.ta.rsi()
df["sma21"] = df.ta.sma(length=21)


# for Downtrends
# Shooting Star
def Revsignal1(df1):
    length = len(df1)
    high = list(df["high"])
    low = list(df["low"])
    close = list(df["close"])
    open = list(df["open"])
    signal = [0] * length
    highdiff = [0] * length
    lowdiff = [0] * length
    bodydiff = [0] * length
    ratio1 = [0] * length
    ratio2 = [0] * length

    for row in range(0, length):
        pass
