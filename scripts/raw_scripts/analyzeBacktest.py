#!/usr/bin/python3

import argparse
import pandas as pd
from matplotlib import pyplot as plt
import pandas_ta as ta
import numpy as np
import code
import datetime

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help = 'Specify a ticker for divinity to run on')
    parser.add_argument('--live', action = 'store_true', help = 'Make divinity run in the live account (default is paper)')
    parser.add_argument('--backtest', action = 'store_true', help = 'Make divinity run a backtest')
    parser.add_argument('--btstartdate', help = 'Make divinity run a backtest')
    parser.add_argument('--btenddate', help = 'Make divinity run a backtest')
    parser.add_argument('--btinterval', help = 'Make divinity run a backtest')
    parser.add_argument('--plot', action = 'store_true', help = 'Plot indicators')
    parser.add_argument('--interactive', action = 'store_true', help = 'Enter interactive console after running')
    parser.add_argument('--write', action = 'store_true', help = 'Write backtest analysis to output folder')
    args = parser.parse_args()
    if args.backtest == True:
        if args.btstartdate is None or \
            args.btenddate is None or \
            args.btinterval is None:
            print('To complete a backtest btstartdate, btenddate, and btinterval must be supplied')
            sys.exit() 
    return args

def dataVis(data, args):
    print(data)
    plt.scatter('ds', 'y', data = data, color = 'black')
    plt.plot('ds', 'yhat', data = data)
    plt.plot('ds', 'maSlow', data = data)
    plt.plot('ds', 'maFast', data = data)
    plt.scatter('crossDate', 'crossY', data = data, color = 'red')
    plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = data, alpha = .5)
    plt.show()
    plt.close()

def edge_intersection(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, x4: int, y4: int) -> list:
    """Intersection point of two line segments in 2 dimensions

    params:
    ----------
    x1, y1, x2, y2 -> coordinates of line a, p1 ->(x1, y1), p2 ->(x2, y2), 

    x3, y3, x4, y4 -> coordinates of line b, p3 ->(x3, y3), p4 ->(x4, y4)

    Return:
    ----------
    list
        A list contains x and y coordinates of the intersection point,
        but return an empty list if no intersection point.

    """

    # None of lines' length could be 0.
    print(((x1 == x2) & (y1 == y2)) | ((x3 == x4) & (y3 == y4)))
    if (((x1 == x2) & (y1 == y2)) | ((x3 == x4) & (y3 == y4))):
        print('line length 0')
        return []

    print('asdfsd')

    # The denominators for the equations for ua and ub are the same.
    den = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    print((y4 - y3) * (x2 - x1))
    print((x4 - x3) * (y2 - y1))

    # Lines are parallel when denominator equals to 0,
    # No intersection point
    if den == 0:
        print('parallel')
        return []

    # Avoid the divide overflow
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / (den + 1e-16)
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / (den + 1e-16)

    # if ua and ub lie between 0 and 1.
    # Whichever one lies within that range then the corresponding line segment contains the intersection point.
    # If both lie within the range of 0 to 1 then the intersection point is within both line segments.
    if (ua < 0 or ua > 1 or ub < 0 or ub > 1):
        print('ua ub lie between 0 and 1')
        return []

    # Return a list with the x and y coordinates of the intersection
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    return [x, y]

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
    # plotting
    if args.plot == True:
        dataVis(data, args = args)
    # signal logic
    data['sell'] = data['yhat_upper'] < data['crossY']
    data['buy'] = data['yhat_lower'] > data['crossY']
    #return signal

def performance(data, start_value = 1000):
    # change in stock value
    data['percentChange'] = data['y']/data['y'].shift(1)
    # benchmarking
    data.loc[0, 'benchmarkValue'] = start_value
    for i in range(1, len(data)):
        data['benchmarkValue'][i] = data['benchmarkValue'][i-1]*data['percentChange'][i]
    # logic for position of strategy
    data.loc[0, 'position'] = 'in'
    data.loc[data['buy'] == True, 'position'] = 'in'
    data.loc[data['sell'] == True, 'position'] = 'out'
    data['position'] = data['position'].ffill()
    data.loc[0, 'stratValue'] = start_value
    # default values to track gains for taxes
    prev_in_value = start_value
    total_losses = 0
    last_buy_date = data['ds'][0]
    buy_sell_day_diff = []
    for i in range(1, len(data)):
        if data['position'][i] == 'in':
            data['stratValue'][i] = data['stratValue'][i-1]*data['percentChange'][i]
            # if last value was out
            if data['position'][i-1] == 'out':
                last_buy_date = data['ds'][i]
        # else ie is 'out'
        else:
            # if previous value was in, then get realized return
            if data['position'][i-1] == 'in':
                # realized gains/losses
                realized_return = data['stratValue'][i-1] - prev_in_value
                sell_date = data['ds'][i]
                buy_sell_day_diff += [sell_date - last_buy_date]
                # if positive then taxes
                if realized_return > 0:
                    taxes = realized_return*.22
                    # subtract taxes
                    data['stratValue'][i] = data['stratValue'][i-1] - taxes
                    # track prev in value
                    prev_in_value = data['stratValue'][i]
                else:
                    # because loss was negative carry over value without doing anything
                    data['stratValue'][i] = data['stratValue'][i-1]
                    prev_in_value = data['stratValue'][i]
                    # track total loss for tax harvesting
                    total_losses += realized_return
            else:
                data['stratValue'][i] = data['stratValue'][i-1]

    # count number of changes
    data.loc[0, 'grp'] = 1
    for i in range(1, len(data)):
        if data['position'][i] != data['position'][i-1]:
            data.loc[i, 'grp'] = 1
        else:
            data.loc[i, 'grp'] = data.loc[i-1, 'grp'] + 1
    grpOneDf = data[data['grp'] == 1]
    grpOneDf['profit'] = grpOneDf['stratValue'] - grpOneDf['stratValue'].shift(1)
    grpOneDf.loc[grpOneDf['position'] == 'in', 'profit'] = pd.NA
    # put grpOneDf profit back into data
    profitIndex = grpOneDf[grpOneDf['profit'].notna()].index
    data.loc[profitIndex, 'profit'] = grpOneDf.loc[profitIndex, 'profit']

def buyOnlyPerformance(data, start_value = 1000):
    # change in stock value
    data['percentChange'] = data['y']/data['y'].shift(1)
    # benchmarking
    data.loc[0, 'benchmarkValue'] = start_value
    # daily dollar increase
    dollar_increase = 16.6
    for i in range(1, len(data)):
        data['benchmarkValue'][i] = data['benchmarkValue'][i-1]*data['percentChange'][i] + dollar_increase # add monday every day
    # logic for position of strategy
    data.loc[0, 'position'] = 'in'
    data.loc[data['buy'] == True, 'position'] = 'in'
    data.loc[data['sell'] == True, 'position'] = 'out'
    data['position'] = data['position'].ffill()
    data.loc[0, 'stratValue'] = start_value
    # default principal val
    principal_value = 0
    for i in range(1, len(data)):
        # increase value of current day by percent change
        data['stratValue'][i] = data['stratValue'][i-1]*data['percentChange'][i]
        # add dollar increase to princiapl
        principal_value += dollar_increase
        # if original strat is in
        if data['position'][i] == 'in':
            # and previous position was out
            if data['position'][i-1] == 'out':
                # then add principal value
                data['stratValue'][i] = data['stratValue'][i] + principal_value
                # reset principle value
                principal_value = 0
    # count number of changes
    data.loc[0, 'grp'] = 1
    for i in range(1, len(data)):
        if data['position'][i] != data['position'][i-1]:
            data.loc[i, 'grp'] = 1
        else:
            data.loc[i, 'grp'] = data.loc[i-1, 'grp'] + 1
    grpOneDf = data[data['grp'] == 1]
    grpOneDf['profit'] = grpOneDf['stratValue'] - grpOneDf['stratValue'].shift(1)
    grpOneDf.loc[grpOneDf['position'] == 'in', 'profit'] = pd.NA
    # put grpOneDf profit back into data
    profitIndex = grpOneDf[grpOneDf['profit'].notna()].index
    data.loc[profitIndex, 'profit'] = grpOneDf.loc[profitIndex, 'profit']

def main():
    args = parseArgs()
    df = pd.read_csv('output/backtestv0.0.2{}{}{}.csv'.format(args.ticker, args.btstartdate, args.btenddate))
    df.columns.values[0] = 'indexValue'
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.reindex(index=df.index[::-1])
    df = df.reset_index(drop = True)
    prophetCross(df, fast = 3, slow = 5, args = args, MA = 'simple')
    performance(df, start_value = 1000)
    #buyOnlyPerformance(df, start_value = 100000)
    print(df[['stratValue', 'benchmarkValue']])
    plt.plot('ds', 'benchmarkValue', data = df)
    plt.plot('ds', 'stratValue', data = df)
    plt.show()
    plt.close()
    if args.interactive == True:
        code.interact(local = dict(globals(), **locals()))
    if args.write == True:
        df.to_csv('output/backtest{}Outcome.csv'.format(args.ticker))

main()
