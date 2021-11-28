from alpaca_trade_api import StreamConn
from alpaca_trade_api.common import URL
#!/usr/bin/env python3
# https://github.com/alpacahq/alpaca-trade-api-python

import asyncio
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.common import URL

ALPACA_API_KEY = 'PKZ8UJHM6IRLYWQQVCQJ'
ALPACA_SECRET_KEY = 'B3Dytdnj8wLleBKYaBKhqHSZz54xWCv2E1V5NMRY'

async def trade_callback(t):
    print('trade', t)


async def quote_callback(q):
    print('quote', q)


# Initiate Class Instance
stream = Stream(ALPACA_API_KEY,
                ALPACA_SECRET_KEY,
                base_url=URL('https://paper-api.alpaca.markets'),
                data_feed='iex')  # <- replace to SIP if you have PRO subscription

# subscribing to event
stream.subscribe_trades(trade_callback, 'AAPL')
stream.subscribe_quotes(quote_callback, 'IBM')

stream.run()