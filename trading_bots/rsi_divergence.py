import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from datetime import datetime

# Reads csv and converts it to a dataframe
df = pd.read_csv("trading_bots\\v75_H_1_2019-2025.csv")

# Adds the rsi indicator to the dataframe with a length specified as a argument passed into it
df["rsi"] = df.ta.rsi(length=14)


#!!! RSI which uses the price instead of a ema
def myRsi(price, n=20):
    delta = price["close"].diff()
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0

    rolUp = dUp.rolling(window=n).mean()
    rolDown = dDown.rolling(window=n).mean().abs()

    rs = rolUp / rolDown
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


#!!! Function to detect pivot points in price
def pivotid(df1, l, n1, n2):
    if l - n1 < 0 or l + n2 >= len(df1):
        return 0

    piv_id_low = 1
    piv_id_high = 1
    for i in range(l - n1, l + n2 + 1):
        if df1.low[l] > df1.low[i]:
            piv_id_low = 0
        if df1.high[l] < df1.high[i]:
            piv_id_high = 0

    if piv_id_high and piv_id_low:
        return 3
    elif piv_id_low:
        return 1
    elif piv_id_high:
        return 2
    else:
        return 0


#!!! Function to detect pivot points in the rsi
def rsiPivotid(df1, l, n1, n2):
    if l - n1 < 0 or l + n2 >= len(df1):
        return 0

    piv_id_low = 1
    piv_id_high = 1
    for i in range(l - n1, l + n2 + 1):
        if df1.rsi[l] > df1.rsi[i]:
            piv_id_low = 0
        if df1.rsi[l] < df1.rsi[i]:
            piv_id_high = 0

    if piv_id_high and piv_id_low:
        return 3
    elif piv_id_low:
        return 1
    elif piv_id_high:
        return 2
    else:
        return 0


# Adds the pivot points of both price and the rsi into the dataframe
n1, n2 = 5, 5
df["pivot"] = df.apply(lambda x: pivotid(df, x.name, n1, n2), axis=1)
df["rsipivot"] = df.apply(lambda x: rsiPivotid(df, x.name, n1, n2), axis=1)


#!!! Helps visualize the pivot points on graphes
def pointpos(x):
    if x["pivot"] == 1:
        return x["low"] - 1e3
    elif x["pivot"] == 2:
        return x["high"] + 1e3
    else:
        return np.nan


def rsiPointpos(x):
    if x["rsipivot"] == 1:
        return x["rsi"] - 1
    elif x["rsipivot"] == 2:
        return x["rsi"] + 1
    else:
        return np.nan


# Adds the pivot points position of both price and the rsi into the dataframe
df["pointpos"] = df.apply(lambda row: pointpos(row), axis=1)
df["rsipointpos"] = df.apply(lambda row: rsiPointpos(row), axis=1)

# Number of candles to check backwards in price
backcandles = 60
# Candle index
candleid = 10021

# Maximal and minimal values with their coordinates
maxim = np.array([])
minim = np.array([])
xxmin = np.array([])
xxmax = np.array([])

maximRsi = np.array([])
minimRsi = np.array([])
xxminRsi = np.array([])
xxmaxRsi = np.array([])

for i in range(candleid - backcandles, candleid + 1):
    if df.iloc[i].pivot == 1:
        minim = np.append(minim, df.iloc[i].low)
        xxmin = np.append(xxmin, i)
    if df.iloc[i].pivot == 2:
        maxim = np.append(maxim, df.iloc[i].high)
        xxmax = np.append(xxmax, i)
    if df.iloc[i].rsipivot == 1:
        minimRsi = np.append(minimRsi, df.iloc[i].rsi)
        xxminRsi = np.append(xxminRsi, df.iloc[i].name)
    if df.iloc[i].rsipivot == 2:
        maximRsi = np.append(maximRsi, df.iloc[i].rsi)
        xxmaxRsi = np.append(xxmaxRsi, df.iloc[i].name)

# Slopes and intercepts
slmin, intercmin = np.polyfit(xxmin, minim, 1)
slmax, intercmax = np.polyfit(xxmax, maxim, 1)
slminRsi, intercminRsi = np.polyfit(xxminRsi, minimRsi, 1)
slmaxRsi, intercmaxRsi = np.polyfit(xxmaxRsi, maximRsi, 1)

print(slmin, slmax, slminRsi, slmaxRsi)


#!!! Divergence function
def divsignal(x, nbackcandles):

    backcandles = nbackcandles
    candleid = int(x.name)

    # Maximal and minimal values with their coordinates
    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])

    maximRsi = np.array([])
    minimRsi = np.array([])
    xxminRsi = np.array([])
    xxmaxRsi = np.array([])

    for i in range(candleid - backcandles, candleid + 1):
        if df.iloc[i].pivot == 1:
            minim = np.append(minim, df.iloc[i].low)
            xxmin = np.append(xxmin, i)
        if df.iloc[i].pivot == 2:
            maxim = np.append(maxim, df.iloc[i].high)
            xxmax = np.append(xxmax, i)
        if df.iloc[i].rsipivot == 1:
            minimRsi = np.append(minimRsi, df.iloc[i].rsi)
            xxminRsi = np.append(xxminRsi, df.iloc[i].name)
        if df.iloc[i].rsipivot == 2:
            maximRsi = np.append(maximRsi, df.iloc[i].rsi)
            xxmaxRsi = np.append(xxmaxRsi, df.iloc[i].name)

    if maxim.size < 2 or minim.size < 2 or maximRsi.size < 2 or minimRsi.size < 2:
        return 0

    slmin, intercmin = np.polyfit(xxmin, minim, 1)
    slmax, intercmax = np.polyfit(xxmax, maxim, 1)
    slminRsi, intercminRsi = np.polyfit(xxminRsi, minimRsi, 1)
    slmaxRsi, intercmaxRsi = np.polyfit(xxmaxRsi, maximRsi, 1)

    # Checks to see if the price slope is postive and the rsi slope is negative
    if slmin > 1e-4 and slmax > 1e-4 and slmaxRsi < -0.1:
        return 1
    # Checks to see if the price slope is negative and the rsi slope is postive
    elif slmin < -1e-4 and slmax < -1e-4 and slminRsi > 0.1:
        return 2
    else:
        return 0


#!!! Divergence function using pivot point levels instead of slopes
def divsignal2(x, nbackcandles):
    backcandles = nbackcandles
    candleid = int(x.name)

    # Close price and position
    closp = np.array([])
    xxclos = np.array([])

    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])

    maximRsi = np.array([])
    minimRsi = np.array([])
    xxminRsi = np.array([])
    xxmaxRsi = np.array([])

    for i in range(candleid - backcandles, candleid + 1):
        closp = np.append(closp, df.iloc[i].close)
        xxclos = np.append(xxclos, i)
        if df.iloc[i].pivot == 1:
            minim = np.append(minim, df.iloc[i].low)
            xxmin = np.append(xxmin, i)
        if df.iloc[i].pivot == 2:
            maxim = np.append(maxim, df.iloc[i].high)
            xxmax = np.append(xxmax, i)
        if df.iloc[i].rsipivot == 1:
            minimRsi = np.append(minimRsi, df.iloc[i].rsi)
            xxminRsi = np.append(xxminRsi, df.iloc[i].name)
        if df.iloc[i].rsipivot == 2:
            maximRsi = np.append(maximRsi, df.iloc[i].rsi)
            xxmaxRsi = np.append(xxmaxRsi, df.iloc[i].name)

    slclos, interclos = np.polyfit(xxclos, closp, 1)

    # Determines if there are enough pivots to consider a divergence
    if slclos > 1e-4 and maximRsi.size < 2 or maxim.size < 2:
        return 0
    if slclos < -1e-4 and maximRsi.size < 2 or maxim.size < 2:
        return 0

    # Determines divergence
    if slclos > 1e-4:
        if maximRsi[-1] < maximRsi[-2] and maxim[-1] > maxim[-2]:
            return 1
    elif slclos < -1e-4:
        if minimRsi[-1] > minimRsi[-2] and minim[-1] < minim[-2]:
            return 1
    else:
        return 0


# Adds a divergence signal to the dataframe
# df["div_signal"] = df.apply(lambda row: divsignal(row, 30), axis=1)

# Selects a index of the dataframe to plot
# dfpl = df[candleid - backcandles - 5 : candleid + backcandles]
dfpl = df[0:500]
# Adds divergence signal to indexed dataframe as using the full "df" takes too long
dfpl["div_signal"] = dfpl.apply(lambda row: divsignal(row, 30), axis=1)
dfpl["div_signal2"] = dfpl.apply(lambda row: divsignal2(row, 30), axis=1)

# Adds another graph plot slot
fig = make_subplots(rows=2, cols=1)

# Plots using the indexed dataframe
fig.append_trace(
    go.Candlestick(
        x=dfpl.index,
        open=dfpl["open"],
        high=dfpl["high"],
        low=dfpl["low"],
        close=dfpl["close"],
    ),
    row=1,
    col=1,
)


# Adds the price pivot pointsto graph
fig.add_scatter(
    x=dfpl.index,
    y=dfpl["pointpos"],
    mode="markers",
    marker=dict(size=5, color="MediumPurple"),
    name="pivot",
    row=1,
    col=1,
)
# Adds the slopes for the price pivot points
fig.add_trace(
    go.Scatter(x=xxmin, y=slmin * xxmin + intercmin, mode="lines", name="minslope"),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(x=xxmax, y=slmax * xxmax + intercmax, mode="lines", name="maxslope"),
    row=1,
    col=1,
)

# Adds rsi to plot
fig.append_trace(go.Scatter(x=dfpl.index, y=dfpl["rsi"]), row=2, col=1)
# Adds the rsi pivot points to graph
fig.add_scatter(
    x=dfpl.index,
    y=dfpl["rsipointpos"],
    mode="markers",
    marker=dict(size=3, color="MediumPurple"),
    name="pivot",
    row=2,
    col=1,
)
# Adds the slopes for the rsi pivot points
fig.add_trace(
    go.Scatter(
        x=xxminRsi,
        y=slminRsi * xxminRsi + intercminRsi,
        mode="lines",
        name="rsiminslope",
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=xxmaxRsi,
        y=slmaxRsi * xxmaxRsi + intercmaxRsi,
        mode="lines",
        name="rsimaxslope",
    ),
    row=2,
    col=1,
)

# Removes x axis range slider
fig.update_layout(xaxis_rangeslider_visible=False)
# Shows the created figure
fig.show()
