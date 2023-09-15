from price_history.crypto import (crypto_by_rank,
                                  get_price_history,
                                  read_price_history,
                                  get_categories,
                                  crypto_by_category)

from financial_indicators import technical_indicators

def main():

    database_path = "top_1001_coins.db"

    get_price_history(crypto_by_rank, [1, 1001], database_path)
    
    # Read in price data from a database 
    index, price_history = read_price_history(database_path)

    print(index)
    print(price_history)

    tickers = index["Ticker"].to_list()
    ignore_coins = ["USDT-USD", "USDC-USD", "STETH-USD"]
    for coin in ignore_coins:
        tickers.remove(coin)

    top_5 = tickers[0:10]

    technical_indicators.roi(price_history, top_5, "2022-01-01")

    # Apply financial indicators

    # technical_indicators.apply_roi(database_path)

if __name__ == "__main__":
    # main()
    categories = get_categories()
    crypto_by_category(categories, "604f2776ebccdd50cd175fdc")