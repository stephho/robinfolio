import os
import json
import requests
from dotenv import load_dotenv


# robinhood api credentials 
load_dotenv()
rh_api_token = os.environ.get('RH_TOKEN')


# robinhood api urls
rh_orders_url = 'https://api.robinhood.com/orders/'
rh_stocks_url = 'https://api.robinhood.com/instruments/'

rh_header = {
    'authority':'api.robinhood.com', 
    'authorization':'Bearer ' + rh_api_token, 
    'accept':'*/*',
    'referrer':'https://robinhood.com/',
    'accept-language':'en-US,en;q=0.9',
    'x-robinhood-api-version':'1.431.4',
    'Content-Type':'application/json'
}


def get_stock_name(instrument_id): 
    """
    Get a stock's ticker symbol and full name, given Robinhood's instrument ID for that stock 

    Args:  
        instrument_id (str): Robinhood instrument ID, unique for each stock 
    
    Returns: 
        (tuple): Stock ticker symbol, stock name. Example: 'AAPL' is the stock ticker symbol, 'Apple' is the stock name
    """
    instrument_url = rh_stocks_url + instrument_id + '/'
    response = requests.get(instrument_url) # does not require authentication 
    response = json.loads(response.text)
    stock_ticker = response['symbol']
    stock_name = response['simple_name'] 
    return (stock_ticker, stock_name)

    
def get_order_history(instrument_id=None): 
    """
    Get all filled (i.e. completed) buy and sell orders in a Robinhood account's history 

    Args:  
        instrument_id (str): Optional filter for filled orders for a particular stock. If no instrument_id is passed, filled orders for all stocks will be returned 
    
    Returns: 
        all_orders (list): A list of dictionaries, where each dictionary is an order and its associated information 
    """
    all_orders = []
    response = requests.get(rh_orders_url, headers=rh_header)
    results = json.loads(response.text)['results'] 
    next_page = json.loads(response.text)['next']

    for r in results: 
        # filter out cancelled or unfilled orders 
        if r['side'] in ['buy', 'sell'] and r['state'] == 'filled': 
            if instrument_id == None: 
                all_orders.append(r) 
            else: 
                if r['instrument_id'] == instrument_id: 
                    all_orders.append(r)
    
    while next_page: 
        response = requests.get(next_page, headers=rh_header)
        results = json.loads(response.text)['results']
        next_page = json.loads(response.text)['next']
        for r in results: 
            if r['side'] in ['buy', 'sell'] and r['state'] == 'filled':
                if instrument_id == None: 
                    all_orders.append(r) 
                else: 
                    if r['instrument_id'] == instrument_id: 
                        all_orders.append(r)
    
    return all_orders 