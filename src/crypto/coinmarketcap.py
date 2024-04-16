import requests
import pandas as pd
from enum import Enum
from pathlib import Path
import json
import pickle

# to do
# use pickle
# build up data stored
# make build up mathods / queries for getting this data 

# id map
# latest listing
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

    cmc_api_key_path = Path(".") / "cmc_api_key.txt"
    with open(cmc_api_key_path, "r") as file:
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
    price_history_df['unix_timestamp'] = pd.to_datetime(price_history_df['unix_timestamp'], unit='s')

    # Drop the original 'price_history_df' column
    price_history_df = price_history_df.drop(columns=["chart_data_list"])

    return price_history_df

def load_pkled_df(path: str):

    path = Path(path)
    with open(path, "rb") as file:
        data: pd.DataFrame = pickle.load(file)

    return data
    

def main():
    
    
    id_map = get_id_map()
    id_map.to_pickle(CMC_SCRIPT_PATH / "id_map.pkl")

    latest_listing, tags_data = get_latest_listing()
    latest_listing.to_pickle(CMC_SCRIPT_PATH / "latest_listing.pkl")
    tags_data.to_pickle(CMC_SCRIPT_PATH / "tags_data.pkl")

    category_id_map = get_category_id_map()
    category_id_map.to_pickle(CMC_SCRIPT_PATH / "category_id_map.pkl")

    category_example = get_category("6617dd1bd0384836b9c7bdf3")
    category_example.to_pickle(CMC_SCRIPT_PATH / "category_example.pkl")



def main_read():

    # test = load_pkled_df(CMC_SCRIPT_PATH / "test.pkl")
    # print(test.columns)

    category_example = load_pkled_df(CMC_SCRIPT_PATH / "category_example.pkl")
    # print(category_example.columns)
    # print(category_example["num_tokens"])
    # print(category_example["market_cap"])
    # coin = list(category_example["coins"])
    # print(coin[0])

    coins_df = pd.json_normalize(list(category_example["coins"])[0])
    print(coins_df)
    



if __name__ == "__main__":

    # main()
    main_read()