from dotenv import load_dotenv
import pandas as pd
from copy import deepcopy
from robinhood import get_order_history, get_instrument_id
from notion import get_db_pg_ids, create_db_pg_template, create_db_pg, update_db_pg, calc_avg_unit_cost, define_sell_lots
import os 


# INPUTS 
# stock to update notion for 
ticker_symbol = 'ABT'


# SET UP ROBINHOOD API 

load_dotenv()
rh_api_token = os.environ.get('RH_TOKEN')

rh_header = {
    'authority':'api.robinhood.com', 
    'authorization':'Bearer ' + rh_api_token, 
    'accept':'*/*',
    'referrer':'https://robinhood.com/',
    'accept-language':'en-US,en;q=0.9',
    'x-robinhood-api-version':'1.431.4',
    'Content-Type':'application/json'
}

rh_orders_url = 'https://api.robinhood.com/orders/'
rh_stocks_url = 'https://api.robinhood.com/instruments/'


# SET UP NOTION API 

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')

# databases 
summary_db_id = os.environ.get('NOTION_SUMMARY_DB')
orders_db_id = os.environ.get('NOTION_ORDERS_DB')
lots_db_id = os.environ.get('NOTION_LOTS_DB')

# page icons 
orders_db_icon = os.environ.get('ORDERS_DB_ICON')
summary_db_icon = os.environ.get('SUMMARY_DB_ICON')
lots_db_icon = os.environ.get('LOTS_DB_ICON')

notion_header = {
    'Authorization':NOTION_TOKEN, 
    'Notion-Version':'2021-08-16', # latest version as of 2021-10-18
    'Content-Type':'application/json'
}

# notion api urls 
db_base_url = 'https://api.notion.com/v1/databases'
page_base_url = 'https://api.notion.com/v1/pages'


# GET ORDERS FROM ROBINHOOD 

order_history = get_order_history(stock_ticker=ticker_symbol)
order_history_df = pd.DataFrame.from_dict(order_history)

# read cleaned order history data into pandas 
cols = ['id', 'instrument_id', 'last_transaction_at', 'side', 'cumulative_quantity', 'average_price', 'fees']
cleaned_orders_df = order_history_df[cols]
cleaned_orders_df.set_index('id', inplace=True)
cleaned_orders_df.rename(columns={'side':'order_type',
    'cumulative_quantity':'shares', 
    'average_price':'unit_cost', 
    'last_transaction_at':'order_date'}, inplace=True)

# get order date in est timezone 
cleaned_orders_df['order_date_utc'] = pd.to_datetime(cleaned_orders_df['order_date'], utc=True, infer_datetime_format=True)
cleaned_orders_df['order_date_est'] = cleaned_orders_df['order_date_utc'].dt.tz_convert('America/New_York')
cleaned_orders_df['order_date_display'] = cleaned_orders_df['order_date_est'].dt.strftime('%Y/%m/%d')
cleaned_orders_df['order_date_est'] = cleaned_orders_df['order_date_est'].dt.strftime('%Y-%m-%dT%H:%M:%S%z') #2021-10-15T12:00:00-07:00

cleaned_orders_df['price_dollars'] = cleaned_orders_df['unit_cost'].str.split('.').str[0]
cleaned_orders_df['price_cents'] = cleaned_orders_df['unit_cost'].str.split('.').str[1]
cleaned_orders_df['price_display'] = cleaned_orders_df['price_dollars'] + '.' + cleaned_orders_df['price_cents'].str[:4]

cleaned_orders_df['shares_int'] = cleaned_orders_df['shares'].str.split('.').str[0]
cleaned_orders_df['shares_partial'] = cleaned_orders_df['shares'].str.split('.').str[1]
cleaned_orders_df['shares_display'] = cleaned_orders_df['shares_int']
cleaned_orders_df.loc[(cleaned_orders_df['shares_partial'] != '00000000'), 'shares_display'] = cleaned_orders_df['shares_int'] + '.' + cleaned_orders_df['shares_partial'].str[:4]

cleaned_orders_df['ticker_symbol'] = ticker_symbol 
cleaned_orders_df['separator'] = '@ $'
cleaned_orders_df['order_type'] = cleaned_orders_df['order_type'].str.upper()
cleaned_orders_df['order_name'] = cleaned_orders_df['order_date_display'].str.cat(cleaned_orders_df[['ticker_symbol', 'order_type', 'shares_display', 'separator']], sep=' ')
cleaned_orders_df['order_name'] = cleaned_orders_df['order_name'].str.cat(cleaned_orders_df['price_display'])
cleaned_orders_df.drop(columns=['separator'], inplace=True)

# important for determining sell lots that orders are in ascending order by timestamp
cleaned_orders_df.sort_values('order_date', inplace=True)
sorted_orders = cleaned_orders_df.to_dict(orient='index')


# PREPARE NOTION 

# get page id for each stock 
stocks_pg_ids = get_db_pg_ids(summary_db_id)

# create json data templates to create pages in databases
summary_template = create_db_pg_template(db_id=summary_db_id, pg_icon=summary_db_icon)
lots_template = create_db_pg_template(db_id=lots_db_id, pg_icon=lots_db_icon)
order_template = create_db_pg_template(orders_db_id, pg_icon=orders_db_icon)

try: 
    stock_pg_id = stocks_pg_ids[ticker_symbol]
except KeyError: 
    print('stock does not exist in summary db, must create a page for it')

    # get stockname from robinhood
    instr_id, stock_name = get_instrument_id(ticker_symbol)

    stock_data = deepcopy(summary_template)
    stock_data['properties']['Stock ticker']['title'][0]['text']['content'] = ticker_symbol
    stock_data['properties']['Stock name']['rich_text'][0]['text']['content'] = stock_name 
    stock_data['properties'].pop('Stock orders') # this relation will be filled out in the orders db 

    stock_status, stock_pg_id = create_db_pg(create_data=stock_data)
    
    stocks_pg_ids[ticker_symbol] = stock_pg_id


# CREATE PAGES FOR EACH ROBINHOOD ORDER IN NOTION ORDERS DATABASE 
# and corresponding pages in notion sell lots database 
# version with avg unit cost calculated from pandas 

for o in sorted_orders: 
    order_data = deepcopy(order_template)

    order_name = sorted_orders[o]['order_name']
    shares = float(sorted_orders[o]['shares']) 

    order_data['properties']['Order']['title'][0]['text']['content'] = order_name
    order_data['properties']['Order date']['date']['start'] = sorted_orders[o]['order_date_est']
    order_data['properties']['Shares']['number'] = shares 
    order_data['properties']['Unit cost']['number'] = float(sorted_orders[o]['unit_cost']) 

    # get the stock's page id in the summary db 
    ticker_symbol = sorted_orders[o]['ticker_symbol']
    stock_pg_id = stocks_pg_ids[ticker_symbol]
    order_data['properties']['Stock']['relation'][0]['id'] = stock_pg_id 

    if sorted_orders[o]['order_type'] == 'BUY': 

        for p in ['Later sold in', 'Avg unit cost', 'Fee', 'Sell lots']:
            # these properties are only for sell  
            order_data['properties'].pop(p)

        order_data['properties']['Type']['select']['id'] = '21b4e1ee-c961-4bef-8d48-0f55d73eb2b7' # BUY

        print('creating the order page for: {}'.format(order_name)) 
        buy_status, buy_pg_id = create_db_pg(create_data=order_data)

        if buy_status == 'success': 
            # get the new average cost after creating buy order, then update it in the buy order page just created 
            avg_cost = calc_avg_unit_cost(stock_pg_id)
            update_avg_cost = {'Avg unit cost':avg_cost}

            update_status, update_pg_id = update_db_pg(pg_id=buy_pg_id, update_dict=update_avg_cost)
            print('\n')
    
    else: # SELL ORDER 

        # these properties need to be updated after the sell order page is created 
        for p in ['Later sold in', 'Sell lots']: 
            order_data['properties'].pop(p) 
        
        order_data['properties']['Type']['select']['id'] = '407f704b-a0a2-47cd-94ae-59aaa1e93e22' # SELL 
        order_data['properties']['Fee']['number'] = float(sorted_orders[o]['fees'])
        
        # get the current average cost in order to calculate cost basis 
        avg_cost = calc_avg_unit_cost(stock_pg_id) 
        order_data['properties']['Avg unit cost']['number'] = avg_cost 

        # create sell order page 
        print('creating the order page for: {}'.format(order_name)) 
        sell_status, sell_pg_id = create_db_pg(create_data=order_data)
        
        if sell_status == 'success': 
            # determine sell lots
            sell_lots = define_sell_lots(stock_pg_id=stock_pg_id, total_shares_sold=shares)

            n = 1
            for lot in sell_lots: 

                # create pages in the sell lots db 
                lots_data = deepcopy(lots_template) 
                
                shares_sold = lot['shares_sold']
                buy_pg_id = lot['buy_pg_id']
                sell_lot_name = order_name + ' -{}'.format(n) # sell order name + an integer 

                lots_data['properties']['Sell order']['relation'][0]['id'] = sell_pg_id
                lots_data['properties']['Shares']['number'] = shares_sold 
                lots_data['properties']['Lots sold from']['relation'][0]['id'] = buy_pg_id 
                lots_data['properties']['Order']['title'][0]['text']['content'] = sell_lot_name 

                lots_status, lots_pg_id = create_db_pg(create_data=lots_data)
                
                n = n+1 
                print('\n')

print('done inputting orders for {} stock into notion!'.format(ticker_symbol))