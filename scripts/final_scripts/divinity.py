#!/usr/local/anaconda3/envs/ipy37/bin/python3

import argparse
import yfinance as yf
import prophet 
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from configparser import ConfigParser
import pandas_ta as ta
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help = 'Specify a ticker for divinity to run on')
    parser.add_argument('--live', action = 'store_true', help = 'Make divinity run in the live account (default is paper)')
    parser.add_argument('--backtest', action = 'store_true', help = 'Make divinity run a backtest')
    parser.add_argument('--btstartdate', help = 'Make divinity run a backtest')
    parser.add_argument('--btenddate', help = 'Make divinity run a backtest')
    parser.add_argument('--btinterval', help = 'Make divinity run a backtest')
    parser.add_argument('--plot', action = 'store_true', help = 'Plot indicators')
    args = parser.parse_args()
    if args.backtest == True:
        if args.btstartdate is None or \
            args.btenddate is None or \
            args.btinterval is None:
            print('To complete a backtest btstartdate, btenddate, and btinterval must be supplied')
            sys.exit() 
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

def fitModel(data, pred_periods = 0):
    proph = prophet.Prophet()
    proph.fit(data)
    fit_dates = proph.make_future_dataframe(periods = pred_periods)
    fit = proph.predict(fit_dates)
    # final data
    final = fit[['ds', 'yhat', 'yhat_upper', 'yhat_lower']]
    final['y'] = data['y']
    return final

#def defineSignal(data):
#    # most recent values
#    y = data.iloc[-1]['y']
#    upper = data.iloc[-1]['yhat_upper']
#    lower = data.iloc[-1]['yhat_lower']
#    # yesterdays value
#    ym1 = data.iloc[-2]['y']
#    # buy 
#    if (ym1 < lower) & (y > lower):
#        signal = 'buy'
#    elif (ym1 > upper) & (y < upper):
#        signal = 'sell'
#    else:
#        signal = 'stay'
#    return signal

def dataVis(data, args):
   plt.scatter('ds', 'y', data = data, color = 'black')
   plt.plot('ds', 'yhat', data = data)
   plt.plot('ds', 'maSlow', data = data)
   plt.plot('ds', 'maFast', data = data)
   plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = data, alpha = .5)
   plt.show()
   plt.close()

def prophetCross(data, fast, slow, args, MA = 'simple'):
    # what type of moving average
    if MA == 'simple':
        data['maSlow'] = ta.sma(data['y'], length = fast)
        data['maFast'] = ta.sma(data['y'], length = slow)
    if MA == 'exponential':
        data['maSlow'] = ta.ema(data['y'], length = fast)
        data['maFast'] = ta.ema(data['y'], length = slow)
    if args.plot == True:
        dataVis(data, args = args)
    # signal logic
    yCurrent = data.iloc[-1]['y']
    yPrevious = data.iloc[-2]['y']
    prophet_upper = data.iloc[-1]['yhat_upper']
    prophet_lower = data.iloc[-1]['yhat_lower']
    maFastCurrent = data.iloc[-1]['maFast']
    maFastPrevious = data.iloc[-2]['maFast']
    maSlowCurrent = data.iloc[-1]['maSlow']
    maSlowPrevious = data.iloc[-2]['maSlow']
    # default signal stay
    signal = 'stay'
    if maFastPrevious > prophet_upper or maSlowPrevious > prophet_upper:
        print('Yesterdays fast MA above CI, potential sell')
        if (maFastCurrent < maSlowCurrent) and (maFastPrevious > maSlowPrevious):
            signal = 'sell'
    if maFastPrevious < prophet_lower or maSlowPrevious < prophet_lower:
        print('Yesterdays fast MA below CI, potential buy')
        if (maFastCurrent > maSlowCurrent) and (maFastPrevious < maSlowPrevious):
            signal = 'buy'
    print('Todays action is {}'.format(signal))
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

def backtest(modelData, args, fit_years = 1, pred_periods = 0):
    # empty df
    out_data = pd.DataFrame()
    # for row of model data except the last 252 (one year)
    for i in range(len(modelData)-1, 252, -1):
        print(i)
        # identify day of iteration and get one year prior
        iter_day = modelData.loc[i, 'ds']
        one_year = iter_day - relativedelta(years = fit_years)
        # define data set
        fit_data = modelData[(modelData['ds'] <= iter_day) & (modelData['ds'] >= one_year)]
        # instantiate prophet model
        proph = prophet.Prophet()
        proph.fit(fit_data)
        # make ds column to predict, not future dates
        out_dates = proph.make_future_dataframe(periods = pred_periods) 
        # forecast
        out_model = proph.predict(out_dates)
        # pull predicted data from dataframes
        new_data = out_model.loc[out_model.index[out_model['ds'] == iter_day], ['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        # add actual value
        new_data['y'] = modelData[modelData['ds'] == iter_day]['y'].values
        # finally append data to populate a df
        out_data = out_data.append(new_data)
    # save data
    out_data.to_csv('output/backtestv0.0.2{}{}{}.csv'.format(args.ticker, args.btstartdate, args.btenddate))

def main():
    # parse args
    args = parseArgs()
    # run model in standard mode
    if args.backtest != True:
        # dates
        to_day = datetime.today() - relativedelta(days = 1)
        to_day = to_day.replace(hour = 15, minute = 59, second = 59)
        from_day = to_day - relativedelta(years = 1)
        # get data
        data = getData(start_date = from_day, end_date = to_day, args = args)
        # fit model
        fit_data = fitModel(data, args = args)
        # define signal
        signal = prophetCross(data = fit_data, MA = 'simple', fast = 2, slow = 4, args = args)
        #dataVis(final_data, args = args)
        makeAction(signal, args = args)
    # backtest model
    else:
        data = getData(args.btstartdate, args.btenddate, args = args)
        backtest(data, args = args)

if __name__ == '__main__':
    args = parseArgs()
    main()
