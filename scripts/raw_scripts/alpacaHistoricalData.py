#!/usr/local/bin/python3

# get s&p 500 data

# modules
import os
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta

# wd
os.chdir('/Users/kylekent/Dropbox/algo_alpaca/')

# load list of symbols
sp500 = pd.read_csv('~/Dropbox/algo_alpaca/data/raw_data/SandP500.csv').sort_values('Symbol')

# start rest api
api = REST('PKZ8UJHM6IRLYWQQVCQJ', 'B3Dytdnj8wLleBKYaBKhqHSZz54xWCv2E1V5NMRY')

# get df of one symbol
#xx = api.get_trades(sp500['Symbol'][27], "2021-07-09", "2021-07-09", limit=100).df

to_day = datetime.now().date() - relativedelta(days = 1)
from_day = to_day-relativedelta(years = 3)

# we neec to delete file first
if os.path.isfile('/Users/kylekent/Dropbox/algo_alpaca/data/rawdata/spDays3monthsFrom073121.csv'):
    os.remove('/Users/kylekent/Dropbox/algo_alpaca/data/raw_data/spDays3monthsFrom073121.csv')

# all symbols
for symbol in sp500['Symbol']:
    print(symbol)
    new_data = api.get_bars(symbol, TimeFrame.Day, from_day, to_day).df
    new_data.reset_index(inplace = True)
    new_data.insert(0, 'symbol', symbol)
    new_data.to_csv('~/Dropbox/algo_alpaca/data/raw_data/spDays3monthsFrom073121.csv',
            mode = 'a',
            header = not os.path.exists('/Users/kylekent/Dropbox/algo_alpaca/data/raw_data/spDays3monthsFrom073121.csv'),
            index = False)

# apple three years
to_day = datetime.now().date() - relativedelta(days = 1)
from_day = to_day-relativedelta(years = 5)

threeYears = api.get_bars('TSLA', TimeFrame.Day, from_day, to_day).df
threeYears.reset_index(inplace = True)
threeYears.insert(0, 'symbol', 'TSLA')
threeYears.to_csv('~/Dropbox/algo_alpaca/data/raw_data/TSLAdaily.csv',
        index = False)
    
# get df of quotes or trades for all symbols
#for symbol in sp500['Symbol']:
#   new_data = api.get_quotes(symbol, "2021-07-09", "2021-07-09", limit=1000000).df
#   new_data.reset_index(inplace=True)
#   new_data.insert(0, 'symbol', symbol)
#   new_data.to_csv('~/Dropbox/algo_alpaca/data/raw_data/spQuotes070921.csv',
#                   mode = 'a',
#                   header = not os.path.exists('/Users/kylekent/Dropbox/algo_alpaca/data/raw_data/spQuotes070921.csv'),
#                   index = False)

# function for turning trades into bars
def generate_tickbars(ticks, frequency=1000):
    times = ticks[:,0]
    prices = ticks[:,1]
    volumes = ticks[:,2]
    res = np.zeros(shape=(len(range(frequency, len(prices), frequency)), 6))
    it = 0
    for i in range(frequency, len(prices), frequency):
        res[it][0] = times[i-1]                        # time
        res[it][1] = prices[i-frequency]               # open
        res[it][2] = np.max(prices[i-frequency:i])     # high
        res[it][3] = np.min(prices[i-frequency:i])     # low
        res[it][4] = prices[i-1]                       # close
        res[it][5] = np.sum(volumes[i-frequency:i])    # volume
        it += 1
    return res

