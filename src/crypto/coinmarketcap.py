import json
from pathlib import Path
import requests
import pandas as pd
import time

# general functions

def df_to_json_file(data: pd.DataFrame, file_name: str, file_destination: str = ".", orient: str = "records") -> None:

    data = data.to_json(orient=orient)
    data = json.loads(data)

    if file_name.endswith(".json"):
        file_name = file_name.removesuffix(".json")

    file_destination = Path(file_destination)
    file_path = file_destination / f"{file_name}.json"

    with open(file_path, "w") as file:
        json.dump(data, file)

# Crypto market

def crypto_map():
    
    cmc_cryptos_url = "https://s3.coinmarketcap.com/generated/core/crypto/cryptos.json"

    cryptos_request = requests.get(cmc_cryptos_url)

    cryptos_request = json.loads(cryptos_request.text)

    df_columns = cryptos_request["fields"]
    df_data = cryptos_request["values"]
    crypto_map_df = pd.DataFrame(columns=df_columns, data=df_data)

    return crypto_map_df

def exchange_map():

    cmc_exchange_url = "https://s3.coinmarketcap.com/generated/core/exchange/exchanges.json"

    exchanges_request = requests.get(cmc_exchange_url)

    exchanges_request = json.loads(exchanges_request.text)

    df_columns = exchanges_request["fields"]
    df_data = exchanges_request["values"]
    exchange_map_df = pd.DataFrame(columns=df_columns, data=df_data)

    return exchange_map_df

def category_map():
    
    cmc_api_key_path = Path(".") / "cmc_api_key.txt"
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
    data = pd.DataFrame(data=data)

    return data

# Technical data

def ohlc_chart_data():
    ...

def close_chart_data():
    ...

def max_supply():
    ...

def category_data(category_id):

    cmc_api_key_path = Path(".") / "cmc_api_key.txt"
    with open(cmc_api_key_path, "r") as file:
        api_key = file.read()

    cmc_categories_url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/category?id={category_id}"

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(cmc_categories_url, headers=headers)

    data = json.loads(response.text)
    data = data["data"]

    data = pd.DataFrame(data=[data])

    return data

# coins, overview = category_data("60308028d2088f200c58a005")
# print(overview)
# print(coins.columns)
# Index(['id', 'name', 'symbol', 'slug', 'num_market_pairs', 'date_added',
#        'tags', 'max_supply', 'circulating_supply', 'total_supply', 'platform',
#        'is_active', 'infinite_supply', 'cmc_rank', 'is_fiat',
#        'self_reported_circulating_supply', 'self_reported_market_cap',
#        'tvl_ratio', 'last_updated', 'quote'],
#       dtype='object')

def tags():
    ...

def no_markets():
    ...


if __name__ == "__main__":

    category_map_df = pd.read_json("categories_map.json", orient="records")
    id = category_map_df["id"]
    counter = 1
    category_df = pd.DataFrame()
    for _id in id: 
        x = category_data(_id)
        print(f"{counter} / {len(id)}")
        counter  = counter + 1
        time.sleep(3)
        category_df = pd.concat([category_df, x], ignore_index=True)


    # print(len(category_df))

    # df_to_json_file(category_df, "full_category_map.json")

    # print(pd.read_json("full_category_map.json"))

    # Assuming 'json_data' contains your JSON data as a string

    with open("full_category_map.json", "r") as file:
        data = json.loads(file.read())
    
    x = pd.DataFrame(data=data)

    print(x["coins"][0][0]["tags"])