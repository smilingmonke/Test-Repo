import pandas as pd
import numpy as np
import pandas_ta as ta


df = pd.read_csv("trading_bots\\v75_D_1_2019-2025.csv")
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

        highdiff[row] = high[row] - max(open[row], close[row])
        bodydiff[row] = abs(open[row] - close[row])

        if bodydiff[row] < 2 * 1e-3:
            bodydiff[row] = 2 * 1e-3

        lowdiff[row] = min(open[row], close[row]) - low[row]
        ratio1[row] = highdiff[row] / bodydiff[row]
        ratio2[row] = lowdiff[row] / bodydiff[row]

        if (
            ratio1[row] > 2.5
            and lowdiff[row] < 0.23 * highdiff[row]
            and bodydiff[row] > 300
            and df.sma21[row] > close[row]
            # and df.rsi[row] > 40
            # and df.rsi[row] < 70
        ):
            signal[row] = 1
        elif (
            ratio2[row] > 2.5
            and highdiff[row] < 0.23 * lowdiff[row]
            and bodydiff[row] > 300
            and df.sma21[row] < close[row]
            # and df.rsi[row] > 30
            # and df.rsi[row] < 60
        ):
            signal[row] = 2

    return signal


df["signal1"] = Revsignal1(df)


# Target Shooting Star
def mytarget(barsupfront, df1):
    length = len(df1)
    high = list(df["high"])
    low = list(df["low"])
    close = list(df["close"])
    open = list(df["open"])
    datr = list(df["atr"])
    trendcat = [None] * length

    for line in range(0, length - barsupfront - 1):
        valueOpenLow = 0
        valueOpenHigh = 0

        highdiff = high[line] - max(open[line], close[line])
        bodydiff = abs(open[line] - close[line])

        tickdiff = datr[line] * 1
        if tickdiff < 5:
            tickdiff = 5

        SLTPRatio = 1

        for i in range(1, barsupfront + 1):
            value1 = close[line] - low[line + i]
            value2 = close[line] - high[line + i]
            valueOpenLow = max(value1, valueOpenLow)
            valueOpenHigh = min(value2, valueOpenHigh)

            if (valueOpenLow >= (SLTPRatio * tickdiff)) and (-valueOpenHigh < tickdiff):
                trendcat[line] = 1  # downtrend
                break
            elif (valueOpenLow < tickdiff) and (
                -valueOpenHigh >= (SLTPRatio * tickdiff)
            ):
                trendcat[line] = 2  # uptrend
                break
            else:
                trendcat[line] = 0  # no trend

    return trendcat


df["trend"] = mytarget(100, df)

conditions = [
    (df["trend"] == 1) & (df["signal1"] == 1),
    (df["trend"] == 2) & (df["signal1"] == 2),
]
values = [1, 2]
df["result"] = np.select(conditions, values)

trendId = 2
print(
    df[df["result"] == trendId].result.count()
    / df[df["signal1"] == trendId].signal1.count()
)
df[(df["result"] != trendId) & (df["signal1"] == trendId)]  # false positives
