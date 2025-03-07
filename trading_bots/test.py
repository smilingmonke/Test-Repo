from datetime import datetime
import time
import MetaTrader5 as mt
import pandas as pd
import plotly.graph_objects as ply
import matplotlib.pyplot as mtpl
import login_info as li

if not mt.initialize():
    print(f"failed to initialize {mt.last_error()}")
else:
    if not mt.login(login=li.login_id, password=li.password, server=li.server):
        print(f"Failed to login to Account #{li.login_id}")

symbol = "Volatility 75 Index"
