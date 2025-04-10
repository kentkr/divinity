#!/usr/bin/python3

import argparse
import yfinance as yf
import prophet 
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from configparser import ConfigParser
import pandas_ta as ta
import sys
import os

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help = 'Specify a ticker for divinity to run on')
    parser.add_argument('--test', action = 'store_true', help = 'Run the algorithm locally, and not on a paper or live account')
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
    print(data)
    data.reset_index(inplace = True)
    
    # Convert MultiIndex to lowercase if it exists
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = pd.MultiIndex.from_tuples(
            [tuple(str(i).lower() for i in col) for col in data.columns]
        )
    else:
        # Handle single-level columns
        data.columns = data.columns.str.lower()
    
    # Select the right columns based on structure
    if isinstance(data.columns, pd.MultiIndex):
        # For MultiIndex, we need to find the right level and names
        # This is dependent on your data structure
        date_col = [col for col in data.columns if 'date' in str(col).lower()]
        close_col = [col for col in data.columns if 'close' in str(col).lower()]
        
        if date_col and close_col:
            data = data[[date_col[0], close_col[0]]]
            # Rename to flat columns
            data.columns = ['date', 'close']
    else:
        # For flat columns
        data = data[['date', 'close']]
    
    data.insert(0, 'symbol', args.ticker)
    data.loc[:, 'date'] = pd.to_datetime(data['date'])
    data = data.rename(columns = {'date':'ds', 'close':'y'})
    return data

def _fitModel(data, pred_periods = 0):
    proph = prophet.Prophet()
    proph.fit(data)
    fit_dates = proph.make_future_dataframe(periods = pred_periods)
    fit = proph.predict(fit_dates)
    # final data
    final = pd.merge(
        fit[['ds', 'yhat', 'yhat_upper', 'yhat_lower']],
        data[['ds', 'y']],
        on='ds',
        how='left'
    )
    return final

def fitModel(data, pred_periods = 0):
    proph = prophet.Prophet()
    proph.fit(data)
    fit_dates = proph.make_future_dataframe(periods = pred_periods)
    fit = proph.predict(fit_dates)
    # final data
    final = fit[['ds', 'yhat', 'yhat_upper', 'yhat_lower']]
    final['y'] = data['y']
    return final

def edge_intersection(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, x4: int, y4: int) -> list:
    # None of lines' length could be 0.
    if (((x1 == x2) & (y1 == y2)) | ((x3 == x4) & (y3 == y4))):
        return []
    # The denominators for the equations for ua and ub are the same.
    den = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    # Lines are parallel when denominator equals to 0,
    # No intersection point
    if den == 0:
        return []
    # Avoid the divide overflow
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / (den + 1e-16)
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / (den + 1e-16)
    # if ua and ub lie between 0 and 1.
    # Whichever one lies within that range then the corresponding line segment contains the intersection point.
    # If both lie within the range of 0 to 1 then the intersection point is within both line segments.
    if (ua < 0 or ua > 1 or ub < 0 or ub > 1):
        return []
    # Return a list with the x and y coordinates of the intersection
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    return [x, y]

def dataVis(data, args):
    plt.scatter('ds', 'y', data = data, color = 'black')
    plt.plot('ds', 'yhat', data = data)
    plt.plot('ds', 'maSlow', data = data)
    plt.plot('ds', 'maFast', data = data)
    plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = data, alpha = .5)
    plt.scatter('crossDate', 'crossY', data = data, color = 'red')
    plt.show()
    plt.close()

def _prophetCross(data, fast, slow, args, MA = 'simple'):
    # what type of moving average
    if MA == 'simple':
        data['maFast'] = ta.sma(data['y'], length = fast)
        data['maSlow'] = ta.sma(data['y'], length = slow)
    if MA == 'exponential':
        data['maFast'] = ta.ema(data['y'], length = fast)
        data['maSlow'] = ta.ema(data['y'], length = slow)
    # convert ds to unix timestamp for next step
    data['ds'] = pd.to_datetime(data['ds']).astype(int)/10**9
    # get intersections of points
    crossList = []
    for i in range(1, len(data)-1):
        row = [data['ds'][i]]
        ix = edge_intersection(data['ds'][i], data['maFast'][i], data['ds'][i+1], data['maFast'][i+1], data['ds'][i], data['maSlow'][i], data['ds'][i+1], data['maSlow'][i+1])
        if not ix:
            row += [None, None]
        else:
            row += ix
        crossList.append(row)
    crossDf = pd.DataFrame(data = crossList, columns = ['ds', 'crossDate', 'crossY'])
    final_data = pd.merge(
        data,
        crossDf,
        on = 'ds',
        how = 'left'
    )
    # convert unix timestamps back to datetime
    final_data['ds'] = pd.to_datetime(final_data['ds'], unit = 's')
    final_data['crossDate'] = pd.to_datetime(final_data['crossDate'], unit = 's')
    return final_data

def prophetCross(data, fast, slow, args, MA = 'simple'):
    # what type of moving average
    if MA == 'simple':
        data['maFast'] = ta.sma(data['y'], length = fast)
        data['maSlow'] = ta.sma(data['y'], length = slow)
    if MA == 'exponential':
        data['maFast'] = ta.ema(data['y'], length = fast)
        data['maSlow'] = ta.ema(data['y'], length = slow)
    # convert ds to unix timestamp for next step
    data['ds'] = pd.to_datetime(data['ds']).astype(int)/10**9
    # get intersections of points
    crossList = []
    for i in range(1, len(data)-1):
        crossList.append(edge_intersection(data['ds'][i], data['maFast'][i], data['ds'][i+1], data['maFast'][i+1], data['ds'][i], data['maSlow'][i], data['ds'][i+1], data['maSlow'][i+1]))
    crossDf = pd.DataFrame(crossList)
    # add cross data to df
    data['crossDate'] = crossDf.iloc[:,0]
    data['crossY'] = crossDf.iloc[:,1]
    # convert unix timestamps back to datetime
    data['ds'] = pd.to_datetime(data['ds'], unit = 's')
    data['crossDate'] = pd.to_datetime(data['crossDate'], unit = 's')
    print(data)
    # signal logic
    if data['yhat_upper'].iloc[-1] < data['crossY'].iloc[-1]:
        signal = 'sell'
    elif data['yhat_lower'].iloc[-1] > data['crossY'].iloc[-1]:
        signal = 'buy'
    else:
        signal = 'stay'
    return signal

def makeAction(signal, args):
    # load api keys
    config = ConfigParser()
    config.read(os.path.join(os.getcwd(), '.env.ini'))
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

def backtest(btstartdate, btenddate, args, fit_years=1, pred_periods=0):
    all_data = getData(datetime.strptime(args.btstartdate, "%Y-%m-%d")-timedelta(days=365), args.btenddate, args=args)
    window_size = 252
    out_data = pd.DataFrame()
    
    for i in range(len(all_data)-window_size+1):
        # Get data for this window
        window_data = all_data.iloc[i:i+window_size].copy()
        
        # Fit model on this window
        fit_data = _fitModel(window_data.copy())
        
        # Calculate crossings for this window
        final_data = _prophetCross(data=fit_data, MA='simple', fast=3, slow=5, args=args)
        
        # Save just the last day with its calculations
        last_day = final_data.iloc[[-1]]
        out_data = pd.concat([out_data, last_day.copy()], ignore_index=True)
    
    # Save data
    out_data.to_csv('output/backtestv0.0.2{}{}{}.csv'.format(args.ticker, args.btstartdate, args.btenddate))
    dataVis(out_data, args)

def main():
    # parse args
    args = parseArgs()
    # run model in standard mode
    if args.backtest != True:
        # dates
        #to_day = datetime.today() - relativedelta(days = 1)
        to_day = datetime.today()
        to_day = to_day.replace(hour = 15, minute = 30, second = 00)
        print(to_day)
        from_day = to_day - relativedelta(years = 1)
        # get data
        data = getData(start_date = from_day, end_date = to_day, args = args)
        # fit model
        fit_data = fitModel(data)
        # define signal
        signal = prophetCross(data = fit_data, MA = 'simple', fast = 3, slow = 5, args = args)
        print('===== Signal: {} ====='.format(signal))
        # make an action if test is not true
        if args.test == False:
            makeAction(signal, args = args)
        # plot
        if args.plot == True:
            dataVis(fit_data, args)
    # backtest model
    else:
        backtest(args.btstartdate, args.btenddate, args = args)

if __name__ == '__main__':
    args = parseArgs()
    main()
