import json
from pathlib import Path
import requests
import pandas as pd
import time
from enum import Enum, Flag
import matplotlib.pyplot as plt
import sqlite3
from pathlib import Path
import numpy as np
import matplotlib.dates as mdates
import logging
import inspect
import shutil

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

    cmc_categories_url = "https://pro-api.coinmarketcap.com/v1//categoricryptocurrencyes"

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
            id INTEGER PRIMARY KEY,
            rank INTEGER,
            name TEXT,
            symbol TEXT,
            slug TEXT,
            is_active INTEGER,
            first_historical_data TEXT,
            last_historical_data TEXT
        )
    '''

def get_coinmarketcap_listing_latest(cmc_api_key_path: Path = Path("."), cmc_api_key_file_name: str = "cmc_api_key.txt", limit: int = 50):

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

class Data_Range_options(Enum):

    DAILY = "1D"
    WEEKLY = "7D"
    MONTHLY = "1M"
    YEARLY = "1Y"
    ALL = "ALL"


def get_all_close_price_history(coin_id: int, range: str = Data_Range_options.ALL.value):
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

def create_all_price_history_database(file_path: Path, file_name: str = "crypto_data.db"):
    """
    Creates a database for the data produced by get_price_history().
    """

    # create the compolete file path for the database
    complete_file_path = Path(file_path) / file_name

    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(complete_file_path)

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # cursor.execute('DROP TABLE IF EXISTS all_close_price_history')

    # Create the table
    cursor.execute('''          
        CREATE TABLE IF NOT EXISTS all_close_price_history (
        DataID INTEGER PRIMARY KEY,
        id INTEGER,
        unix_timestamp INTEGER,
        close_usd REAL,
        volume_usd REAL,
        mc_usd REAL,
        fixed_supply REAL,
        supply REAL,
        FOREIGN KEY (id) REFERENCES cmc_id_map(id)
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def add_all_close_price_to_db(id: int, db_path: str = ".", db_name: str = "crypto_data.db"):

    complete_path = Path(db_path) / db_name
    create_all_price_history_database(file_path=db_path)
    price_history = get_all_close_price_history(id)
    price_history["id"] = id
    conn = sqlite3.connect(complete_path)
    price_history.to_sql("all_close_price_history", conn, if_exists="append", index=False)


####### refactored again #########
    
# to do list
    # consider adding the create table query with primary and foreign keys (watch out remeber can't create foreign key if primary not made so order of creation maters) 
    # consider changing the table variables Enum to include the types also state these types in another ENum
        # why, I want less hard coded values in the create table 
        # maybe nested enums to include both? research that #### found a very good solution see the example below
    
    # use date data types for db then use parse dates in read_sql

# Configure logging
logging.basicConfig(filename='cmc.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

# Constant paths and varaibles
CMC_SCRIPT_PATH = Path(__file__).parent.resolve()

CMC_API_KEY_FILE_PATH = CMC_SCRIPT_PATH / "cmc_api_key.txt"

DEFAULT_DB_FILE_PATH = CMC_SCRIPT_PATH / "crypto_data4.db"

class SQL_TYPES(Enum):

    INTEGER = "INTEGER"
    TEXT = "TEXT"
    REAL = "REAL"
    BOOL = "BOOL"
    DATETIME = "DATETIME"
    BIGINT = "BIGINT"

# cmc id map functionality
CMC_ID_MAP_TABLE_NAME = "cmc_id_map"

class CMC_ID_MAP_VARIABLES(Enum):

    ID = "cmc_id", SQL_TYPES.TEXT.value
    RANK = "rank", SQL_TYPES.INTEGER.value
    NAME = "name", SQL_TYPES.TEXT.value
    SYMBOL = "symbol", SQL_TYPES.TEXT.value
    SLUG = "slug", SQL_TYPES.TEXT.value
    IS_ACTIVE = "is_active", SQL_TYPES.BOOL.value
    FIRST_HISTORICAL_DATA = "first_recorded", SQL_TYPES.DATETIME.value
    LAST_HISTORICAL_DATA = "last_recorded", SQL_TYPES.DATETIME.value

    @property
    def name(self):
        return self.value[0]
    
    @property
    def sql_type(self):
        return self.value[1]
    

def get_id_map(cmc_api_key_file_path: str = CMC_API_KEY_FILE_PATH) -> pd.DataFrame:

    # getting cmc api key
    try:
        with open(cmc_api_key_file_path, "r") as file:
            api_key = file.read()
            logging.info(f"got api key: {api_key}")

    except Exception as e:
        logging.error(f"Error occured while reading the cmc api key file: {e}")
        raise

    cmc_id_map_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    params = {
        "listing_status": "active,inactive",
    }

    # call to the cmc id map api 
    try:
        response = requests.get(cmc_id_map_api_url, headers=headers, params=params)
        logging.info(f"request: {response.request.method} | {response.request.url}")
        response.raise_for_status()

    except Exception as e:
        logging.error(f"failed to get response: {e}")
        raise
    
    # manipulating id map api call data
    try:
        id_map_data: dict = response.json()
        id_map_data = id_map_data["data"]

        id_map_data: pd.DataFrame = pd.DataFrame(id_map_data)
        logging.info(f"raw id map df: \n{id_map_data.head()}")
        id_map_data = id_map_data.drop(columns="platform")

        id_map_data = id_map_data.rename(columns={
            "id": CMC_ID_MAP_VARIABLES.ID.name,
            "rank": CMC_ID_MAP_VARIABLES.RANK.name,
            "name": CMC_ID_MAP_VARIABLES.NAME.name,
            "slug": CMC_ID_MAP_VARIABLES.SLUG.name,
            "is_active": CMC_ID_MAP_VARIABLES.IS_ACTIVE.name,
            "first_historical_data": CMC_ID_MAP_VARIABLES.FIRST_HISTORICAL_DATA.name,
            "last_historical_data": CMC_ID_MAP_VARIABLES.LAST_HISTORICAL_DATA.name 
            })
        logging.info(f"returned df: \n{id_map_data.head()}")
    
    except Exception as e:
        logging.error(f"error converting id map data to a pandas dataframe: {e}")
        raise

    return id_map_data

# cmc latest listing functionality
CMC_LATEST_LISTING_TABLE_NAME = "cmc_latest_listings"

class CMC_LATEST_LISTING_VARIABLE_NAMES(Enum):

    ID = CMC_ID_MAP_VARIABLES.ID.name, CMC_ID_MAP_VARIABLES.ID.sql_type
    NUM_MARKET_PAIRS = "num_market_pairs", SQL_TYPES.TEXT.value
    MAX_SUPPLY = "max_supply", SQL_TYPES.TEXT.value
    CIRCULATING_SUPPLY = "circulating_supply", SQL_TYPES.TEXT.value
    TOTAL_SUPPLY = "total_supply", SQL_TYPES.TEXT.value
    INFINITE_SUPPLY = "infinite_supply", SQL_TYPES.BOOL.value
    SELF_REPORTED_CIRCULATING_SUPPLY = "self_reported_supply", SQL_TYPES.TEXT.value
    SELF_REPORTED_MC = "self_reported_mc", SQL_TYPES.TEXT.value
    TVL_RATIO = "tvl_ratio", SQL_TYPES.TEXT.value
    LAST_UPDATED = "last_updated", SQL_TYPES.DATETIME.value

    @property
    def name(self):
        return self.value[0]
    
    @property
    def sql_type(self):
        return self.value[1]

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

    tags_data = tags_data.rename(columns={
        "id": CMC_TAGS_VARIABLE_NAMES.ID.name,
        "tag": CMC_TAGS_VARIABLE_NAMES.TAGS.name
    })

    latest_listing_data = latest_listing_data.drop(columns=["platform", "quote", "tags", "name", "symbol", "cmc_rank", "date_added", "slug"])

    latest_listing_data = latest_listing_data.rename(columns={
        "id": CMC_LATEST_LISTING_VARIABLE_NAMES.ID.name,
        "num_market_pairs": CMC_LATEST_LISTING_VARIABLE_NAMES.NUM_MARKET_PAIRS.name,
        "circulating_supply": CMC_LATEST_LISTING_VARIABLE_NAMES.CIRCULATING_SUPPLY.name,
        "total_supply": CMC_LATEST_LISTING_VARIABLE_NAMES.TOTAL_SUPPLY.name,
        "max_supply": CMC_LATEST_LISTING_VARIABLE_NAMES.MAX_SUPPLY.name,
        "infinite_supply": CMC_LATEST_LISTING_VARIABLE_NAMES.INFINITE_SUPPLY.name,
        "last_updated": CMC_LATEST_LISTING_VARIABLE_NAMES.LAST_UPDATED.name,
        "tvl_ratio": CMC_LATEST_LISTING_VARIABLE_NAMES.TVL_RATIO.name,
        "self_reported_circulating_supply": CMC_LATEST_LISTING_VARIABLE_NAMES.SELF_REPORTED_CIRCULATING_SUPPLY.name,
        "self_reported_market_cap": CMC_LATEST_LISTING_VARIABLE_NAMES.SELF_REPORTED_MC.name
        })

    # create new tags table and link to two 

    return latest_listing_data, tags_data

# cmc tags functionality
CMC_TAGS_TABLE_NAME = "cmc_tags"

class CMC_TAGS_VARIABLE_NAMES(Enum):

    ID = CMC_ID_MAP_VARIABLES.ID.name, CMC_ID_MAP_VARIABLES.ID.sql_type
    TAGS = "tags", SQL_TYPES.TEXT.value

    @property
    def name(self):
        return self.value[0]
    
    @property
    def sql_type(self):
        return self.value[1]

# cmc category functionality
CMC_CATEGORY_TABLE_NAME = "cmc_category_map"

class CMC_CATEGORY_VARIABLE_NAMES(Enum):

    ID = "cmc_category_id", SQL_TYPES.TEXT.value
    NAME = "name", SQL_TYPES.TEXT.value
    TITLE = "title", SQL_TYPES.TEXT.value
    DESCRIPTION = "description", SQL_TYPES.TEXT.value
    NUM_TOKENS = "num_tokens", SQL_TYPES.INTEGER.value
    AVG_PRICE_CHANGE = "avg_price_change", SQL_TYPES.REAL.value
    MARKET_CAP = "mc", SQL_TYPES.REAL.value
    MARKET_CAP_CHANGE = "mc_change", SQL_TYPES.REAL.value
    VOLUME = "volume", SQL_TYPES.REAL.value
    VOLUME_CHANGE = "volume_change", SQL_TYPES.REAL.value
    LAST_UPDATED = "last_updated", SQL_TYPES.DATETIME.value

    @property
    def name(self):
        return self.value[0]
    
    @property
    def sql_type(self):
        return self.value[1]


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
    
    categories = categories.rename(columns={
        "id": CMC_CATEGORY_VARIABLE_NAMES.ID.name,
        "name": CMC_CATEGORY_VARIABLE_NAMES.NAME.name,
        "title": CMC_CATEGORY_VARIABLE_NAMES.TITLE.name,
        "description": CMC_CATEGORY_VARIABLE_NAMES.DESCRIPTION.name,
        "num_tokens": CMC_CATEGORY_VARIABLE_NAMES.NUM_TOKENS.name,
        "avg_price_change": CMC_CATEGORY_VARIABLE_NAMES.AVG_PRICE_CHANGE.name,
        "market_cap": CMC_CATEGORY_VARIABLE_NAMES.MARKET_CAP.name,
        "market_cap_change": CMC_CATEGORY_VARIABLE_NAMES.MARKET_CAP_CHANGE.name,
        "volume": CMC_CATEGORY_VARIABLE_NAMES.VOLUME.name,
        "volume_change": CMC_CATEGORY_VARIABLE_NAMES.VOLUME_CHANGE.name,
        "last_updated": CMC_CATEGORY_VARIABLE_NAMES.LAST_UPDATED.name
    })
    # would it not be bettwe just to rename what needs to
    # what abut setting the sql types, you would still need Enum or a different and less complex solution, but one would be neededa    
    logging.info(f"category df: {categories.head()}")

    return categories


# cmc price history functionality
CMC_PRICE_HISTORY_TABLE_NAME = ...

class CMC_PRICE_HISTORY_VARIABLE_NAMES(Enum):...

def get_price_history():...

# db management functionality
def store_data_to_db(data: pd.DataFrame, colomns_variables: Enum, table_name: str, db_file_path: str = DEFAULT_DB_FILE_PATH) -> None:

    try:
        dtypes = {col.name: str(col.sql_type) for col in colomns_variables}
        logging.info(f"summary of data: {data.dtypes}")
        logging.info(f"dtypes: {dtypes}")
        with sqlite3.connect(db_file_path) as conn:  
            # store data to table
            data.to_sql(table_name, conn, if_exists="append", index=False, dtype=dtypes)
        logging.info(f"stored data to db at table {table_name}")

    # what happens if there are multiple primary and foreign keys??
    # should create table be its own this
    except Exception as e:
        logging.error(f"failed to save data to db: {e}")
        raise

    # except pd.errors as e:
    #     logging.error(f"failed to convert df and store data to sql table: {e}")
    #     raise 

def drop_table(table_name: str, db_file_path: str = DEFAULT_DB_FILE_PATH) -> None:

    try:
        with sqlite3.connect(db_file_path) as conn:
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    except sqlite3.Error as e:
        logging.error(f"Error occured while dropping table: {e} | {e.sqlite_errorcode} | {e.sqlite_errorname}")
        raise

def read_from_table(table_name: str, db_file_path: str = DEFAULT_DB_FILE_PATH) -> pd.DataFrame:

    try:
        with sqlite3.connect(db_file_path) as conn:
            data = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            logging.info(f"data has been read from db: {data.head()}")
            return data

    except Exception as e:
        logging.error(f"error reading table from db: {e}")
        raise

def remove_duplicates_from_table(table_name: str, db_file_path:str = DEFAULT_DB_FILE_PATH) -> None:

    try:
        with sqlite3.connect(db_file_path) as conn:
            conn.execute(f"""
                DELETE FROM {table_name}
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM {table_name}
                    GROUP BY ALL *
                );
            """)
    except sqlite3.Error as e:
        logging.error(f"Error removing duplicates: {e} | {e.sqlite_errorcode} | {e.sqlite_errorname}")
        raise

def backup_database(db_file_path: str = DEFAULT_DB_FILE_PATH, db_copy_path: str = Path(DEFAULT_DB_FILE_PATH).parent, copy_abrv: str = "_copy") -> None:

    try:
        db_copy_file_name = f"{Path(db_file_path).name.split('.')[0]}{copy_abrv}.db"

        db_copy_file_path = db_copy_path / db_copy_file_name
        logging.info(f"db copy file path: {db_copy_file_path}")

        shutil.copyfile(db_file_path, db_copy_file_path)
    
    except Exception as e:
        logging.error(f"failed to backup db: {e}")
        raise
    
def create_table(table_name: str, colomn_variables: Enum, ref_table_name: str = None, primary_key: Enum = None, foreign_key: Enum = None, db_file_path: str = DEFAULT_DB_FILE_PATH) -> None:

    try:
        with sqlite3.connect(db_file_path) as conn:
            table_format = [
                    f"{col.name} {col.sql_type} PRIMARY KEY" if col.name is primary_key 
                    else f"{col.name} {col.sql_type}" for col in colomn_variables
            ]
            if foreign_key:
                table_format.append(f"FOREIGN KEY ({foreign_key}) REFERENCES {ref_table_name}({foreign_key})")

            conn.execute(f"""CREATE TABLE {table_name} ({', '.join(table_format)})""")
    
    except sqlite3.Error as e:
        logging.error(f"failed to create the table: {e} | {e.sqlite_errorcode} | {e.sqlite_errorname}")
        raise

def main():

    def id_map():
        drop_table(CMC_ID_MAP_TABLE_NAME)
        create_table(CMC_ID_MAP_TABLE_NAME, CMC_ID_MAP_VARIABLES, primary_key=CMC_ID_MAP_VARIABLES.ID.name)
        data = get_id_map()
        store_data_to_db(data, CMC_ID_MAP_VARIABLES, CMC_ID_MAP_TABLE_NAME)
    
    latest_listing_data, tags_data = get_latest_listing(limit=5000)
    latest_listing_data = latest_listing_data.astype(str) # dtype seems to not be honored explaining why it wants to use SQLite integers not those specified
    # print(latest_listing_data.max())

    def make_latest_listing():
        drop_table(CMC_LATEST_LISTING_TABLE_NAME)
        create_table(CMC_LATEST_LISTING_TABLE_NAME, CMC_LATEST_LISTING_VARIABLE_NAMES, foreign_key=CMC_LATEST_LISTING_VARIABLE_NAMES.ID.name, ref_table_name=CMC_ID_MAP_TABLE_NAME, primary_key=CMC_LATEST_LISTING_VARIABLE_NAMES.ID.name)
        store_data_to_db(latest_listing_data, CMC_LATEST_LISTING_VARIABLE_NAMES, CMC_LATEST_LISTING_TABLE_NAME)
        # this is working in pandas and it does not know the types, best tp specify all types in the .to_SQL part to avoid integer overflow (done, but need to check)
        # do this for all, use the dtyes and the types already given in a dict comprehension to specifiy the types before conversion (done)
    
    def tags_map():
        drop_table(CMC_TAGS_TABLE_NAME)
        create_table(CMC_TAGS_TABLE_NAME, CMC_TAGS_VARIABLE_NAMES, foreign_key=CMC_TAGS_VARIABLE_NAMES.ID.name, ref_table_name=CMC_ID_MAP_TABLE_NAME)
        store_data_to_db(tags_data, CMC_TAGS_VARIABLE_NAMES, CMC_TAGS_TABLE_NAME)

    def category_id_map():
        drop_table(CMC_CATEGORY_TABLE_NAME)
        create_table(CMC_CATEGORY_TABLE_NAME, CMC_CATEGORY_VARIABLE_NAMES, primary_key=CMC_CATEGORY_VARIABLE_NAMES.ID.name)
        data = get_category_id_map()
        store_data_to_db(data, CMC_CATEGORY_VARIABLE_NAMES, CMC_CATEGORY_TABLE_NAME)

    def categories_data():
        ...

    id_map()
    make_latest_listing()
    tags_map()
    category_id_map()


    # to do
    # try converting everything into str before .to_sql, then keep the correct types when creating the table, then see what happens to types when you read in the data, does python use the types stated in SQL or are they still all strings as stated initially
    # maybe go to the pandas page for help and support

    # switch to SQL ALCHEMY and see if dtypes works then when used correctly, as this is actually supported by pandas
        # could remove sql_types maybe

    
    

    
    # df = read_from_table(CMC_ID_MAP_TABLE_NAME)

def main2():

    add_all_close_price_to_db(1027)

    # btc_price_history = get_all_close_price_history(1)
    # print(btc_price_history)

    # # print((btc_price_history["unix_timestamp"]))
    # time = btc_price_history["unix_timestamp"].iloc[:-1]
    # time_interval = time.diff().mean()
    # print(time.iloc[0])
    # print(time_interval)

    # diff = price.d
    # plt.plot(btc_price_history["unix_timestamp"], btc_price_history["mc_usd"]/btc_price_history["close_usd"])
    # # plt.plot(btc_price_history["unix_timestamp"], btc_price_history["fixed_supply"])
    # plt.yscale("log")
    # plt.show()
    # print(btc_price_history)
    # eth_price_history = get_all_close_price_history(3890)

    # eth_btc_merge = pd.merge(btc_price_history, eth_price_history, on="unix_timestamp", suffixes=("_btc", "_eth"))
    # eth_btc_merge["unix_timestamp"] = pd.to_datetime(eth_btc_merge["unix_timestamp"])

    # eth_btc = eth_btc_merge["close_usd_eth"] / eth_btc_merge["close_usd_btc"]

    # btc_price_history["unix_timestamp"] = pd.to_datetime(btc_price_history["unix_timestamp"])
    # btc_price_history["time_numeric"] = mdates.date2num(btc_price_history["unix_timestamp"])

    # plt.plot(eth_btc_merge["unix_timestamp"], eth_btc_merge["supply_btc"])
    # plt.plot(btc_price_history["unix_timestamp"], btc_price_history["supply"])
    # plt.yscale("log")
    # # plt.title('ETHBTC')
    # plt.show()

if __name__ == "__main__":

    main()