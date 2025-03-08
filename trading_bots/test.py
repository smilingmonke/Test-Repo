from datetime import datetime, timedelta
import time
import MetaTrader5 as mt
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as ply
import matplotlib.pyplot as mtpl
import login_info as li

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
timeframe = mt.TIMEFRAME_D1
now = datetime.now()
date_from = datetime(2019, 1, 1)
date_to = datetime(2025, 1, 1)

data = mt.copy_rates_range(symbol, timeframe, date_from, date_to)
df = pd.DataFrame(data)
df["time"] = pd.to_datetime(df["time"], unit="s")
df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)

df.ta.indicators()
# print(df)

# df["ATR"] = df.ta.atr()
# df["RSI"] = df.ta.rsi()
