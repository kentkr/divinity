

forecast.columns.values

xx = forecast.loc[forecast.index[forecast['ds'] == iter_day], ['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
xx['y'] = modelData[modelData['ds'] == iter_day]['y']

xy = forecast.loc[forecast.index[forecast['ds'] == iter_day + relativedelta(days = 1)], ['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
xy['y'] = modelData[modelData['ds'] == iter_day + relativedelta(days = 1)]['y']

xx.append(xy)

df = pd.DataFrame()
df = df.append(xx)
df = df.append(xy)
df

len(modelData)-1

xx

for i in 1:


new_data['y'] = modelData[modelData['ds'] == iter_day]['y'].values



modelData.iloc[-1]['y']
new_data = pd.DataFrame()
new_data['y'] = modelData[modelData['ds'] == '2021-07-30']['y'].values
if (new_data['y'][0] > 0) & (new_data['y'][0] > 0):
    print('asldkfj')
modelData.iloc[[-1, -2]].iloc[1,1] > 0
