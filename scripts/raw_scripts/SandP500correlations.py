#!/usr/local/bin/python3

# find correlations between sp500 variables for 07/09/21

# modules
import os
import pandas as pd
import numpy as np
from alpaca_trade_api.rest import REST, TimeFrame
from scipy.stats import pearsonr

os.chdir('/Users/kylekent/Dropbox/algo_alpaca/')

# load data -------------------------------------------------------------------

spDays = pd.read_csv('data/raw_data/spDays3monthsFrom073121.csv')

# get correlations ------------------------------------------------------------

# correlations of close for each stock 
pearsonr(spDays[spDays['symbol'] == 'AAPL']['close'],
        spDays[spDays['symbol'] == 'A']['close'])[0]

def histogram_intersection(a, b):
    v = np.minimum(a, b).sum().round(decimals=1)
    return v

spDays.groupby('symbol')[['close']].corr()

# make df wider 
spLong = spDays.pivot_table(index = 'timestamp',
        columns = 'symbol',
        values = 'close').reset_index()

# correlate
spLong.corr()
