import time
import os
import pandas as pd
import pandas_ta as ta
import MetaTrader5 as mt
from datetime import datetime, timedelta
import login_info as li


# returns selected symbol
def symbol_selector():
    symbols = {1: "Volatility 75 Index", 2: "Volatility 25 Index"}

    for i in range(1, len(symbols) + 1):
        print(f"{i}. {symbols[i]}")

    symbol = int(input(f"Please choose a symbol> "))

    try:
        if not symbols[symbol]:
            print(f"Invalid symbol key :{symbol}")
        else:
            symbol = symbols[symbol]
            print(f"Selected symbol: {symbol}")
    except:
        print(f"Invalid symbol key :{symbol}")

    return symbol


"""
FUNCTIONS TO MAKE :>>
1) Kill switch - exits every open trade and pending order ✅
2) Trade Pauser - determines if the bot has lot x% in x number of trades and pauses the bot for an x period of time ✅
3) Overtime - exits if trade exceed time limit
3) ATRClose - exits if price reaches the previous close plus ATR
"""


# Cancels a pending order
def CancelOrder(symbol, ticket=None):

    if ticket is not None:
        orders = mt.orders_get(ticket=ticket)

    tried = 0
    done = 0
    for order in orders:
        tried += 1

        request = {"action": mt.TRADE_ACTION_REMOVE, "order": order.ticket}

        for tries in range(1):
            r = mt.order_send(request)
            if r == None:
                return None
            if (
                r.retcode != mt.TRADE_RETCODE_REQUOTE
                and r.retcode != mt.TRADE_RETCODE_PRICE_OFF
            ):
                if r.retcode == mt.TRADE_RETCODE_DONE:
                    done += 1
                break

        if done > 0:
            if done == tried:
                return True
            else:
                return False

    return False


# Pauses the bot trading if the losses exceed a certain amount within a time period
def LossPause(max_loss):

    trade_losses = 0
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    deals = mt.history_deals_get(yesterday, now)
    if deals == None:
        print(f"NO DEALS, {mt.last_error()}")
    elif len(deals) > 0:
        deals_df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        deals_df["time"] = pd.to_datetime(deals_df["time"], unit="s")
        deals_df = deals_df[deals_df["profit"] < 0]
        deals_df.reset_index(drop=True, inplace=True)

        for i in range(0, len(deals_df)):
            trade_losses += deals_df["profit"].iloc[i]

        trade_losses = abs(trade_losses)
        if trade_losses > max_loss:
            print(f"\n😴...Sleeping cuz losses have exceeded {max_loss}...😴\n")
            time.sleep(3600)
        else:
            print(f"\nContinuing to trade until losses exceed {max_loss}\n")


# Exits every open position and pending order
def KillSwitch(symbol):

    print(" ")

    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    print("\n👹TURNING ON THE KILL SWITCH👹\n")

    trades_closed = 0
    orders_cancelled = 0

    if mt.positions_total() > 0:

        positions = mt.positions_get()
        pos_df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        tickets = [0] * len(positions)
        tickets = pos_df["ticket"]

        for ticket in tickets:
            if mt.Close(symbol, ticket=ticket):
                trades_closed += 1

        print(f"\n# of closed trades = {trades_closed}")
        pos_checked = True

    if mt.orders_total() > 0:
        orders = mt.orders_get()
        orders_df = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
        tickets = [0] * len(orders)
        tickets = orders_df["ticket"]

        for ticket in tickets:
            if CancelOrder(symbol, ticket=ticket):
                orders_cancelled += 1

        print(f"\n# of orders cancelled = {orders_cancelled}")

    else:
        print("\nNO ACTIVE ORDERS OR POSITIONS TURNING OFF KILL SWITCH...")

    print("\n...Turning off KillSwitch...\n")

    return trades_closed


# Creates a trade
def CreateTrade(symbol, volume, price, sl, tp, order_type, deviation):  # sl

    order = {
        "action": mt.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "price": price,
        "sl": sl,
        "tp": tp,
        "order_type": order_type,
        "deviation": deviation,
    }

    r = mt.order_send(order)

    return r


# Exits if price reaches the previous close plus ATR
def ATRClose(symbol, atr_price):

    trade_type = ""
    in_pos = False
    atr_factor = 1
    atr_price *= atr_factor
    exits = 0

    positions = mt.positions_get()
    positions_df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())

    if len(positions) > 0:
        in_pos = True
        while in_pos:
            price = mt.symbol_info_tick(symbol).ask
            positions = mt.positions_get()
            os.system("cls" if os.name == "nt" else "clear")
            print("\n🔍Checking if its time to exit...🔍\n")
            i = 1
            for pos in positions:

                if pos.type == 1:
                    trade_type = "SELL"
                elif pos.type == 0:
                    trade_type = "BUY"
                print(
                    f"< Trade #: {i} | {trade_type} | Lots: {pos.volume} | Profit: {pos.profit:.2} >"
                )
                time.sleep(3)
                entry = pos.price_open

                buysl = round(entry - atr_price, 2)
                buytp = round(entry + atr_price, 2)
                sellsl = round(entry + atr_price, 2)
                selltp = round(entry - atr_price, 2)

                if pos.type == mt.ORDER_TYPE_BUY:

                    if price < buysl:
                        print("🔴Hit SL exiting buy...")
                        exits += KillSwitch(symbol)
                        in_pos = False
                        break
                    elif price > buytp:
                        print("🟢Hit TP exiting buy...")
                        exits += KillSwitch(symbol)
                        in_pos = False
                        break
                elif pos.type == mt.ORDER_TYPE_SELL:
                    if price > sellsl:
                        print("🔴Hit SL exiting sell...")
                        exits += KillSwitch(symbol)
                        in_pos = False
                        break
                    elif price < selltp:
                        print("🟢Hit TP exiting sell...")
                        exits += KillSwitch(symbol)
                        in_pos = False
                        break

                i += 1

    else:
        print(f"Open positions = {len(positions)}")

    return exits


# Retrieves price info and ask price then puts it into a dataframe
def getData(symbol, timeframe):

    timeframes = {
        "one_minute": mt.TIMEFRAME_M1,
        "five_minute": mt.TIMEFRAME_M5,
        "fifteen_minute": mt.TIMEFRAME_M15,
        "thirty_minute": mt.TIMEFRAME_M30,
        "hourly": mt.TIMEFRAME_H1,
        "four_hour": mt.TIMEFRAME_H4,
        "daily": mt.TIMEFRAME_D1,
        "weekly": mt.TIMEFRAME_W1,
        "monthly": mt.TIMEFRAME_MN1,
    }

    if not mt.initialize():
        print(f"failed to initialize {mt.last_error()}")
    else:
        if not mt.login(login=li.login_id, password=li.password, server=li.server):
            print(f"Failed to login to Account #{li.login_id}")

    timeframe = mt.TIMEFRAME_H1
    now = datetime.now()
    date_from = now - timedelta(days=21)

    ask = mt.symbol_info_tick(symbol).ask

    data = mt.copy_rates_range(symbol, timeframe, date_from, now)
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.drop(columns=["spread", "real_volume", "tick_volume"], axis=1, inplace=True)
    df.columns = ["Local time", "Open", "High", "Low", "Close"]

    # Indicators
    df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
    df["MA10"] = ta.sma(close=df.Close, length=10)
    df["MA20"] = ta.sma(close=df.Close, length=20)
    df["MA100"] = ta.sma(close=df.Close, length=100)
    df["MA200"] = ta.sma(close=df.Close, length=200)
    # df["ATRMean"] = df["ATR"].rolling(12).mean()

    return df, ask
