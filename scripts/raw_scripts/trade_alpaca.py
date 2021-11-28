# test script to buy sell paper stocks

# import and wd ---------------------------------------------------
import os
import alpaca_trade_api as tradeapi

os.chdir('/Users/kylekent/Dropbox/algo_alpaca/')

# exploring api doc ----------------------------------------------

# start rest api
api = tradeapi.REST('PKZ8UJHM6IRLYWQQVCQJ', 'B3Dytdnj8wLleBKYaBKhqHSZz54xWCv2E1V5NMRY', 
        api_version = 'v2',
        base_url = 'https://paper-api.alpaca.markets')

# account
account = api.get_account()
account.__dict__
account.status
account.portfolio_value
account.cash

# sell order
api.submit_order('TSLA', qty = 10, side = 'buy')

# get orders
orders = api.list_orders()
len(orders)
orders[0]._raw.get('id')
orders[0].id

#api.get_order(order_id = )

# list positions
positions = api.list_positions()
positions[0].symbol
positions[0].qty

# cancel order
#api.cancel_order(order_id = )
api.cancel_all_orders()

# sell order
api.submit_order('AAPL', qty = positions[0].qty, side = 'sell')

