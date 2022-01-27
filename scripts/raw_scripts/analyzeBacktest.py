#!/usr/local/anaconda3/envs/ipy37/bin/python3

import argparse
import pandas as pd
from matplotlib import pyplot as plt
import pandas_ta as ta
import numpy as np

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

# get args
args = parseArgs()

# load data
#df = pd.read_csv('output/backtestv0.0.2{}2019-01-012021-12-29.csv'.format(args.ticker))
df = pd.read_csv('output/tmp.csv')
df['ds'] = pd.to_datetime(df['ds'])
print(df.dtypes)

print(np.log(4))
prophetCross(df, fast = 5, slow = 15, args = args, MA = 'simple')
