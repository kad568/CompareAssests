import requests
import pandas as pd
from enum import Enum
from pathlib import Path
import json
import pickle
from time import sleep
import matplotlib.pyplot as plt
from functools import wraps


# to do
# make build up mathods / queries for getting this data 

# tags map
# cetergory map
# category data (top 1000)
# price history (top 1000)
    # linear interpolation between days

# tools
    # power law
    # ratio of coins (need linear price interpolation)
    # technical indicators
        # rsi
        # volatility
    # onchain data

# MINIMUM VIABLE PRODUCT

# Constant paths and varaibles
CMC_SCRIPT_PATH = Path(__file__).parent.resolve()

CMC_API_KEY_FILE_PATH = CMC_SCRIPT_PATH / "cmc_api_key.txt"

def retry(max_attempts=5, initial_sleep=1):
    def decorator_retry(func):
        @wraps(func)
        def wrapper_retry(*args, **kwargs):
            sleep_time = initial_sleep
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    print(f"Attempt {attempt + 1} failed. Retrying in {sleep_time} seconds.")
                    sleep(sleep_time)
                    sleep_time *= 2
        return wrapper_retry
    return decorator_retry


def get_id_map(cmc_api_key_file_path: str = CMC_API_KEY_FILE_PATH) -> pd.DataFrame:

    # getting cmc api key
    with open(cmc_api_key_file_path, "r") as file:
        api_key = file.read()


    cmc_id_map_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    params = {
        "listing_status": "active,inactive",
    }

    # call to the cmc id map api 
    response = requests.get(cmc_id_map_api_url, headers=headers, params=params)
    response.raise_for_status()

    
    # manipulating id map api call data
    id_map_data: dict = response.json()
    id_map_data = id_map_data["data"]

    id_map_data: pd.DataFrame = pd.DataFrame(id_map_data)
    id_map_data = id_map_data.drop(columns="platform")

    return id_map_data

def get_latest_listing(cmc_api_key_path: str = CMC_API_KEY_FILE_PATH, limit: int = 5) -> pd.DataFrame:

    with open(cmc_api_key_path, "r") as file:
        api_key = file.read()

    coinmarketcap_latest_listing_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    params = {
        'limit': limit,
    }

    response = requests.get(coinmarketcap_latest_listing_api_url, headers=headers, params=params)

    latest_listing_data: dict = response.json() # do you need to use json here? 
    latest_listing_data = latest_listing_data["data"]


    latest_listing_data: pd.DataFrame = pd.DataFrame(latest_listing_data)

    tags_data: pd.DataFrame = latest_listing_data[["id", "tags"]]
    tags_data = tags_data.explode("tags")

    latest_listing_data = latest_listing_data.drop(columns=["platform", "quote", "tags", "name", "symbol", "cmc_rank", "date_added", "slug"])

    return latest_listing_data, tags_data

def get_category_id_map(cmc_api_key_path: str = CMC_API_KEY_FILE_PATH) -> pd.DataFrame:
    
    with open(cmc_api_key_path, "r") as file:
        api_key = file.read()

    cmc_categories_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories"

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(cmc_categories_url, headers=headers)

    data = json.loads(response.text)
    data = data["data"]
    categories = pd.DataFrame(data=data)

    return categories

def get_category(category_id: str):

    with open(CMC_API_KEY_FILE_PATH, "r") as file:
        api_key = file.read()

    cmc_categories_url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/category?id={category_id}"

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(cmc_categories_url, headers=headers)
    print(response.status_code)

    data = json.loads(response.text)
    data = data["data"]

    data = pd.DataFrame(data=[data])

    return data

def get_all_category_coins(category_ids, sleep_time = 5, save_path = None):

    category_coins_df = pd.DataFrame()
    x = 1

    for category in category_ids:

        category_df = get_category(category)
        sleep(sleep_time)
        print(x)

        coins_list = list(category_df["coins"])[0]
        coins_df = pd.json_normalize(coins_list, max_level=0)
        coins_df["category_id"] = category
        coins_df = coins_df[["category_id", "id"]]

        category_coins_df = pd.concat([category_coins_df, coins_df], ignore_index=True)
        category_coins_df = category_coins_df.reset_index(drop=True)

        if save_path:
            category_coins_df.to_pickle(f"{save_path}.pkl")
        
        x  += 1

    return category_coins_df

class CMC_Data_Range(Enum):

    DAILY = "1D"
    WEEKLY = "7D"
    MONTHLY = "1M"
    YEARLY = "1Y"
    ALL = "ALL"

def get_close_price_history(coin_id: int, range: Enum = CMC_Data_Range.ALL):
    """
    Produces pandas dataframe of the price history of a given crypto with the following columns:
    - close usd
    - volume usd
    - marketcap usd
    - fixed supply (yes or no)
    - token supply
    """

    range = range.value 
    # set up request
    cmc_chart_api_base = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart"
    chart_api_params = {
        "id": str(coin_id),
        "range": range,
        # "interval": "1D"
    }

    optional_chart_headers = {
        "Origin": "https://coinmarketcap.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Platform": "web",
        "Referer": "https://coinmarketcap.com/",
        "Sec-Fetch-Mode": "cors"
    }

    # make request
    chart_api_request = requests.get(cmc_chart_api_base, params=chart_api_params, headers=optional_chart_headers)

    # unpack relevant json data into a list of chart data records
    chart_data: dict = chart_api_request.json()
    chart_data = chart_data["data"]["points"]
    chart_data = [
        {"unix_timestamp": unix_timestamp, "chart_data_list": point_data["v"]} 
        for unix_timestamp, point_data in chart_data.items() 
    ]

    # create dataframe
    price_history_df = pd.DataFrame(chart_data)

    # Unpack "chart_data_list" into separate columns
    price_history_df[["close_usd", "volume_usd", "mc_usd", "fixed_supply", "supply"]] = price_history_df["chart_data_list"].apply(pd.Series)

    # Convert Unix timestamp to datetime
    price_history_df['unix_timestamp'] = pd.to_datetime(price_history_df['unix_timestamp'], unit="s") # reverted back to normal method to keep time data as resample.mean() removes this anyway
    # Drop the original 'price_history_df' column
    price_history_df = price_history_df.drop(columns=["chart_data_list"])

    price_history_df["id"] = coin_id

    return price_history_df

def load_pkled_df(path: str):

    path = Path(path)
    with open(path, "rb") as file:
        data: pd.DataFrame = pickle.load(file)

    return data

def get_all_coin_close_price_history(coin_id_df: pd.DataFrame, rank_limit = 500, save_path = None, sleep_time = 2, attemps = 10):
    
    price_history_df = pd.DataFrame()

    x = 1

    coins_within_range = coin_id_df[coin_id_df["rank"] <= rank_limit]["id"] 

    for coin_id in coins_within_range:
        
        # ADD FOR LOOP WITH BREAK FOR TRY AND EXCEPT AND BACKING OFF METHOD - Done (att)
        for att in range(attemps):
            try:
                coin_price_history = get_close_price_history(coin_id)
                break
            except Exception as e:
                if att == attemps - 1:
                    raise e
                print(f"attempt failed, now sleeping for {sleep_time}s")
                sleep_time *= 2
                sleep(sleep_time)
        
        price_history_df = pd.concat([price_history_df, coin_price_history], ignore_index=True)
        print(x)
        if save_path:

            price_history_df.to_pickle(save_path)

        sleep(sleep_time)
        x += 1

    return price_history_df

def interpolate_price_history(price_history_df: pd.DataFrame):

    interp_dfs = []

    for _, group_df in price_history_df.groupby("id"):
        group_df["unix_timestamp"] = pd.to_datetime(group_df["unix_timestamp"])
        interp_group = group_df.resample("D", on="unix_timestamp").mean().interpolate()
        interp_group = interp_group.reset_index()
        interp_dfs.append(interp_group)

    interp_df = pd.concat(interp_dfs)
    interp_df = interp_df.reset_index(drop=True)

    return interp_df

def main():
    
    # btc = get_close_price_history(1)
    # btc.to_pickle(CMC_SCRIPT_PATH / "close_price_history.pkl")

    id_map = load_pkled_df(CMC_SCRIPT_PATH / "id_map.pkl")
    price_history = get_all_coin_close_price_history(id_map,rank_limit=2, save_path=CMC_SCRIPT_PATH / "price_history.pkl")

    # up to 447

    print(price_history)
    

def main_read():
    
    id_map = load_pkled_df(CMC_SCRIPT_PATH / "id_map.pkl")


    index = load_pkled_df(CMC_SCRIPT_PATH / "coin_price_history_index.pkl")
    index = interpolate_price_history(index)
    index.to_pickle(CMC_SCRIPT_PATH / "coin_price_history_index_interp.pkl")
    print(index)



    # btc_eth_data: pd.DataFrame = load_pkled_df(CMC_SCRIPT_PATH / "btc_eth_daily_price_history.pkl")
    # btc_eth_data.reset_index(level="id", drop=True, inplace=True) # impotant add to the main function
    # btc = btc_eth_data[btc_eth_data["id"] == 1]
    # eth = btc_eth_data[btc_eth_data["id"] == 1027]
    # eth_btc = eth.div(btc, axis="index")
    # eth_btc = eth_btc["close_usd"].dropna()

    # eth_btc.plot(loglog=True)
    # plt.show()



    # TO DO
    # get all price data for top 1000 coins (possibly add proper sleep with backoff / try again something simple) # back off does not work, maybe proxy needed / other startegy, cookies???
    # use interp on all
    # then what???????????????

    # latest_listing = load_pkled_df(CMC_SCRIPT_PATH / "latest_listing.pkl")
    # print(latest_listing.columns)
    # print(latest_listing)
    
    # btc = load_pkled_df(CMC_SCRIPT_PATH  / "close_price_history.pkl")
    # print(btc)





if __name__ == "__main__":

    # main()
    main_read()