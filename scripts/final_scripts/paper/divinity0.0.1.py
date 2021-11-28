#!/usr/bin/env python

# submit basic order using prophet

# import and wd --------------------------------

import yfinance as yf
import prophet 
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from matplotlib import pyplot as plt
from configparser import ConfigParser

# load data -------------------------------------

# dates
to_day = datetime.today() - relativedelta(days = 1)
to_day = to_day.replace(hour = 15, minute = 59, second = 59)
from_day = to_day - relativedelta(years = 1)

# yf data
tsla = yf.download(tickers = 'TSLA', start = from_day, end = to_day, interval = '1d')

# process
tsla.reset_index(inplace = True)
tsla.columns = tsla.columns.str.lower()
tsla = tsla[['date', 'close']]
tsla.insert(0, 'symbol', 'TSLA')
tsla.copy().loc[:, 'date'] = pd.to_datetime(tsla['date'])

tsla = tsla.rename(columns = {'date':'ds', 'close':'y'})

# fit model ---------------------------------------

# instantiate
proph = prophet.Prophet()

# fit model to TSLA 
proph.fit(tsla)

# dates to predict (no future dates)
fit_dates = proph.make_future_dataframe(periods = 0)

# acutally predict
fit = proph.predict(fit_dates)

# combine fit data and regular data ------------------------------------------

# final data
final = fit[['ds', 'yhat', 'yhat_upper', 'yhat_lower']]
final['y'] = tsla['y']

# define signals -------------------------------------------------------------

# most recent values
y = final.iloc[-1]['y']
upper = final.iloc[-1]['yhat_upper']
lower = final.iloc[-1]['yhat_lower']

# yesterdays value
ym1 = final.iloc[-2]['y']

# buy 
if (ym1 < lower) & (y > lower):
    signal = 'buy'
elif (ym1 > upper) & (y < upper):
    signal = 'sell'
else:
    signal = 'stay'

print('\nTodays action is: ' + signal)

# get brokerage account info ------------------------------------------------------------

# load api keys
config = ConfigParser()
config.read('/Users/kylekent/Dropbox/divinity/.env.ini')

paper_key = config.get('alpaca_paper', 'alpaca_paper_key')
paper_secret_key = config.get('alpaca_paper', 'alpaca_paper_secret_key')

# start rest api
api = tradeapi.REST(paper_key, paper_secret_key, 
        api_version = 'v2',
        base_url = 'https://paper-api.alpaca.markets')

# lists of need to know account info
account = api.get_account()
orders = api.list_orders()
positions = api.list_positions()

cash = float(account.cash)
buy_shares = int(cash/y)

# if signal is buy
if signal == 'buy':
    # get amount of stock buyable
    buy_shares = cash/y
    api.submit_order('TSLA', qty = buy_shares, side = 'buy')
    print('{} shares bought'.format(buy_shares))

# if signal is sell
if signal == 'sell':
    # get amount of stock buyable
    sell_shares = float(positions[0].qty)
    api.submit_order('TSLA', qty = sell_shares, side = 'sell')
    print('{} shares sold'.format(sell_shares))

# plot prediction with real value
plt.scatter('ds', 'y', data = final, color = 'black')
plt.plot('ds', 'yhat', data = final)
plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = final, alpha = .5)
plt.show()
plt.close()

