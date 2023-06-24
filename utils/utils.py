from datetime import datetime, timedelta, timezone
import time as time
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests as requests
import os
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))
from keys import keys

def parse_time(weeks_ago_start=None, weeks_ago_end=None):
    
    if not weeks_ago_start:
        weeks_ago_start = 20
    else:
        pass
    if not weeks_ago_end:
        weeks_ago_end = 8
    else:
        pass
    if (weeks_ago_start < weeks_ago_end):
        raise Exception('The value of weeks_ago_start must be greater than weeks_ago_end')

    now = time.time()*1000
    #convert to integer
    now_int = round(now)
    #convert the previous to a datetime object
    now_dt = pd.to_datetime(now_int, unit='ms')
    
    ###Processing the start
    
    #create a datetime object "weeks_ago_start" weeks in the past
    start_dt = now_dt - timedelta(weeks=weeks_ago_start)
    #transform the start datetime object in a float
    start_dt_int = start_dt.timestamp() * 1000
    #round the float to obtain an integer
    start_str = str(round(start_dt_int))
    
    ###Processing the end
    
    #create a datetime object "weeks_ago_end" weeks in the past
    end_dt = now_dt - timedelta(weeks=weeks_ago_end)
    #transform the end datetime object in a float
    end_dt_int = end_dt.timestamp() * 1000
    #round the float to obtain an integer
    end_str = str(round(end_dt_int))
    
    return (start_str, end_str)

def get_history_v2(symbol, interval, start, end = None):
    '''
    Function to format data from get_historical_klines from Binance
    '''
    api_key = keys.LIVE_API_KEY
    api_secret = keys.LIVE_API_SECRET
    client = Client(api_key=api_key, api_secret=api_secret)
   
    try:                  
        bars = client.get_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    except (BinanceAPIException, ConnectionResetError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(e)
        print('Something went wrong. Error occured at %s. Wait for 1 min.' % (datetime.now().astimezone(timezone.utc)))
        time.sleep(60)
        client = Client(api_key, api_secret)
        bars = client.get_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    print(len(bars))
    df = pd.DataFrame(bars)
    df["Date"] = pd.to_datetime(df.iloc[:,0], unit = "ms")
    df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                  "Clos Time", "Quote Asset Volume", "Number of Trades",
                  "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.set_index("Date", inplace = True)
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors = "coerce")
    
    return (df, client)

def get_history_v3(symbol, interval, start, end = None, testnet=None):
    '''
    Function to format data from get_historical_klines from Binance
    '''
    if (testnet==False):
        api_key = keys.LIVE_API_KEY
        api_secret = keys.LIVE_API_SECRET
        client = Client(api_key=api_key, api_secret=api_secret, tld = 'com', testnet = testnet)

    if (testnet==True): 
        api_key = keys.TESTNET_API_KEY
        api_secret = keys.TESTNET_API_SECRET
        client = Client(api_key=api_key, api_secret=api_secret, tld = "com", testnet = testnet)
    try:                  
        bars = client.get_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    except (BinanceAPIException, ConnectionResetError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(e)
        print('Something went wrong. Error occured at %s. Wait for 1 min.' % (datetime.now().astimezone(timezone.utc)))
        time.sleep(60)
        client = Client(api_key, api_secret)
        bars = client.get_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    print(len(bars))
    df = pd.DataFrame(bars)
    df["Date"] = pd.to_datetime(df.iloc[:,0], unit = "ms")
    df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                  "Clos Time", "Quote Asset Volume", "Number of Trades",
                  "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.set_index("Date", inplace = True)
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors = "coerce")
    
    return (df, client)

def futures_history(symbol, interval, start, end = None, testnet=None):
    '''
    Function to format data from get_historical_klines from Binance
    '''
    client = None
    if (testnet==False):
        api_key = keys.LIVE_API_KEY
        api_secret = keys.LIVE_API_SECRET
        client = Client(api_key=api_key, api_secret=api_secret, tld = 'com', testnet = testnet)

    if (testnet==True):
        api_key = keys.TESTNET_API_KEY
        api_secret = keys.TESTNET_API_SECRET 
        client = Client(api_key=api_key, api_secret=api_secret, tld = "com", testnet = testnet)
    try:                  
        bars = client.futures_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    except (BinanceAPIException, ConnectionResetError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(e)
        print('Something went wrong. Error occured at %s. Wait for 1 min.' % (datetime.now().astimezone(timezone.utc)))
        time.sleep(60)
        client = Client(api_key, api_secret, testnet = testnet)
        bars = client.futures_historical_klines(symbol = symbol, interval = interval,
                                        start_str = start, end_str = end, limit = 1000)
        
    print(len(bars))
    df = pd.DataFrame(bars)
    df["Date"] = pd.to_datetime(df.iloc[:,0], unit = "ms")
    df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                  "Clos Time", "Quote Asset Volume", "Number of Trades",
                  "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.set_index("Date", inplace = True)
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors = "coerce")
    
    return df

def find_max(filename=None, type_max=None, type_trend=None, strategy=None):
    '''
    filename must be introduced with extension ".csv"
    '''
    if (filename==None or type_trend==None or type_max==None):
        print('all input parameters are mandatory')
    
    if (type == 'max'):
        opt_filename = f"opt_gather_max_{type_trend}.csv"
    if (type == 'max_net'):
        opt_filename = f"opt_gather_max_net_{type_trend}.csv"

    df = pd.read_csv(filename)
    newmax = pd.DataFrame()
    if (strategy == 'peak'):
        newmax = df[df.multiple_macd_peak_strategy == df.multiple_macd_peak_strategy.max()].drop_duplicates(keep='first')
    else:
        newmax = df[df.multiple_macd_strategy == df.multiple_macd_strategy.max()].drop_duplicates(keep='first')
    print('newmax', newmax)
    return newmax
   
def get_returns_outliers(start=None, symbol=None, end=None, interval=None, nsmall=None, nlarge=None):
    '''
    REMARK: Introduced time must be in Tokyo time (UTC+9) but the calculations will be in UTC
    Prepare all the fields of data necessary for the study. The interval of dates to be studied is the one
    given when delclaring the class. To prepare another interval of dates, please create another class instance.
    :param start: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-01-29-20:00"
    :type start: str.
    :param end: a string with the following format ""%Y-%m-%d-%H:%M:%S" .i.e. "2022-02-29-20:00:00"
    :type end: str.
    :param interval: string among the followings: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    :type interval: s
    '''
    from_time = None
    to_time = None
    if (start != None):
        from_time = int(datetime.strptime(start, "%Y-%m-%d-%H:%M:%S").timestamp()*1000)
    if (end != None):
        to_time = int(datetime.strptime(end, "%Y-%m-%d-%H:%M:%S").timestamp()*1000)
    data, client = get_history_v2(symbol=symbol, interval=interval, start=from_time, end=to_time)
    data['log_returns'] = np.log(data.Close.div(data.Close.shift(1)))
    
    nsmallest = data.log_returns.nsmallest(nsmall)
    nlargest = data.log_returns.nlargest(nlarge)
    
    dataToReturn = [
    nsmallest,
    nlargest,
    client, data
    ]
    
    return dataToReturn

def iterate_periods(ticker, interval, from_date, to_date, int_num, ema_slow, ema_fast, ema_signal, sma_slow, sma_fast):
    '''
    Helper function to iterate over out-of-sample intervals and compare the results of the backtesting strategy.
    "int_num" is the number of intervals that will be created backwards, with the same time length as:
    ---> to_date - from_date
    In this manner is posible to test the consistency of the strategy in different intervals and extract some statistics.
    '''
    
    res_lt = []
    
    for i in range(0,int_num):
                
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d-%H:%M") # end date object
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d-%H:%M") # start date object
        int_len_days = ((to_date_obj - from_date_obj).total_seconds())/(3600*24)
        to_date_obj_iter = to_date_obj - i*timedelta(days=int_len_days) # end date object for iteration 
        to_date_str_iter = to_date_obj_iter.strftime("%Y-%m-%d-%H:%M") # end date string for iteration     
        from_date_obj_iter = from_date_obj - i*timedelta(days=int_len_days) # start date object for iteration  
        from_date_str_iter = from_date_obj_iter.strftime("%Y-%m-%d-%H:%M") # start date string for iteration      
        macd_sma = Macd_long_backtester_sma(ticker)
        macd_sma.prepare_data(start=from_date_str_iter, end=to_date_str_iter, interval=interval)
        tp = macd_sma.execute_backtest(start=from_date_str_iter, ema_slow=ema_slow, ema_fast=ema_fast, ema_signal=ema_signal, sma_slow=sma_slow, sma_fast=sma_fast)
        trades_num = macd_sma.data_init.trades[macd_sma.data_init.trades == 1].sum()
        res_lt.append((tp[0], tp[3], tp[4], tp[7], from_date_str_iter, to_date_str_iter, trades_num))
    
    res_df = pd.DataFrame(data=res_lt, columns = ['multiple hold', 'sharpe hold', 'multiple strategy', 'sharpe strategy','from date', 'end_date', 'trades num'])
    return res_df  

def save_opt_results(res=None, opt_type=None, gross_or_net=None, interval=None, symbol=None):
    
    to_add = res.to_frame().T

    for col_name, value in to_add.iteritems():   
        if (col_name != 'start_opt' and col_name != 'end_opt' and col_name != 'macd_slow_opt' and col_name != 'macd_fast_opt' and col_name != 'macd_signal_opt' and col_name != 'sma_slow' and col_name != 'sma_fast' and col_name != 'success_trades_net' and col_name != 'failure_trades_net' and col_name != 'total_trades'):
            to_add[f"{col_name}"] = round(value.astype(float),2)
        else:
            pass    
        
    to_add['opt_type'] = opt_type
    to_add['gross_or_net'] = gross_or_net
    to_add['interval'] = interval
    to_add['symbol'] = symbol
    if os.path.exists(f"results.csv"):
        df_imported = pd.read_csv(f"results.csv", on_bad_lines='skip')
        df_complete = pd.concat([df_imported, to_add], axis = 0)
        df_complete.to_csv(f"results.csv", mode='w', index=False, header=True)
    else:
        to_add.to_csv(f"results.csv", mode='w', index=False, header=True) 

def remake_client(testnet=None):
    client = None
    if (testnet==False):
        api_key = "xxx"
        api_secret = "xxx"
        client = Client(api_key=api_key, api_secret=api_secret, tld = "com", testnet = testnet)

    if (testnet==True):
        api_key = "xxx"
        api_secret = "xxx"
        client = Client(api_key=api_key, api_secret=api_secret, tld = "com", testnet = testnet)
    
    return client

def save_ses_results(txt_filename=None):
    with open(txt_filename) as f:
        json_dict = json.load(f)
    json_dict_keys = json_dict.keys()
    df = pd.DataFrame(json_dict, columns=json_dict_keys, index=[0])
    if os.path.exists(f"results.csv"):
        df_imported = pd.read_csv(f"results.csv", on_bad_lines='skip')
        df_complete = pd.concat([df_imported, df], axis = 0)
        df_complete.to_csv(f"results.csv", mode='w', index=False, header=True)
    else:
        df.to_csv(f"results.csv", mode='w', index=False, header=True) 
    return df
