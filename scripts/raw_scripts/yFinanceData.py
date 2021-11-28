#!/usr/bin/env python3 

import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta

os.chdir('/Users/kylekent/Dropbox/algo_alpaca/')

to_day = datetime.now().date() - relativedelta(days = 1)
from_day = to_day-relativedelta(years = 5)

data = yf.download(tickers = 'TSLA', start = from_day, end = to_day, interval = '1d')

data.reset_index(inplace = True)
data.insert(0, 'symbol', 'TSLA')

data.columns = data.columns.str.lower()

data.columns.values[1] = 'timestamp'

data.to_csv('data/raw_data/TSLAdaily_yf.csv')
