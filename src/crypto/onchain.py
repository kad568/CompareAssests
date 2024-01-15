import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import chompjs
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import stats
import numpy as np


CHAIN_EXPOSED_BASE_URL = "https://chainexposed.com"

def get_short_term_holder_realised_price_history(): 

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

    return price_data_df, STH_price_df

def get_long_term_holder_realised_price_history():

    long_term_holder_realised_price_url = f"{CHAIN_EXPOSED_BASE_URL}/XthRealizedPriceLongTermHolder.html"

    response = requests.get(long_term_holder_realised_price_url)
    soup = bs(response.text, "html.parser")
    scripts = soup.find_all('script')
    plot_script_raw = scripts[5].text
    plot_data_dict = list(chompjs.parse_js_objects(plot_script_raw)) 
    
    price_data = plot_data_dict[2]
    price_data_df = pd.DataFrame(data={"price": price_data["y"], "date": price_data["x"]})
    price_data_df["date"] = pd.to_datetime(price_data_df["date"])
    price_data_df["price"] = pd.to_numeric(price_data_df["price"])

    LTH_price = plot_data_dict[3]
    LTH_price_df = pd.DataFrame(data={"LTH_price": LTH_price["y"], "date": LTH_price["x"]})
    LTH_price_df["date"] = pd.to_datetime(LTH_price_df["date"])
    LTH_price_df["LTH_price"] = pd.to_numeric(LTH_price_df["LTH_price"])

    return price_data_df, LTH_price_df


def plot_STH_LTH(price_df, realised_price_df, type):

    difference = stats.zscore((price_df["price"] - realised_price_df[f"{type}_price"]) / price_df["price"])

  # plot price and STH
    plt.subplot(2, 1, 1)
    plt.plot(price_df["date"], price_df["price"])
    plt.plot(realised_price_df["date"], realised_price_df[f"{type}_price"])
    plt.yscale("log")

    plt.subplot(2, 1, 2)
    plt.plot(price_df["date"], difference)
    plt.fill_between(price_df["date"], y1=difference, alpha=.1)
    plt.axhline(y = 0, color= "r")
    plt.grid()
    plt.show()

def run_script():

    # price_1, STH_price_history = get_short_term_holder_realised_price_history()
    price_2, LTH_price_history = get_long_term_holder_realised_price_history()

    plot_STH_LTH(price_2, LTH_price_history, "LTH")

if __name__ == "__main__":
    run_script()



