import MetaTrader5 as mt
import login_info as li
from datetime import datetime, timedelta
import time
import pandas as pd
import schedule
import bot_functions as uf


if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
timeframe = mt.TIMEFRAME_H1
now = datetime.now()
yesterday = now - timedelta(days=1)
today = datetime.today()
date_from = today - timedelta(days=31)
date_to = datetime(2025, 1, 1)

data = mt.copy_rates_range(symbol, timeframe, date_from, now)
df = pd.DataFrame(data)
df["time"] = pd.to_datetime(df["time"], unit="s")
df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
df.columns = ["Local time", "Open", "High", "Low", "Close"]

uf.KillSwitch(symbol)
