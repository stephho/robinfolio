import os
import json
import requests
from dotenv import load_dotenv



class robinhood: 
    """
    Class for interacting with Robinhood API 

    Attributes: 
        api_token (str): Robinhood API token
        api_header (dict): HTTP headers required by Robinhood API 
        api_orders_url (str): Robinhood's API URL for interacting with order objects
        api_stocks_url (str): Robinhood's API URL for interacting with stock objects, 
            aka instruments
        orders (list): Robinhood account's order history, represented as a list 
            of dictionaries, where each dictionary is an order and its associated
            information
        instrument_id (str): If orders are filtered for a particular stock, this
            is the stock's Robinhood instrument ID, a unique alphanumeric identifier 
        stock_ticker (str): If orders are filtered for a particular stock, the stock 
            ticker symbol
        stock_name (str): If orders are filtered for a particular stock, the stock 
            name, i.e. company name
    """

    def __init__(self, api_token): 
        self.api_token = api_token 
        self.api_header = {
            'authority':'api.robinhood.com', 
            'authorization':'Bearer ' + self.api_token, 
            'accept':'*/*',
            'referrer':'https://robinhood.com/',
            'accept-language':'en-US,en;q=0.9',
            'x-robinhood-api-version':'1.431.4',
            'Content-Type':'application/json'
        }
        self.api_orders_url = 'https://api.robinhood.com/orders/'
        self.api_stocks_url = 'https://api.robinhood.com/instruments/'


    def get_stock_name(self, instrument_id): 
        """
        Get a stock's ticker symbol and name, given Robinhood's instrument ID 
        for that stock 
        
        Args:  
            instrument_id (str): Robinhood unique alphaumneric ID for a stock 
        
        Returns: 
            (tuple): 
                stock_ticker (str): Stock ticker symbol
                stock_name (str): Stock name, i.e. company name
        
        Example: 
            'Apple' is the stock name, 'AAPL' is the stock ticker symbol, and 
            the instrument ID is '450dfc6d-5510-4d40-abfb-f633b7d9be3e'
        """
        instrument_url = self.api_stocks_url + instrument_id + '/'
        response = requests.get(instrument_url) # does not require authentication 
        response = json.loads(response.text)
        stock_ticker = response['symbol']
        stock_name = response['simple_name'] 
        return (stock_ticker, stock_name)


    def get_instrument_id(self, stock_ticker): 
        """
        Get Robinhood's instrument ID and name for a stock, given its ticker symbol 

        Args:  
            stock_ticker (str): Stock ticker symbol. Not case sensitive 
        
        Returns: 
            (tuple): 
                instrument_id (str): Robinhood's unique alphanumeric ID for a stock 
                stock_name (str): Stock name, i.e. company name 
        
        Example: 
            'Apple' is the stock name, 'AAPL' is the stock ticker symbol, and 
            the instrument ID is '450dfc6d-5510-4d40-abfb-f633b7d9be3e'
        """
        stock_ticker = stock_ticker.upper() 
        ticker_url = self.api_stocks_url + '?symbol=' + stock_ticker
        response = requests.get(ticker_url) # does not require authentication 
        results = json.loads(response.text)['results']
        if results: # results is a list
            instrument_id = results[0]['id'] 
            stock_name = results[0]['simple_name']
        else: # results list is empty 
            print('Instrument ID for stock ticker symbol {} not found'.format(stock_ticker))
            instrument_id = None
            stock_name = None
        return (instrument_id, stock_name) 

    
    def get_order_history(self, instrument_id=None, stock_ticker=None): 
        """
        Get all filled (i.e. completed) buy and sell orders in a Robinhood 
        account's history

        Args:  
            instrument_id (str): Optional filter for filled orders for a 
                particular stock, by its Robinhood instrument ID
                Example: Apple is '450dfc6d-5510-4d40-abfb-f633b7d9be3e' 
            stock_ticker (str): Optional filter for filled orders for a 
                particular stock ticker symbol. Not case sensitive 
                Example: 'AAPL' is the stock ticker symbol for Apple
                
            If both instrument_id and stock_ticker are passed, instrument_id is 
            used. If neither instrument_id nor stock_ticker is passed, filled 
            orders for all stocks will be returned 

        Attributes: 
            orders (list): A list of dictionaries, where each dictionary is 
                an order and its associated information 
        """

        if not instrument_id and stock_ticker: 
            self.instrument_id, self.stock_name = self.get_instrument_id(stock_ticker=stock_ticker) 
            self.stock_ticker = stock_ticker 
        elif instrument_id and not stock_ticker: 
            self.stock_ticker, self.stock_name = self.get_stock_name(instrument_id=instrument_id)
            self.instrument_id = instrument_id 
        elif instrument_id and stock_ticker: 
            print('both instrument ID {} and stock ticker symbol {} were passed'.format(instrument_id, stock_ticker))
            print('using instrument ID {} only...'.format(instrument_id))
            self.stock_ticker, self.stock_name = self.get_stock_name(instrument_id=instrument_id)
            self.instrument_id = instrument_id 
        else: 
            self.instrument_id = None 
            self.stock_ticker = None 
            self.stock_name = None 

        all_orders = []
        response = requests.get(self.api_orders_url, headers=self.api_header)
        results = json.loads(response.text)['results'] 
        next_page = json.loads(response.text)['next']

        for r in results: 
            # filter out cancelled or unfilled orders 
            if r['side'] in ['buy', 'sell'] and r['state'] == 'filled': 
                if not self.instrument_id: 
                    all_orders.append(r) 
                else: 
                    if r['instrument_id'] == self.instrument_id: 
                        all_orders.append(r)
        
        while next_page: 
            next_page = next_page.replace('http://loadbalancer-brokeback.nginx.service.robinhood', 'https://api.robinhood.com')
            response = requests.get(next_page, headers=self.api_header)
            results = json.loads(response.text)['results']
            next_page = json.loads(response.text)['next']

            for r in results: 
                if r['side'] in ['buy', 'sell'] and r['state'] == 'filled':
                    if self.instrument_id == None: 
                        all_orders.append(r) 
                    else: 
                        if r['instrument_id'] == self.instrument_id: 
                            all_orders.append(r)
        
        self.orders = all_orders 