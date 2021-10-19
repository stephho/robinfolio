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
    '''
    Get the schema (column names and data types) of a Notion database 

    Args:  
        db_id (str): Notion database ID
    
    Returns: 
        db_schema (dict): Notion database schema, aka properties. Keys are column names
    '''
    db_url = db_base_url + '/' + db_id 
    response = requests.get(db_url, headers=header)
    db_schema = json.loads(response.text)['properties']
    return db_schema