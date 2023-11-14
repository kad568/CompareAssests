import json
from pathlib import Path
import requests
import pandas as pd
import time
from enum import Enum
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FuncFormatter
from matplotlib.dates import AutoDateLocator, DateFormatter
import sqlite3
from pathlib import Path

# general functions

#lol delete this. Just use standard functions

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
    
    cmc_cryptos_map_url = "https://s3.coinmarketcap.com/generated/core/crypto/cryptos.json"

    cryptos_request = requests.get(cmc_cryptos_map_url)

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
    categories = pd.DataFrame(data=data)

    def _category_data(category_id):

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

    id = categories["id"]
    counter = 1
    category_df = pd.DataFrame()
    for _id in id: 
        category = _category_data(_id)
        print(f"{counter} / {len(id)}")
        counter  = counter + 1
        time.sleep(3)
        category_df = pd.concat([category_df, category], ignore_index=True)

    return data

###################### new + refractored code ########################

def get_coinmarketcap_id_map(cmc_api_key_path: Path = Path("."), cmc_api_key_file_name: str = "cmc_api_key.txt"):
    
    cmc_api_key_path = cmc_api_key_path / cmc_api_key_file_name
    with open(cmc_api_key_path, "r") as file:
        api_key = file.read()

    coinmarketcap_id_map_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    params = {
        "listing_status": "active,inactive",
    }

    response = requests.get(coinmarketcap_id_map_api_url, headers=headers, params=params)

    id_map_data: dict = response.json()
    id_map_data = id_map_data["data"]

    id_map_data: pd.DataFrame = pd.DataFrame(id_map_data)
    id_map_data = id_map_data.drop(columns="platform")

    return id_map_data

    # to do
    # make a platform db
    # replace platform data and add it to platform database

cmc_id_map_table_name = "cmc_id_map"

create_id_map_query = f'''
        CREATE TABLE IF NOT EXISTS {cmc_id_map_table_name} (
            assest_id INTEGER PRIMARY KEY,
            rank INTEGER,
            name TEXT,
            symbol TEXT,
            slug TEXT,
            is_active INTEGER,
            first_historical_data TEXT,
            last_historical_data TEXT
        )
    '''

def get_coinmarketcap_listing_latest(cmc_api_key_path: Path = Path("."), cmc_api_key_file_name: str = "cmc_api_key.txt", limit: int = 5000):

    cmc_api_key_path = cmc_api_key_path / cmc_api_key_file_name
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

    latest_listing_data: dict = response.json()
    latest_listing_data = latest_listing_data["data"]


    latest_listing_data: pd.DataFrame = pd.DataFrame(latest_listing_data)

    latest_listing_data = latest_listing_data.drop(columns=["platform", "quote", "tags"])

    # create new tags table and link to two 

    return latest_listing_data

latest_listing_table_name = "cmc_latest_listings"

create_latest_listing_table_query = f'''
        CREATE TABLE {latest_listing_table_name} (
            crypto_id REAL PRIMARY KEY,
            name TEXT,
            symbol TEXT,
            slug TEXT,
            num_market_pairs REAL,
            date_added TEXT,
            max_supply REAL,
            circulating_supply REAL,
            total_supply REAL,
            infinite_supply TEXT,
            cmc_rank REAL,
            self_reported_circulating_supply REAL,
            self_reported_market_cap REAL,
            tvl_ratio REAL,
            last_updated TEXT,
        )
    '''

class Range_options(Enum):

    DAILY = "1D"
    WEEKLY = "7D"
    MONTHLY = "1M"
    YEARLY = "1Y"
    ALL = "ALL"




def get_all_close_price_history(coin_id: int, range: str = Range_options.ALL.value):
    """
    Produces pandas dataframe of the price history of a given crypto with the following columns:
    - close usd
    - volume usd
    - marketcap usd
    - fixed supply (yes or no)
    - token supply
    """

    # set up request
    cmc_chart_api_base = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart"
    chart_api_params = {
        "id": str(coin_id),
        "range": range,
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

def create_all_price_history_database(file_path: Path, file_name: str = "crypto_data.db"):
    """
    Creates a database for the data produced by get_price_history().
    """

    # create the compolete file path for the database
    complete_file_path = file_path / file_name

    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(complete_file_path)

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create the table
    cursor.execute('''
        CREATE TABLE all_close_price_history (
            DataID INTEGER PRIMARY KEY,
            crypto_id INTEGER,
            unix_timestamp INTEGER
            close REAL,
            volume REAL,
            marketcap REAL,
            fixed_supply INTEGER
            FOREIGN KEY (crypto_id) REFERENCES crypto_info(crypto_id)
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def main():

    db_file_path = "."
    db_name = "crypto_data.db"
    db_file = Path(db_file_path) / db_name

    # get id_map_data
    id_map = get_coinmarketcap_id_map()

    latest_listing = get_coinmarketcap_listing_latest()

    # populate both tables
    with sqlite3.connect(db_file) as conn:

        id_map.to_sql(cmc_id_map_table_name, conn, if_exists="replace", index=False, schema=create_id_map_query)
        latest_listing.to_sql(latest_listing_table_name, conn, if_exists="replace", index=False, schema=create_latest_listing_table_query)



def main2():

    btc_price_history = get_all_close_price_history(14)

    time_stamp = btc_price_history["unix_timestamp"]
    price = btc_price_history["price_usd"]

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.yscale('log')
    ax.plot(time_stamp, price)
    ax.autoscale(enable=True, axis='both')

    # Customize y-axis tick labels
    def price_formatter(x, pos):
        return f"${x:,.0f}"

    formatter = FuncFormatter(price_formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.grid(which='minor', linestyle=':', linewidth=0.5)

    # Add more detail to x-axis timestamps
    date_formatter = DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_formatter)

    plt.xlabel('Timestamp')
    plt.ylabel('Price (USD)')
    plt.title('BTC-USD')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":

    # crypto_info = crypto_map()
    # print(len(crypto_info))
    # print(crypto_info.columns)
    # for col in crypto_info.columns:
    #     print(crypto_info[col][0]) 
    # filtered_crypto_info = crypto_info[crypto_info['is_active'] == 0]

    # print(len(filtered_crypto_info))

    main()
    # crypto_id_map = get_coinmarketcap_id_map()
    # print(crypto_id_map.columns)
    # print(crypto_id_map)
    # print(len(crypto_id_map))

    # latest_listing = get_coinmarketcap_listing_latest()
    # print(latest_listing)
    # print(latest_listing.columns)
    # print(len(latest_listing))
