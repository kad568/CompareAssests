import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup as bs
import chompjs



CHAIN_EXPOSED_BASE_URL = "https://chainexposed.com"

def get_short_term_holder_realised_price_histroty(): 

    short_term_holder_realised_price_url = f"{CHAIN_EXPOSED_BASE_URL}/XthRealizedPriceShortTermHolder.html"

    response = requests.get(short_term_holder_realised_price_url)
    soup = bs(response.text, "html.parser")
    scripts = soup.find_all('script')
    plot_script_raw = scripts[5].text
    plot_data_dict = list(chompjs.parse_js_objects(plot_script_raw)) 
    print(plot_data_dict)
    # got trace 1 and 2, just disect the raw dictioanry
    return 0

def run_script():
    
    STH_price_history = get_short_term_holder_realised_price_histroty()

if __name__ == "__main__":
    run_script()



