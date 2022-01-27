# script testing prophet model prediction of 5 year tesla close stock data

# modules and dir ---------------------------------------------------------------

import os
import pandas as pd
import prophet
from matplotlib import pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
import yfinance as yf

# load data ---------------------------------------------------------------------

# days from Jan 1 2015 - Jul 30 2021
from_day = '2015-01-01'
to_day = '2021-07-31'

# TSLA for 5 years
tsla = yf.download(tickers = 'TSLA', start = '2021-01-06', end = '2022-01-07', interval = '1h')
gspc = yf.download(tickers = '^GSPC', start = '2021-01-06', end = '2022-01-07', interval = '1h')
dji = yf.download(tickers = '^DJI', start = '2021-01-06', end = '2022-01-07', interval = '1h')

# function to change names, get close price
def process_yf(data, ticker):
    data.reset_index(inplace = True)
    data.columns.values[0] = 'date'
    data.insert(0, 'symbol', ticker)
    data.columns = data.columns.str.lower()
    data = data[['symbol', 'date', 'close']]
    data.copy().loc[:, 'date'] = pd.to_datetime(data['date']).copy()
    print(data['date'].dtype)
    data['date'] = data['date'].dt.tz_localize(None)
    print(data['date'].dtype)
    return(data)

# process data
tsla = process_yf(tsla, 'TSLA')
print(tsla)
gspc = process_yf(gspc, 'GSPC')
dji = process_yf(dji, 'DJI')

# model data -----------------------------------------------------------------------

# get just time stamp and close
modelData = tsla[['date', 'close']]

# change names to 'ds' and 'y'
modelData = modelData.rename(columns = {'date':'ds', 'close':'y'})

# convert ds column to datetime
modelData['ds'] = pd.to_datetime(modelData['ds'])

# for loop one year moving prediction --------------------------------------------

def backtest(modelData, model_period = 5, pred_periods = 0):
    # empty df
    out_data = pd.DataFrame()
    # for row of model data except the last 252 (one year)
    for i in range(len(modelData)-1, -1, -1):
        # identify day of iteration and get one year prior
        iter_day = modelData.loc[i, 'ds']
        one_year = iter_day - relativedelta(days = 20)
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
        print(out_data)
    # save data
    out_data.to_csv('output/tmp.csv')

tsla_backtest = backtest(modelData)

# define signal ------------------------------
# previous, current, and yhat_upper value 
prev = fit_data.iloc[-2]['y']
cur = fit_data.iloc[-1]['y']
yhat_upper = new_data['yhat_upper'][0]
# if upper CI between previous and current value then buy
if (prev > yhat_upper) & (cur < yhat_upper):
    signal = 'sell'
#if else (prev < yhat_lower) & (cur > yhat_upper):
#    signal = 'buy'
#else:
#    signal = 'stay'
# add signal
new_data['signal'] = signal
# price delta
(cur/prev)*100
# if buy

# plot data fit every day for a year
fig, (ax1, ax2) = plt.subplots(figsize = (12,8))
plt.scatter('ds', 'y', data = out_data, color = 'black')
plt.plot('ds', 'yhat', data = out_data)
plt.fill_between('ds', 'yhat_lower', 'yhat_upper', data = out_data, alpha = .5)
plt.show()
plt.close()

