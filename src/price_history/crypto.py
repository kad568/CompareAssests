from requests import Session
from bs4 import BeautifulSoup as bs
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from math import ceil
import json
from pathlib import Path

from ._price_history_utils import (YAHOO_CRYPTO_URL, 
                    BASE_HEADERS,
                    SOUP_PARSER)


tickers_per_response = 250 # maxium allowed by Yahoo Fianance


def crypto_by_rank(rank_range: list) -> pd.DataFrame:
    """
    Saves the name, ticker and market capitalization of cryptos within a given rank range to a CSV.

    Args:
        rank_range (list): A list of the two integers, the start and end rank. For example,
            [1, 100], would fetch the top 100 coins. Whereas, [1, -1], would fetch all coins.
        output_file_path (str): The file path of the output CSV.

    Returns:
        None and a text file
    
    Examples:
        >>> crypto_by_rank([1, 10], 'top10cryptos.csv')
        # Fetches the top 10 cryptocurrencies and saves them to top10cryptos.csv

    OUT OF DATE
    """

    # Assert function args are valid
    for rank in rank_range:
        assert isinstance(rank, int)

    rank_range_length = len(rank_range)
    assert rank_range_length == 2, f"Expected 2 items, but {rank_range_length} items were given."

    start_rank = rank_range[0]
    end_rank = rank_range[1]

    session = Session()

    if end_rank <= 0:   
        # Get total number of crypto tickers on Yahoo Finance
        response = session.get(YAHOO_CRYPTO_URL, headers=BASE_HEADERS)
        soup = bs(response.content, SOUP_PARSER)

        total_coins_class = {'class': 'Mstart(15px) Fw(500) Fz(s)'}
        total_coins_tags = soup.find('span', attrs=total_coins_class)
        total_number_of_coins: str = total_coins_tags.text.split()[2]
        end_rank += int(total_number_of_coins)

    offset = start_rank - 1

    required_url_calls = ceil((end_rank - offset) / tickers_per_response)

    crypto_index_urls = []

    # Create a list of all required urls
    for url_call in range(required_url_calls - 1):
        
        crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}?"
                                 f"offset={offset + url_call * tickers_per_response}&"
                                 f"count={tickers_per_response}")
    
    crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}?"
                             f"offset={offset + (required_url_calls - 1) * tickers_per_response}&"
                             f"count={(end_rank - offset) % tickers_per_response}")
    
    crypto_index_df = pd.DataFrame(columns=["Rank", "Name", "Ticker", "MarketCap"])
    rank_counter = start_rank

    for url in crypto_index_urls:
        # Collect the respone content from each url
        response = session.get(url, headers=BASE_HEADERS)
        soup = bs(response.content, SOUP_PARSER)

        crypto_tags = soup.find_all('tr')[1:]
        
        for crypto in crypto_tags:
            # Extract relavent data for each crypto
            ticker_tag_class = {'aria-label': 'Symbol'}
            ticker = crypto.find('td', attrs=ticker_tag_class).text

            name_tag_class = {'aria-label': 'Name'}
            name = crypto.find('td', attrs=name_tag_class).text

            mc_tag_class = {'data-field': 'marketCap'}
            market_cap = crypto.find('fin-streamer', attrs=mc_tag_class)['value']
            
            crypto_index = pd.DataFrame(data={"Rank": rank_counter,
                                              "Name": [name], 
                                              "Ticker": [ticker], 
                                              "MarketCap": [market_cap]})
            
            rank_counter += 1

            # Add all varibles to the dataframe
            crypto_index_df = pd.concat([crypto_index_df, 
                                         crypto_index], ignore_index=True)
            
    return crypto_index_df


def crypto_by_market_cap(market_cap_range: list) -> pd.DataFrame:
    """
    Saves the name, ticker and market capitalization of cryptos within a given market 
    capitalization range to a CSV.

    Args:
        market_cap_range (list): A list of the two integers, the start and end market capitalization. For example,
            [1_000_000, 0], would fetch coins with a market capitalization of less than 1 million.
        output_file_path (str): The file path of the output CSV.

    Returns:
        None and a text file
    
    Examples:
        >>> crypto_by_mc([1_000_000, 10], 'top_1_million_mc_cryptos.csv')
        # Fetches cryptocurrencies with a market capitalization of less than 1 million saves them to top_1_million_mc_cryptos.csv
        
    OUT OF DATE
    """

    # Assert function args are valid
    for rank in market_cap_range:
        assert isinstance(rank, int)

    mc_range_length = len(market_cap_range)
    assert mc_range_length == 2, f"Expected 2 items, but {mc_range_length} items were given."

    start_mc = market_cap_range[0]
    end_mc = market_cap_range[1]

    session = Session()

    # Get the total number of cryptos on Yahoo Finance
    response = session.get(YAHOO_CRYPTO_URL, headers=BASE_HEADERS)
    soup = bs(response.content, SOUP_PARSER)  

    total_coins_class = {'class': 'Mstart(15px) Fw(500) Fz(s)'}
    total_coins_tags = soup.find('span', attrs=total_coins_class)
    total_number_of_coins: str = total_coins_tags.text.split()[2]

    required_url_calls = int(total_number_of_coins / tickers_per_response)

    crypto_index_urls = []

    # Create a list of all required urls
    for url_call in range(required_url_calls):
        crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}?"
                                 f"offset={url_call * tickers_per_response}&"
                                 f"count={tickers_per_response}")
    
    crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}={url_call * tickers_per_response}&count={total_number_of_coins}")

    crypto_index_df = pd.DataFrame(columns=["Name", "Ticker", "MarketCap"])

    for url in crypto_index_urls:
        # Collect the respone content from each url
        response = session.get(url, headers=BASE_HEADERS)
        soup = bs(response.content, SOUP_PARSER)

        crypto_tags = soup.find_all('tr')[1:]
        
        for tag in crypto_tags:    
            # Extract relavent data for each crypto
            ticker_tag_class = {'aria-label': 'Symbol'}
            ticker = tag.find('td', attrs=ticker_tag_class).text

            name_tag_class = {'aria-label': 'Name'}
            name = tag.find('td', attrs=name_tag_class).text

            mc_tag_class = {'data-field': 'marketCap'}
            market_cap = tag.find('fin-streamer', attrs=mc_tag_class)['value']
            market_cap = int(market_cap)

            if end_mc <= market_cap <= start_mc:
                crypto_index = pd.DataFrame(data={"Name": [name], 
                                                  "Ticker": [ticker], 
                                                  "MarketCap": [market_cap]})
            # Add all varibles to the dataframe
            crypto_index_df = pd.concat([crypto_index_df, 
                                         crypto_index], 
                                         ignore_index=True)           

        if market_cap <= end_mc:
            break
    
    return crypto_index_df


def check_duplicate_tickers(crypto_index_df: pd.DataFrame) -> pd.DataFrame:
    """
    Retruns the percentage of duplicate tickers within a CSV file. Also, writting these
    to a seperate file.
    """

    duplicates = []
    seen = set()
    crypto_index = crypto_index_df.values

    for crypto in crypto_index:
        # Checks if ticker seen twice
        if crypto_index_df in seen:
            duplicates.append(crypto)

        seen.add(crypto)

    duplicates_df = pd.DataFrame(duplicates, columns=["Rank", "name", "ticker", "marketCap"])
            
    return duplicates_df


def get_price_history(search_method: object, range: list, database_name: str) -> list:
    """
    Returns the price history for each crypto from an input file.

    Args:
        input_file_path (str): input CSV path containing crypto data.
    """

    crypto_index: pd.DataFrame =  search_method(range)
    tickers = crypto_index["Ticker"].to_list()

    crypto_price_history = yf.download(tickers, group_by='Ticker', auto_adjust=True)
    crypto_price_history = crypto_price_history.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1)

    engine = create_engine(f"sqlite:///{database_name}")

    crypto_index.to_sql("index", engine, if_exists="replace", index=False)
    crypto_price_history.to_sql("price_history", engine, if_exists="replace", index=True)

    return crypto_price_history

def read_price_history(database_path: str):

    engine = create_engine(f"sqlite:///{database_path}")
    
    with engine.connect() as connection:
        price_history = pd.read_sql_table("price_history", connection)
        price_history = price_history.sort_values(by=["Date"])

        price_history = price_history.groupby("Ticker")

        crypto_index = pd.read_sql_table("index", connection)
        crypto_index = crypto_index.dropna()

    return (crypto_index, price_history)

def get_categories(save = True, save_location = "."):
    """
    gets the crypto categories listed on coinmarketcap.com

    :param: save Option to save categories to a json file
    """
    
    with open("./price_history/coinmarketcap_api_key.txt", "r") as file:
        api_key = file.read()

    coinmarketcap_api_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories'

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    session = Session()

    session.headers.update(headers)

    response = session.get(coinmarketcap_api_url)

    data = json.loads(response.text)

    # extract and format data

    crypto_categories = {"name": [], 
                         "id": []}

    for category in data["data"]:
        category_name = category["name"]
        crypto_categories["name"].append(category_name)

        category_id = category["id"]
        crypto_categories["id"].append(category_id)
        
        category_id, category_name = None, None

    crypto_categories_df = pd.DataFrame(data=crypto_categories)

    def _save(location: str = "."):

        crypto_categories_json = crypto_categories_df.to_json()

        with open(f"{location}/crypto_categories.json", "w") as file:
            json.dump(crypto_categories_json, file)

    if save:
        _save(save_location)
    
    return crypto_categories_df


def crypto_by_category(crypto_categories_df: pd.DataFrame, category_id: str):


    with open("./price_history/coinmarketcap_api_key.txt", "r") as file:
        api_key = file.read()

    coinmarketcap_api_url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/category?id={category_id}'

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
    }

    session = Session()

    session.headers.update(headers)

    response = session.get(coinmarketcap_api_url)

    data = json.loads(response.text)

    print(data)

    for 

        # add each to df
        # crypto_categories_df.

    # category_ids = data["data"]["id"]
    # category_names = data["data"]["name"]

    # crypto_categories = pd.DataFrame(data={
    #     "name": category_names,
    #     "id": category_ids
    #     }
    # )

    # print(crypto_categories)

#     if save:
#             with open("crypto_categories.json", "w") as file:
#                 json.dump(data, file)

# def _load_categories():

#     with open("crypto_categories.json", "r") as file:
#         data = json.loads(file.read())
#         print(data["data"][0])
#     return data

#     _load_categories()
