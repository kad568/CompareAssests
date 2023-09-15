import pandas as pd   
from matplotlib import pyplot as plt 

from price_history.crypto import read_price_history


def roi(grouped_df: pd.DataFrame.groupby, tickers, start_date = "2000-01-01"):

    for ticker in tickers:

        asset = grouped_df.get_group(ticker)
        asset = asset.sort_values(by=["Date"])
        asset = asset.loc[asset['Date'] > start_date]
        price = asset["Close"].tolist()
        date = asset["Date"].tolist()
        start_price = price[0]
        roi = [(_ - start_price) / start_price for _ in price]

        plt.plot(date, roi, label=ticker)

    plt.legend(loc="upper left")
    plt.grid(which='both')
    plt.ylabel("Return on Investment")
    plt.xlabel("Time")
    plt.yscale('symlog')

    plt.show()

# use an SQL data base rather than csv files - DONE
# link index to crypto price history table


# backtesting function
# chart visualiser


# def apply_roi(database: pd.DataFrame) -> pd.DataFrame:

#     crypto_index_df, price_history_df = read_price_history(database)

#     tickers = crypto_index_df["Tickers"].to_list()

#     price_history_df["roi"] = ...



