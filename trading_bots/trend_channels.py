import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt


df = pd.read_csv("trading_bots\\v75_H_1_2019-2025.csv")


backcandles = 50
wind = 5
candleid = 1200
# More dynamic backcandles

backcandles = 24 * 15
brange = backcandles // 5
wind = 3
candleid = 1200

maxim = np.array([])
minim = np.array([])
xxmin = np.array([])
xxmax = np.array([])

for i in range(candleid - backcandles, candleid + 1, wind):
    minim = np.append(minim, df.low.iloc[i : i + wind].min())
    xxmin = np.append(xxmin, df.low.iloc[i : i + wind].idxmin())
for i in range(candleid - backcandles, candleid + 1, wind):
    maxim = np.append(maxim, df.high.iloc[i : i + wind].max())
    xxmax = np.append(xxmax, df.high.iloc[i : i + wind].idxmax())

slope_min, intercmin = np.polyfit(xxmin, minim, 1)
slope_max, intercmax = np.polyfit(xxmax, maxim, 1)

dfpl = df[candleid - backcandles - 100 : candleid + backcandles]

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

# fig.add_trace(
#     go.Scatter(x=xxmin, y=slope_min * xxmin + intercmin, mode="lines", name="min slope")
# )
# fig.add_trace(
#     go.Scatter(x=xxmax, y=slope_max * xxmax + intercmax, mode="lines", name="max slope")
# )


#!!! Fitting intercepts to meet highest or lowest cadnle point in time slice

adjintercmin = (
    df.low.loc[candleid - backcandles : candleid].min()
    - slope_min * df.low.iloc[candleid - backcandles : candleid].idxmin()
)
adjintercmax = (
    df.high.loc[candleid - backcandles : candleid].max()
    - slope_max * df.high.iloc[candleid - backcandles : candleid].idxmax()
)

# fig.add_trace(
#     go.Scatter(
#         x=xxmin, y=slope_min * xxmin + adjintercmin, mode="lines", name="min slope"
#     )
# )
# fig.add_trace(
#     go.Scatter(
#         x=xxmax, y=slope_max * xxmax + adjintercmax, mode="lines", name="max slope"
#     )
# )


#!!! Fitting intercepts to wrap price candles

adjintercmax = (df.high.iloc[xxmax] - slope_max * xxmax).max()
adjintercmin = (df.low.iloc[xxmin] - slope_min * xxmin).min()

# fig.add_trace(
#     go.Scatter(
#         x=xxmin, y=slope_min * xxmin + adjintercmin, mode="lines", name="min slope"
#     )
# )
# fig.add_trace(
#     go.Scatter(
#         x=xxmax, y=slope_max * xxmax + adjintercmax, mode="lines", name="max slope"
#     )
# )
# fig.show()

#!!! More dynamic backcandles

backcandles = 24 * 15
brange = backcandles // 5
wind = 3
candleid = 1200

optbackcandles = backcandles
slope_diff = 10000


for r1 in range(backcandles - brange, backcandles + brange):
    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])

    for i in range(candleid - backcandles, candleid + 1, wind):
        minim = np.append(minim, df.low.iloc[i : i + wind].min())
        xxmin = np.append(xxmin, df.low.iloc[i : i + wind].idxmin())
    for i in range(candleid - backcandles, candleid + 1, wind):
        maxim = np.append(maxim, df.high.iloc[i : i + wind].max())
        xxmax = np.append(xxmax, df.high.iloc[i : i + wind].idxmax())

    slope_min, intercmin = np.polyfit(xxmin, minim, 1)
    slope_max, intercmax = np.polyfit(xxmax, maxim, 1)

    if abs(slope_min - slope_max) < slope_diff:
        slope_diff = abs(slope_min - slope_max)
        optbackcandles = r1
        slope_min_opt = slope_min
        slope_max_opt = slope_max
        intercminopt = intercmin
        intermaxopt = intercmax

# print(optbackcandles)

dfpl = df[candleid - wind - optbackcandles - backcandles : candleid + optbackcandles]

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

adjintercmax = (df.high.iloc[xxmax] - slope_max_opt * xxmax).max()
adjintercmin = (df.low.iloc[xxmin] - slope_min_opt * xxmin).min()

# fig.add_trace(
#     go.Scatter(
#         x=xxmin, y=slope_min_opt * xxmin + adjintercmin, mode="lines", name="min slope"
#     )
# )
# fig.add_trace(
#     go.Scatter(
#         x=xxmax, y=slope_max_opt * xxmax + adjintercmax, mode="lines", name="max slope"
#     )
# )
# fig.show()


#!!! More Optimization

backcandles = 100
brange = 50
wind = 5
candleid = 3000

optbackcandles = backcandles
slope_diff = 100
slope_dist = 10000


for r1 in range(backcandles - brange, backcandles + brange):
    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])

    for i in range(candleid - backcandles, candleid + 1, wind):
        minim = np.append(minim, df.low.iloc[i : i + wind].min())
        xxmin = np.append(xxmin, df.low.iloc[i : i + wind].idxmin())
    for i in range(candleid - backcandles, candleid + 1, wind):
        maxim = np.append(maxim, df.high.iloc[i : i + wind].max())
        xxmax = np.append(xxmax, df.high.iloc[i : i + wind].idxmax())

    slope_min, intercmin = np.polyfit(xxmin, minim, 1)
    slope_max, intercmax = np.polyfit(xxmax, maxim, 1)

    dist = (slope_max * candleid + intercmax) - (slope_min * candleid + intercmin)

    if dist < slope_dist:
        slope_dist = dist
        optbackcandles = r1
        slope_min_opt = slope_min
        slope_max_opt = slope_max
        intercminopt = intercmin
        intermaxopt = intercmax
        maxim_opt = maxim.copy()
        minim_opt = minim.copy()
        xxmin_opt = xxmin.copy()
        xxmax_opt = xxmax.copy()

print(optbackcandles)
dfpl = df[candleid - wind - optbackcandles - backcandles : candleid + optbackcandles]

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

adjintercmax = (df.high.iloc[xxmax_opt] - slope_max_opt * xxmax_opt).max()
adjintercmin = (df.low.iloc[xxmin_opt] - slope_min_opt * xxmin_opt).min()

fig.add_trace(
    go.Scatter(
        x=xxmin,
        y=slope_min_opt * xxmin_opt + adjintercmin,
        mode="lines",
        name="min slope",
    )
)
fig.add_trace(
    go.Scatter(
        x=xxmax,
        y=slope_max_opt * xxmax_opt + adjintercmax,
        mode="lines",
        name="max slope",
    )
)
fig.show()
