# OOP practice
#https://realpython.com/python3-object-oriented-programming/

import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# dates
to_day = datetime.today() - relativedelta(days = 1)
to_day = to_day.replace(hour = 15, minute = 59, second = 59)
from_day = to_day - relativedelta(years = 1)

class data:
    def __init__(self, ticker, start_date, end_date, interval):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.raw_data = self.getData()
        self.model_data = self.process4Model()

    # pull data
    def getData(self):
        data = yf.download(self.ticker, self.start_date, self.end_date, interval = self.interval)
        return data
    # process data
    def process4Model(self):
        data = self.raw_data
        data.reset_index(inplace = True)
        data.columns = data.columns.str.lower()
        data = data[['date', 'close']]
        data.insert(0, 'symbol', self.ticker)
        data.copy().loc[:, 'date'] = pd.to_datetime(data['date'])
        data = data.rename(columns = {'date':'ds', 'close':'y'})
        return data

#data.tsla = data('tsla', from_day, to_day, '1d')
tmp = data('tsla', from_day, to_day, '1d')
print(tmp)
print(tmp.raw_data)
print(tmp.processed_data)
#print(data.tsla.processed_data)


