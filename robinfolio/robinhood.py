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


def get_instrument_id(stock_ticker): 
    """
    Get Robinhood's instrument ID for a stock, given its ticker symbol 

    Args:  
        stock_ticker (str): Stock ticker symbol. Example: 'AAPL' is the stock ticker symbol for Apple. Not case sensitive 
    
    Returns: 
        instrument_id (str): Robinhood's unique alphanumeric ID for a stock. Example: The instrument ID for AAPL is '450dfc6d-5510-4d40-abfb-f633b7d9be3e'
    """
    stock_ticker = stock_ticker.upper() 
    ticker_url = rh_stocks_url + '?symbol=' + stock_ticker
    response = requests.get(ticker_url) # does not require authentication 
    response = json.loads(response.text)['results']
    if results: # results is a list
        instrument_id = results[0]['id'] 
    else: # results list is empty 
        print('Instrument ID for stock ticker symbol {} not found'.format(stock_ticker))
        instrument_id = None
    return instrument_id

    
def get_order_history(instrument_id=None, stock_ticker=None): 
    """
    Get all filled (i.e. completed) buy and sell orders in a Robinhood account's history 

    Args:  
        instrument_id (str): Optional filter for filled orders for a particular stock, by its Robinhood instrument ID. Example: Apple is '450dfc6d-5510-4d40-abfb-f633b7d9be3e' 
        stock_ticker (str): Optional filter for filled orders for a particular stock ticker symbol. Example: 'AAPL' is the stock ticker symbol for Apple. Not case sensitive 
        If both instrument_id and stock_ticker are passed, instrument_id is used 
        If neither instrument_id nor stock_ticker is passed, filled orders for all stocks will be returned 

    Returns: 
        all_orders (list): A list of dictionaries, where each dictionary is an order and its associated information 
    """

    if instrument_id == None and stock_ticker != None: 
        instr_id = get_instrument_id(stock_ticker=stock_ticker) 
    else: 
        instr_id = instrument_id 

    all_orders = []
    response = requests.get(rh_orders_url, headers=rh_header)
    results = json.loads(response.text)['results'] 
    next_page = json.loads(response.text)['next']

    for r in results: 
        # filter out cancelled or unfilled orders 
        if r['side'] in ['buy', 'sell'] and r['state'] == 'filled': 
            if instr_id == None: 
                all_orders.append(r) 
            else: 
                if r['instrument_id'] == instr_id: 
                    all_orders.append(r)
    
    while next_page: 
        next_page = next_page.replace('http://loadbalancer-brokeback.nginx.service.robinhood', 'https://api.robinhood.com')
        response = requests.get(next_page, headers=rh_header)
        results = json.loads(response.text)['results']
        next_page = json.loads(response.text)['next']

        for r in results: 
            if r['side'] in ['buy', 'sell'] and r['state'] == 'filled':
                if instr_id == None: 
                    all_orders.append(r) 
                else: 
                    if r['instrument_id'] == instr_id: 
                        all_orders.append(r)
    
    return all_orders 