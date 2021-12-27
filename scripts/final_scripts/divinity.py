#!/usr/local/anaconda3/envs/ipy37/bin/python3

# import block
#import yfinance as yf
#from datetime import datetime
#from dateutil.relativedelta import relativedelta
#import pandas as pd

import argparse
import yfinance as yf
import prophet 
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from matplotlib import pyplot as plt
from configparser import ConfigParser

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help = 'Specify a ticker for divinity to run on')
    parser.add_argument('--live', action = 'store_true', help = 'Make divinity run in the live account (default is paper)')
    parser.add_argument('--backtest', action = 'store_true', help = 'Make divinity run a backtest')
    parser.add_argument('--plot', action = 'store_true', help = 'Plot indicators')
    args = parser.parse_args()
    return args

def getData(start_date, end_date, args):
    data = yf.download(args.ticker, start_date, end_date, interval = '1d')
    data.reset_index(inplace = True)
    data.columns = data.columns.str.lower()
    data = data[['date', 'close']]
    data.insert(0, 'symbol', args.ticker)
    data.copy().loc[:, 'date'] = pd.to_datetime(data['date'])
    data = data.rename(columns = {'date':'ds', 'close':'y'})
    return data

def fitModel(data, args):
    proph = prophet.Prophet()
    proph.fit(data)
    fit_dates = proph.make_future_dataframe(periods = 0)
    fit = proph.predict(fit_dates)
    # final data
    final = fit[['ds', 'yhat', 'yhat_upper', 'yhat_lower']]
    final['y'] = data['y']
    if args.plot == True:
        plt.scatter('ds', 'y', data = final, color = 'black')
        plt.plot('ds', 'yhat', data = final)
        plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = final, alpha = .5)
        plt.show()
        plt.close()
    return final

def defineSignal(data):
    # most recent values
    y = data.iloc[-1]['y']
    upper = data.iloc[-1]['yhat_upper']
    lower = data.iloc[-1]['yhat_lower']
    # yesterdays value
    ym1 = data.iloc[-2]['y']
    # buy 
    if (ym1 < lower) & (y > lower):
        signal = 'buy'
    elif (ym1 > upper) & (y < upper):
        signal = 'sell'
    else:
        signal = 'stay'
    return signal

def makeAction(signal, args):
    # load api keys
    config = ConfigParser()
    config.read('/Users/kylekent/Dropbox/divinity/.env.ini')
    # use live api or paper api
    if args.live == True:
        print('Using live alpaca account')
        account_key = config.get('alpaca_real', 'alpaca_real_key')
        account_secret_key = config.get('alpaca_real', 'alpaca_real_secret_key')
        # start rest api
        api = tradeapi.REST(account_key, account_secret_key, 
                api_version = 'v2',
                base_url = 'https://api.alpaca.markets')
    else:
        print('Using paper alpaca account')
        account_key = config.get('alpaca_paper', 'alpaca_paper_key')
        account_secret_key = config.get('alpaca_paper', 'alpaca_paper_secret_key')
        # start rest api
        api = tradeapi.REST(account_key, account_secret_key, 
                api_version = 'v2',
                base_url = 'https://paper-api.alpaca.markets')
    # lists of need to know account info
    account = api.get_account()
    orders = api.list_orders()
    positions = api.list_positions()
    cash = float(account.cash)
    print('\nTodays action is: ' + signal)
    # if signal is buy and cash greater than 0
    if signal == 'buy' and cash > 0:
        # get amount of stock buyable
        buy_shares = float(cash/y)
        api.submit_order('TSLA', qty = buy_shares, side = 'buy')
        print('{} shares bought'.format(buy_shares))
    # if signal is sell
    if signal == 'sell':
        # get amount of stock buyable
        sell_shares = float(positions[0].qty)
        api.submit_order('TSLA', qty = sell_shares, side = 'sell')
        print('{} shares sold'.format(sell_shares))

def main():
    # parse args
    args = parseArgs()
    # dates
    to_day = datetime.today() - relativedelta(days = 1)
    to_day = to_day.replace(hour = 15, minute = 59, second = 59)
    from_day = to_day - relativedelta(years = 1)
    data = getData(start_date = from_day, end_date = to_day, args = args)
    final_data = fitModel(data, args = args)
    signal = defineSignal(final_data)
    makeAction(signal, args = args)

if __name__ == '__main__':
    args = parseArgs()
    main()
