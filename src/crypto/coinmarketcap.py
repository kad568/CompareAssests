import json
from pathlib import Path
import requests
import pandas as pd

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

# crypto_map_df = crypto_map()
# df_to_json_file(crypto_map_df, "crypto_map.json")

def exchange_map():

    cmc_exchange_url = "https://s3.coinmarketcap.com/generated/core/exchange/exchanges.json"

    exchanges_request = requests.get(cmc_exchange_url)

    exchanges_request = json.loads(exchanges_request.text)

    df_columns = exchanges_request["fields"]
    df_data = exchanges_request["values"]
    exchange_map_df = pd.DataFrame(columns=df_columns, data=df_data)

    return exchange_map_df

# exchange_map_json_str = exchange_map().to_json(orient="records")
# exchange_map_json = json.loads(exchange_map_json_str)
# save_json_to_file(exchange_map_json, "exchange_map.json")

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

categories_df = category_map()
df_to_json_file(categories_df, "categories_map.json")


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
    coins = data["data"]["coins"]
    del data["data"]["coins"]
    overview = data["data"]

    coins = pd.DataFrame(data=coins)

    return coins, overview

coins, _ = category_data("60308028d2088f200c58a005")
# print(coins.columns)
# Index(['id', 'name', 'symbol', 'slug', 'num_market_pairs', 'date_added',
#        'tags', 'max_supply', 'circulating_supply', 'total_supply', 'platform',
#        'is_active', 'infinite_supply', 'cmc_rank', 'is_fiat',
#        'self_reported_circulating_supply', 'self_reported_market_cap',
#        'tvl_ratio', 'last_updated', 'quote'],
#       dtype='object')

print(coins["tags"].head())

def tags():
    ...

def no_markets():
    ...