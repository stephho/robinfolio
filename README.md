# robinfolio

> **robinfolio** aims to get information about your [Robinhood](https://robinhood.com/) portfolio and order history into [Notion.so](https://notion.so) databases, allowing easier and more granular tracking of your stocks, costs, and gains and losses

## Background
While Robinhood is good at giving you an overview of your portfolio, its reporting cabilities are limited in terms of displaying more detail about your order history — for example, calculating your gains and losses on individual orders. There's not even an easy way to export that data into Google Sheets or Excel, a popular method of generating portfolio reporting among amateur traders. I've chosen Notion because of their easy-to-use interface that allows filtering, sorting, different views of the same database, and a better note-taking experience. 

robinfolio is a Python project which enables automating the process of getting information about your portfolio from your Robinhood account and into Notion, using the Robinhood and Notion APIs :rocket: 

## Notion requirements 
### Creating the databases 
You'll need three databases: 
1. Summary — an overview of your portfolio, at the stock level 
2. Orders 
3. Sell lots 

More instructions coming soon on how to set up the databases. 

### Set up Notion API integration 
Follow step 1 and 2 in Notion's [Getting Started guide](https://developers.notion.com/docs/getting-started#getting-started) to create a Notion API token and to add the integration to each of your databases 

## Robinhood requirements 
### Find your API token 
1. Log in to your Robinhood account in a browser on desktop. These instructions are for Google Chrome, but any browser will be similar
2. Right click anywhere on the page and select "Inspect" 
3. In the window that appears (it may be to the side or at the bottom of your screen), select "Network" 
4. In the search box, type in "orders" and select any of the rows under "Name" 
5. In the new window that appears, select "Headers" and scroll down to where it says "authorization." The long alphanumeric string after the word "Bearer" is your API token

## Thanks 
Much thanks to [How to export your Robinhood stocks by Bart Claeys](https://medium.com/@bartclaeys/how-to-export-your-robinhood-stocks-fc8245b3d118) for giving me my starting point! 