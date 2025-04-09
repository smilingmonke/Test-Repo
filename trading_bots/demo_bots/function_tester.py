import MetaTrader5 as mt
import login_info as li
from datetime import datetime, timedelta
import time
import pandas as pd
import schedule
import bot_functions as uf
import pandas_ta as ta

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "XAUUSD"
v75 = "Volatility 75 Index"
tf = "H1"

# symbol = uf.symbol_selector()
# timeframe = uf.timeframe_selector()
lots = uf.lots_selector()
print(f"LOTS = {lots}")
