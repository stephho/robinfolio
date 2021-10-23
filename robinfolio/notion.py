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

notion_header = {
    'Authorization':NOTION_TOKEN, 
    'Notion-Version':'2021-08-16', # latest version as of 2021-10-18
    'Content-Type':'application/json'
}


def get_db_schema(db_id, simple=False): 
    """
    Get the schema (column names and data types, aka properties) of a Notion database 

    Args:  
        db_id (str): Notion database ID
        simple (bool): If True, return schema with only property name and type, and only for properities that require inputs (i.e. not formulas or rollups)
    
    Returns: 
        db_schema (dict): Notion database schema. Keys are column names
    """
    db_url = db_base_url + '/' + db_id 
    response = requests.get(db_url, headers=notion_header)
    db_schema_full = json.loads(response.text)['properties']
    
    if simple: 
        db_schema = {}
        for prop_name, prop_info in db_schema_full.items(): 
            prop_type = prop_info['type']
            if prop_type in ['formula', 'rollup', 'created_time', 'created_by', 'last_edited_time', 'last_edited_by']: 
                # these property types are automatically populated
                pass 
            else: 
                db_schema[prop_name] = prop_type
    else: 
        db_schema = db_schema_full 

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
    response = requests.post(db_query_url, headers=notion_header)
    pages = json.loads(response.text)['results']
    return pages


def get_db_pg_ids(db_id): 
    """ 
    Get the page titles (names) and page IDs in a Notion database 
    
    Args: 
        db_id (str): Notion database ID

    Returns: 
        pg_dict (dict): Keys are the page titles, values are the page IDs 
    
    Example: 
       {'GOOG': '11045592-f563-467f-b04f-11cbc6230118',
        'AAPL': '6488baa1-961e-46c0-adce-2382f5bfe7c0'}
    """

    # find name of db's title property 
    db_schema = get_db_schema(db_id=db_id, simple=True)
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


def create_db_pg_template(db_id, pg_icon=None): 
    """
    Create a template for the json data of a new Notion page in a database
    The template is formatted according to the database's schema (properties) 
    so that it can be used to create a new page in that database

    Args: 
        db_id (str): Notion database ID 
        pg_icon (str): Optional. URL of an image where it is hosted. The image is used as the icon of the page

    Returns: 
        pg_template (dict): Template to be used to create a new page in the database
        Keys are parent, icon, properties. Values need to be filled in to create a page 
    """

    db_schema = get_db_schema(db_id, simple=True)

    pg_template = {
        'parent': {'database_id': db_id}, 
        'icon': {'type': 'external', 'external':{'url':pg_icon}}, 
        'properties': {}
    }

    if pg_icon == None: 
        pg_template.pop('icon')

    for prop_name, prop_type in db_schema.items(): 
        if prop_type == 'date': 
            pg_template['properties'][prop_name] = {prop_type:{'start': None, 'end': None}}
        elif prop_type == 'select': 
            pg_template['properties'][prop_name] = {prop_type:{'id': None}}
        elif prop_type == 'relation': 
            pg_template['properties'][prop_name] = {prop_type:[{'id': None}]}
        elif prop_type == 'title': 
            pg_template['properties'][prop_name] = {prop_type:[{'text': {'content': None}}]}
        else: # number and rich_text properties do not need special format 
            pg_template['properties'][prop_name] = {prop_type:None}

    return pg_template 
    

def get_page_props(pg_id, prop=None): 
    """
    Get the properties of a Notion page 

    Args: 
        pg_id (str): Notion page ID. Example: '522fccf3-f806-44a7-9560-1d094bebbe33'. Must have dash notation 
        prop (str): Optional. Name of the property of the page to filter for

    Returns: 
        (dict): Keys are the property names. Values are the property types and the current value of the property 
    """
    pg_url = page_base_url + '/' + pg_id 
    response = requests.get(pg_url, headers=notion_header)
    pg_props = json.loads(response.text)['properties']
    if prop == None: 
        return pg_props 
    else: 
        return pg_props[prop]