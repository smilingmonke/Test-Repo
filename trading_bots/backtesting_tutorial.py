from backtesting import Strategy, Backtest
import pandas as pd
import numpy as np
import pandas_ta as ta


df = pd.read_csv("trading_bots\\CSV\\v75_H_1_2019-2025.csv")

df["ATR"] = ta.atr(high=df.High, low=df.Low, close=df.Close, length=14)
df["SMA10"] = ta.sma(df.Close, length=10)
df["SMA20"] = ta.sma(df.Close, length=20)
df["SMA100"] = ta.sma(df.Close, length=100)
df["SMA200"] = ta.sma(df.Close, length=200)


def SMAsig(df1, l, SMAbackcandles):
    sigup = 2
    sigdn = 1
