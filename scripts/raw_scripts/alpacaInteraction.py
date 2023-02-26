import alpaca_trade_api as tradeapi
import pandas as pd
from configparser import ConfigParser
import os

print(os.path.join(os.getcwd(), '.env.ini'))
config = ConfigParser()
config.read(os.path.join(os.getcwd(), '.env.ini'))
print('Using paper alpaca account')
account_key = config.get('alpaca_paper', 'alpaca_paper_key')
account_secret_key = config.get('alpaca_paper', 'alpaca_paper_secret_key')

# start rest api
api = tradeapi.REST(account_key, account_secret_key, 
        api_version = 'v2',
        base_url = 'https://paper-api.alpaca.markets')

account = api.get_account()
orders = api.list_orders()
positions = api.list_positions()
cash = float(account.cash)

tradeapi.REST(account_key, account_secret_key,
        api_version = 'v2',
        base_url = 'https://paper-api.alpaca.markets')

print(account)
print(orders)
print(positions)
print(cash)
