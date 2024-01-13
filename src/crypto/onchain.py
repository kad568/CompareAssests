import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup as bs
import chompjs
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import stats
import numpy as np


CHAIN_EXPOSED_BASE_URL = "https://chainexposed.com"

def get_short_term_holder_realised_price_histroty(): 

    short_term_holder_realised_price_url = f"{CHAIN_EXPOSED_BASE_URL}/XthRealizedPriceShortTermHolder.html"

    response = requests.get(short_term_holder_realised_price_url)
    soup = bs(response.text, "html.parser")
    scripts = soup.find_all('script')
    plot_script_raw = scripts[5].text
    plot_data_dict = list(chompjs.parse_js_objects(plot_script_raw)) 

    price_data = plot_data_dict[2]
    price_data_df = pd.DataFrame(data={"price": price_data["y"], "date": price_data["x"]})
    price_data_df["date"] = pd.to_datetime(price_data_df["date"])
    price_data_df["price"] = pd.to_numeric(price_data_df["price"])

    STH_price = plot_data_dict[3]
    STH_price_df = pd.DataFrame(data={"STH_price": STH_price["y"], "date": STH_price["x"]})
    STH_price_df["date"] = pd.to_datetime(STH_price_df["date"])
    STH_price_df["STH_price"] = pd.to_numeric(STH_price_df["STH_price"])

    difference = stats.zscore((price_data_df["price"] - STH_price_df["STH_price"]) / price_data_df["price"])

  # plot price and STH
    plt.subplot(2, 1, 1)
    plt.plot(price_data_df["date"], price_data_df["price"])
    plt.plot(STH_price_df["date"], STH_price_df["STH_price"])
    plt.yscale("log")

    plt.subplot(2, 1, 2)
    plt.plot(price_data_df["date"], difference)
    plt.grid()
    plt.show()

    # got trace 1 and 2, just disect the raw dictioanry
    return 0

def run_script():
    
    STH_price_history = get_short_term_holder_realised_price_histroty()

if __name__ == "__main__":
    run_script()



