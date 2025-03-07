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
