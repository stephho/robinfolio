import os
import json
import requests
from dotenv import load_dotenv


# get notion api credentials 
load_dotenv()
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

# notion urls 
db_base_url = 'https://api.notion.com/v1/databases'
page_base_url = 'https://api.notion.com/v1/pages'

header = {
    'Authorization':NOTION_TOKEN, 
    'Notion-Version':'2021-08-16', # latest version as of 2021-10-18
    'Content-Type':'application/json'
}


def get_db_schema(db_id): 
    """
    Get the schema (column names and data types, aka properties) of a Notion database 

    Args:  
        db_id (str): Notion database ID
    
    Returns: 
        db_schema (dict): Notion database schema. Keys are column names
    """
    db_url = db_base_url + '/' + db_id 
    response = requests.get(db_url, headers=header)
    db_schema = json.loads(response.text)['properties']
    return db_schema


def get_db_pages(db_id): 
    """
    Get a list of pages (and the properties and content of each page) in a Notion database 

    Args: 
        db_id (str): Notion database ID

    Returns: 
        pages (list): List of pages in the Notion database 
    """
    db_query_url = db_base_url + '/' + db_id + '/query'
    response = requests.post(db_query_url, headers=header)
    pages = json.loads(response.text)['results']
    return pages


def get_db_pg_ids(db_id): 
    """ 
    Get the page titles (names) and page IDs in a Notion database 
    
    Args: 
        db_id (str): Notion database ID

    Returns: 
        pg_dict (dict): Keys are the page titles, values are the page IDs 
    """

    # find name of db's title property 
    db_schema = get_db_schema(db_id=db_id)
    prop_title = []
    for prop_name, prop_type in db_schema.items(): 
        if prop_type == 'title': 
            prop_title.append(prop_name)
    prop_title = prop_title[0] # there is always only one title property in each database 

    # query db to get db page ids and names 
    pages = get_db_pages(db_id=db_id)
    pg_dict = {}
    for pg in pages: 
        pg_name = pg['properties'][prop_title]['title'][0]['plain_text']
        pg_dict[pg_name] = pg['id']
    
    return pg_dict 