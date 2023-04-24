from requests import Session
from bs4 import BeautifulSoup as bs
from time import sleep
import yfinance as yf
import pandas as pd

from ._utils import (YAHOO_CRYPTO_URL, 
                    BASE_HEADERS,
                    SOUP_PARSER)


tickers_per_response = 250 # maxium allowed by Yahoo Fianance


def crypto_by_rank(rank_range: list, output_file_path: str) -> None:
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
    """

    # Assert function args are valid
    for rank in rank_range:
        assert isinstance(rank, int)

    rank_range_length = len(rank_range)
    assert rank_range_length == 2, f"Expected 2 items, but {rank_range_length} items were given."

    assert isinstance(output_file_path, str)

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

    required_url_calls = int((end_rank - offset) / tickers_per_response)

    crypto_index_urls = []

    # Create a list of all required urls
    for url_call in range(required_url_calls):
        
        crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}?"
                                 f"offset=\{offset + url_call * tickers_per_response}&"
                                 f"count={tickers_per_response}")
    
    crypto_index_urls.append(f"{YAHOO_CRYPTO_URL}?"
                             f"offset={offset + required_url_calls * tickers_per_response}&"
                             f"count={end_rank-offset}")

    with open(output_file_path, 'w', encoding="utf-8") as output_file:
        output_file.truncate(0) # clear the output file
        output_file.write('name,ticker,marketCap\n')
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

                # Write crypto data to the output CSV
                output_file.write(f'{name},{ticker},{market_cap}\n')


def crypto_by_market_cap(market_cap_range: list, output_file_path: str) -> None:
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
    """

    # Assert function args are valid
    for rank in market_cap_range:
        assert isinstance(rank, int)

    mc_range_length = len(market_cap_range)
    assert mc_range_length == 2, f"Expected 2 items, but {mc_range_length} items were given."

    assert isinstance(output_file_path, str)

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

    with open(output_file_path, 'w', encoding="utf-8") as output_file:
        output_file.truncate(0) # clear the output file
        output_file.write('name,ticker,marketCap\n')
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
                    # Write to CSV if within mc range
                    output_file.write(f'{name},{ticker},{market_cap}\n')

            if market_cap <= end_mc:
                break


def check_duplicate_tickers(check_file_path: str, duplicates_file_path: str) -> str:
    """
    Retruns the percentage of duplicate tickers within a CSV file. Also, writting these
    to a seperate file.
    """

    duplicates = []

    with open(check_file_path, 'w+') as file:
        seen = set()
        cryptos = file.read().splitlines()

    with open(duplicates_file_path, 'w+') as dup_file:
        dup_file.truncate(0) # cleear the duplicate ticker output file
        for crypto in cryptos:
            crypto_lowercase = crypto.lower()

            # Checks if ticker seen twice
            if crypto_lowercase in seen:
                duplicates.append(crypto)
                dup_file.write(f'{crypto}\n')

            seen.add(crypto_lowercase)
            
    return str(len(duplicates)*100/len(file))


def get_price_history(input_file_path: str):
    """
    Returns the price history for each crypto from an input file.

    Args:
        input_file_path (str): input CSV path containing crypto data.
    """

    crypto_index_df = pd.read_csv(input_file_path)
    tickers = crypto_index_df

    return tickers




# use an SQL data base rather than csv files
# link index to crypto price history table


# backtesting function
# chart visualiser
    