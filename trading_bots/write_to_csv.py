import csv

from datetime import datetime, timedelta

import pandas as pd
import MetaTrader5 as mt
import login_info as li

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
timeframe = mt.TIMEFRAME_H4
now = datetime.now()
today = datetime.today()
date_from = datetime(2019, 1, 1)
date_to = datetime(2025, 1, 1)

data = mt.copy_rates_range(symbol, timeframe, date_from, today)
df = pd.DataFrame(data)
df["time"] = pd.to_datetime(df["time"], unit="s")
df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)

df.to_csv("v75_H_4_2019-2025.csv", index=False)
