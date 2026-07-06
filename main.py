
import argparse
import pandas as pd
import yfinance as yf
import sys
import pandas_ta_classic as ta
import prophet
import duckdb
import plotnine as pl


def main():
    # parse args
    args = parse_args()
    df = get_data('2025-06-05', '2026-06-05', args.ticker)
    df = fit_model(df, date_col='date', y_col='close')
    data_vis(df)

def print_df(_: pd.DataFrame, limit: int | None = None) -> None:
    duckdb.sql(f'select * from _ {limit if limit else ''}') \
        .show()
    

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--ticker', type=str, required=True, help='Specify a ticker for divinity to run on')
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


def get_data(start_date: str, end_date: str, ticker: str) -> pd.DataFrame:
    data = yf.download(ticker, start_date, end_date, interval = '1d')
    if data is None:
        raise ValueError('Data is None')
    data.reset_index(inplace = True)
    data.columns = [col[0].lower() for col in data.columns]
    data = data[['date', 'close']]
    data.insert(0, 'symbol', ticker)
    return data # type: ignore


def prophet_cross(
    data: pd.DataFrame, 
    fast: int, 
    slow: int, 
    MA: str = 'simple',
) -> str:
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
    # signal logic
    if data['yhat_upper'].iloc[-1] < data['crossY'].iloc[-1]:
        signal = 'sell'
    elif data['yhat_lower'].iloc[-1] > data['crossY'].iloc[-1]:
        signal = 'buy'
    else:
        signal = 'stay'
    return signal


def fit_model(
    data: pd.DataFrame, 
    date_col: str, 
    y_col: str, 
    pred_periods: int = 0
) -> pd.DataFrame:
    data = duckdb.sql(f"""
        select 
            {date_col} as ds,
            {y_col} as y,
            *
        from data
    """).df()
    proph = prophet.Prophet()
    proph.fit(data)
    fit_dates = proph.make_future_dataframe(periods = pred_periods)
    fit = proph.predict(fit_dates)
    print(fit.columns)
    combined = duckdb.sql(f"""
        select
            data.date,
            data.close,
            fit.*
        from data
        join fit
            on data.date = fit.ds
    """).df()
    return combined 


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


def data_vis(data: pd.DataFrame) -> None:
    print(data.columns)
    plot = (
        pl.ggplot(data, pl.aes('date', 'close'))
            + pl.geom_point()
    )
    plot.show()


if __name__ == "__main__":
    main()
