#!/usr/bin/env python
# coding: utf-8

# In[24]:


import ta
import trendet
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import sys
sys.path.append('/Users/jp/Desktop/Investment/utils')
import utils as utils
import math
from string import ascii_uppercase
from itertools import product
import os
from binance.client import Client
from binance.exceptions import *
import requests as requests
import time as time
import matplotlib.dates as mdates


# In[5]:


class Macd_long_backtester():
    '''
    Macd class for backtesting strategies
    How to use this class:
    1) Use 'prepare_data' method:
        INPUTS
        - start
        - end
        - interval
        
        COLUMNS CREATED
        - log_returns_hold
        - multiple_hold_acum
        - position
        - inv_sign
        
    In order to perform the backtest first it is necessary to follow 2.1) and 2.2) points in order to get the
    period of data of interest. Once this period (start and finish) has been chosen, it is necessary to create
    a new instance of the class and follow points 1) and 3)
        
    2.1) Use 'assign_trends' method: 
        INPUTS
        - window_size
        
        COLUMNS CREATED
        - Up Trend
        - Down Trend
    
    2.2) Use 'get_trend_dates' to obtain the dates 'start' and 'finish' for creating the new instance to perform
    the optimization
    
    3) Use 'execute_backtest' to perform the backtesting analysis for the period obtained, and with the macd
    paramters given in the point 1) in the new class instance
    
    SUMMARY:
    
    FIRST: points 1) 2.1) and 2.2) --> trends analysis and get period for analysis
    SECOND: points 1) and 3) --> new class instance for backtesting with period obtained with get_trend_dates 
    '''
    
    def __init__(self,symbol=None):
        
        """Macd long backtester constructor
        :param symbol: symbol from Binance from which to extract the data, .i.e. 'BTCUSDT'
        :type symbol: str.
        :param data: a dataframe with all the data extract from the Binance API for the selected function inputs.
        :type data: DataFrame
        :param data_uptrend: a dataframe with data extracted from self.data but only for the type of trend
        :type data_uptrend: str.
        :param data_downtrend: a dataframe with data extracted from self.data but only for the type of trend
        :type data_down_trend: str.
        :param data_sideways: a dataframe with data extracted from self.data but only for the type of trend
        :type data_sideways: str.
        """
        print('class version 1.1 is being used')
        self.symbol = symbol
        self.data_init = pd.DataFrame()
        self.trend_assigned = None
        self.type_trend = None
        self.trend_ref = None
        #Read-only parameters below, only informative of the last data prepared
        #Assigned in prepare_data() method.
        self.start = None
        self.end = None
        self.interval = None
        self.from_time = None
        self.to_time = None
        
        self.ema_slow = None
        self.ema_fast = None
        self.ema_signal = None
        self.opt_results = None

    
    def __repr__(self):
        return f"Macd_long_backtester(symbol={self.symbol})"

    def prepare_data(self, start=None, end=None, interval=None):
        '''
        REMARK: Introduced time must be in Tokyo time (UTC+9) but the calculations will be in UTC
        Prepare all the fields of data necessary for the study. The interval of dates to be studied is the one
        given when delclaring the class. To prepare another interval of dates, please create another class instance.
        :param start: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-01-29-20:00"
        :type start: str.
        :param end: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-02-29-20:00"
        :type end: str.
        :param interval: string among the followings: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        :type interval: str.
        '''
        
        self.start = start
        self.end = end
        self.interval = interval
        from_time = int(datetime.strptime(start, "%Y-%m-%d-%H:%M").timestamp()*1000)
        to_time = int(datetime.strptime(end, "%Y-%m-%d-%H:%M").timestamp()*1000)
        self.from_time = from_time
        self.to_time = to_time
        self.data_init = utils.get_history_v2(symbol=self.symbol, interval=interval, start=from_time, end=to_time)[0]
        self.data_init['log_returns_hold'] = np.log(self.data_init.Close.div(self.data_init.Close.shift(1)))
        self.data_init['multiple_hold_acum'] = np.exp(self.data_init.log_returns_hold.cumsum())
        #initialize positions and sign_inv
        self.data_init['position'] = 0
        self.data_init['inv_sign'] = 0
    
    def assign_trends(self, window_size=12, plot=False):
        '''
        REQUIREMENT: execute after "prepare_data" method AND a minimum window size of 12 days
        :param window_size: a trend that has a window higher than the introduced number is assigned.
        :type window_size: int.
        '''
        if (window_size < 12):
            print('Minimum window size is 12 (calculated with BTCUSDT so far)')
            return
        
        #THE SAMPLING INTERVAL MUST BE DAILY IN ORDER FOR THE ALGORITH TO WORK (AS FAR AS I KNOW)
        if (self.interval != '1d'):
            print("The interval that has to be used to assign trends is '1d'")
            return
        
        if (self.trend_assigned == True): 
            print("The trends have already been assigned, please execute first 'clean_assign_trend' before executing            this method again")
            return
        
        sns.set(style='darkgrid')
        res = trendet.identify_df_trends(df=self.data_init, column='Close', window_size=window_size)
        max_close = res.Close.max()      
                
        plt.figure(figsize=(20, 10))
        ax = sns.lineplot(x=res.index, y=res['Close'])
        labels = res['Up Trend'].dropna().unique().tolist()

        for label in labels:
            sns.lineplot(x=res.loc[res['Up Trend'] == label].index, y=res.loc[res['Up Trend'] == label].Close, color='green')
            pol1 = ax.axvspan(res.loc[res['Up Trend'] == label].index[0], res.loc[res['Up Trend'] == label].index[-1], alpha=0.2, color='green')
            coord = pol1.get_xy()
            xcoord = -1 + coord[0][0] + (coord[2][0] - coord[1][0])/2
            ax.annotate(label, (xcoord, max_close*3/4))

        labels = res['Down Trend'].dropna().unique().tolist()

        for label in labels:
            sns.lineplot(x=res.loc[res['Down Trend'] == label].index, y=res.loc[res['Down Trend'] == label].Close, color='red')
            pol2 =ax.axvspan(res.loc[res['Down Trend'] == label].index[0], res.loc[res['Down Trend'] == label].index[-1], alpha=0.2, color='red')
            coord = pol2.get_xy()
            xcoord = -1 + coord[0][0] + (coord[2][0] - coord[1][0])/2
            ax.annotate(label, (xcoord, max_close*2/4))

        increase_letter = False
        side_labels = []
        i = 0     
        
        for index, data in res.iterrows():
            if (not isinstance(data['Up Trend'], str) and not isinstance(data['Down Trend'], str)):
                if (increase_letter == True):
                    i+=1
                res.loc[index, 'Up Trend'] = ascii_uppercase[i]*2
                res.loc[index, 'Down Trend'] = ascii_uppercase[i]*2
                side_labels.append(ascii_uppercase[i]*2)
                increase_letter = False

            if (isinstance(data['Up Trend'], str) or isinstance(data['Down Trend'], str)):
                pass
                increase_letter = True 

        for label in side_labels:
            sns.lineplot(x=res.loc[res['Up Trend'] == label].index, y=res.loc[res['Up Trend'] == label].Close, color='blue')
            pol3 =ax.axvspan(res.loc[res['Up Trend'] == label].index[0], res.loc[res['Up Trend'] == label].index[-1], alpha=0.2, color='grey')
            coord = pol3.get_xy()
            xcoord = -0.5 + coord[0][0] + (coord[2][0] - coord[1][0])/2
            ax.annotate(label, (xcoord, max_close*1/4))

        self.trend_assigned = True
    
    def get_trend_dates(self, type_trend=None, trend_ref=None, do_plot=False):
        
        '''
        REQUIREMENT: execute after "assign_trends" method
        Once the trends have been assigned in data_init, in this function the type of trend seen in the trends chart
        and its trend_ref ('A', 'B', 'AA'...), are given and, as output we receive the start and the end dates of the trend.
        :param type: valid fields are 'Up Trend', 'Down Trend' and 'Sideways'
        :type type: str.
        :param trend_ref: letter/s that have been assigned in the 'Up Trend' and 'Down Trend' columns in data_init
        :type type: str.
        :param plot: if True, plots the selected trend
        :param type: bool.
        
        :return a tuple with two integers representing the time in milliseconds since the epoch for the start and end period.
        '''
        
        if (type_trend == 'Up Trend'):
            date_init = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10))

        if (type_trend == 'Down Trend'):
            date_init = self.data_init.loc[self.data_init['Down Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Down Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10)) 
                
        if (type_trend == 'Sideways'):
            #the letters are in both columns so it does not matter which column it is accesed
            date_init = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10))            
   
        date_init_int = int(date_init.timestamp()*1000)
        date_end_int = int(date_end.timestamp()*1000)
        self.trend_type = type_trend
        self.trend_ref = trend_ref
       
        print('date_init:', date_init, date_init_int)
        print('date_end:', date_end, date_end_int)    
                                
        return (date_init_int, date_end_int)

    
    def clean_assign_trend(self):
        '''Delete the columns 'Up Trend' and 'Down Trend' in data_init generated by the 'assign_trend_method'
        '''
        if (self.trend_assigned == None):
            print('trends must be assigned first')
            return
        
        self.data_init.drop(columns=['Up Trend', 'Down Trend'], inplace=True)
        self.trend_assigned = False
        
    def execute_backtest(self, start=None, ema_slow=None, ema_fast=None, ema_signal=None):
        '''
        REQUIREMENT: execute after "prepare_data" method
        :param start: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-01-29-20:00"
        :type start: str.
        :param end: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-02-29-20:00"
        :type end: str.
        '''
        #Prepare pre-data to start with non NaN at the backtesting period
        from_time_obj = datetime.strptime(start, "%Y-%m-%d-%H:%M")
#       ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        ema_diff = ema_slow + ema_signal + 2
        td = timedelta()
        if 'm' in self.interval:
            num_min = int(self.interval.replace('m',''))
            td = timedelta(minutes=num_min*(ema_diff))
        if 'h' in self.interval:
            num_h = int(self.interval.replace('h',''))
            td = timedelta(hours=num_h*(ema_diff))
        if 'd' in self.interval:
            num_day = int(self.interval.replace('d',''))
            td = timedelta(days=num_day*(ema_diff))
        if 'w' in self.interval:
            num_week = int(self.interval.replace('w',''))
            td = timedelta(weeks=num_week*(ema_diff))
        if 'M' in self.interval:
            num_week_m = int(self.interval.replace('M',''))
            td = timedelta(weeks=num_week_m * 4 * (ema_diff))
        pre_from_time_obj = from_time_obj - td
        pre_from_time = int((from_time_obj - td).timestamp()*1000)
        self.data_init_pre = utils.get_history_v2(symbol=self.symbol, interval=self.interval, start=pre_from_time, end=self.to_time)[0]
        #Assign the MACD parameters to the class to see which parameters have been used last
        self.ema_slow = ema_slow
        self.ema_fast = ema_fast
        self.ema_signal = ema_signal 
        #obtaining MACD instance from python ta
        macd_diff = ta.trend.MACD(close=self.data_init_pre.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd_diff()
        macd_macd = ta.trend.MACD(close=self.data_init_pre.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd()
        macd_signal = ta.trend.MACD(close=self.data_init_pre.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd_signal()
        #assigning the values of macd to ticker dataframe
        self.data_init_pre['macd_diff'] = macd_diff
        self.data_init_pre['macd_macd'] = macd_macd
        self.data_init_pre['macd_signal'] = macd_signal   
        self.data_init = self.data_init_pre.loc[from_time_obj:].copy()
        #Initialize again buy-and-hold parameters for new data
        self.data_init['log_returns_hold'] = np.log(self.data_init.Close.div(self.data_init.Close.shift(1)))
        self.data_init['multiple_hold_acum'] = np.exp(self.data_init.log_returns_hold.cumsum())
        #initialize again positions and sign_inv for new data
        self.data_init['position'] = 0
        self.data_init['inv_sign'] = 0
        #stablish neutral conditions
        ht_pos = self.data_init.macd_diff.shift(1) > 0
        ht_plusone_neg = self.data_init.macd_diff < 0
        #stablish neutral positions
        self.data_init.loc[ht_pos & ht_plusone_neg, 'inv_sign'] = -1
        #stablish buy conditions
        ht_neg = self.data_init.macd_diff.shift(1) < 0
        ht_plusone_pos = self.data_init.macd_diff > 0
        #stablish buy positions
        self.data_init.loc[ht_neg & ht_plusone_pos, 'inv_sign'] = 1
        #create neutral and buy positions algorithm
        for index, data in self.data_init.iterrows():
            if (data.inv_sign == 1):
                self.data_init.loc[index, 'position'] = 1
                one_delta_pos = index + (self.data_init.index[1]-self.data_init.index[0])
                self.data_init_sub_buy = self.data_init.loc[one_delta_pos:]
                for index_sub_buy, data_sub_buy in self.data_init_sub_buy.iterrows():
                    if (data_sub_buy.inv_sign == 0):
                        self.data_init.loc[index_sub_buy, 'position'] = 1
                    if (data_sub_buy.inv_sign != 0):
                        break
            if (data.inv_sign == 0):
                pass
            if(data.inv_sign == -1):
                self.data_init.loc[index, 'position'] = 0

        #stablish the trading costs and the number of trades done
        self.data_init['trades'] = 0
        trading_cost = np.log(1 - 0.00075) + np.log(1 - 0.0001)
        trade_exec_cond = self.data_init.position.diff().fillna(0).abs() != 0
        self.data_init.loc[trade_exec_cond, 'trades'] = 1
        #calculate strategy returns
        self.data_init['macd_log_returns'] = self.data_init.log_returns_hold * self.data_init.position.shift(1)
        self.data_init['macd_log_returns_net'] = self.data_init.macd_log_returns + self.data_init.trades * trading_cost
        self.data_init['macd_log_returns_acum'] = np.exp(self.data_init.macd_log_returns.cumsum())
        self.data_init['macd_log_returns_net_acum'] = np.exp(self.data_init.macd_log_returns_net.cumsum())

        #calculating the function outputs
        multiple_hold = np.exp(self.data_init.log_returns_hold.sum())
        ann_log_mean_hold = self.data_init.log_returns_hold.mean() * 365
        ann_log_std_hold = self.data_init.log_returns_hold.std() * np.sqrt(365)
        sharpe_ratio_hold = ann_log_mean_hold / ann_log_std_hold
        
        multiple_macd_strategy = np.exp(self.data_init.macd_log_returns.sum())
        ann_log_mean_macd = self.data_init.macd_log_returns.mean() * 365
        ann_log_std_macd = self.data_init.macd_log_returns.std() * np.sqrt(365)
        sharpe_ratio_macd = ann_log_mean_macd / ann_log_std_macd
        
        multiple_macd_strategy_net = np.exp(self.data_init.macd_log_returns_net.sum())
        ann_log_mean_macd_net = self.data_init.macd_log_returns_net.mean() * 365
        ann_log_std_macd_net = self.data_init.macd_log_returns_net.std() * np.sqrt(365)
        sharpe_ratio_macd_net = ann_log_mean_macd_net / ann_log_std_macd_net
        tuple_return = (multiple_hold, ann_log_mean_hold, ann_log_std_hold, sharpe_ratio_hold, multiple_macd_strategy, ann_log_mean_macd, ann_log_std_macd, sharpe_ratio_macd, multiple_macd_strategy_net, ann_log_mean_macd_net, ann_log_std_macd_net, sharpe_ratio_macd_net)

        df_return = pd.DataFrame(data=[list(tuple_return)], columns=['multiple_hold', 'ann_log_mean_hold', 'ann_log_std_hold', 'sharpe_ratio_hold', 'multiple_macd_strategy', 'ann_log_mean_macd', 'ann_log_std_macd', 'sharpe_ratio_macd', 'multiple_macd_strategy_net', 'ann_log_mean_macd_net', 'ann_log_std_macd_net', 'sharpe_ratio_macd_net'])
        print(df_return)
        return tuple_return
    
    def plot_backtest_results(self, start_plot=None, end_plot=None, width_bars=0.1):
        # from IPython.core.display import display, HTML
        # display(HTML("<style>.container { width:100% !important; }</style>"))
        colors=[]

        fig, (close_ax, macd_ax, acum_ax) = plt.subplots(nrows=3, ncols=1, figsize=(30,20), gridspec_kw={'height_ratios': [4,2,4]}, sharex=True)

        close_ax.grid(visible=True, which='major', axis='x', color='grey')
        macd_ax.grid(visible=True, which='major', axis='x', color='grey')
        acum_ax.grid(visible=True, which='major', axis='x', color='grey')
        close_ax.grid(visible=True, which='major', axis='y', color='grey')
        macd_ax.grid(visible=True, which='major', axis='y', color='grey')
        acum_ax.grid(visible=True, which='major', axis='y', color='grey')
        close_ax.grid(visible=True, which='minor', axis='x', color='grey')
        macd_ax.grid(visible=True, which='minor', axis='x', color='grey')
        acum_ax.grid(visible=True, which='minor', axis='x', color='grey')        

        close_ax.tick_params(labelrotation=45)
        macd_ax.tick_params(labelrotation=45)
        acum_ax.tick_params(labelrotation=45)

        close_ax.margins(0)
        macd_ax.margins(0)
        acum_ax.margins(0)
        
        close_ax.set_ylim(auto=True)

#         days = mdates.DayLocator()
#         macd_ax.xaxis.set_minor_locator(days)
#         date_form = mdates.DateFormatter('%Y-%m-%dT%H:%M:%S')
#         close_ax.xaxis.set_major_formatter(date_form)
        
        data_init_ready = self.data_init              
        if ((start_plot != None) and (end_plot !=None)):
            cond_start = self.data_init.index >= start_plot
            cond_end = self.data_init.index <= end_plot
            data_init_ready = self.data_init[cond_start&cond_end]
                
        for index, value in data_init_ready.macd_diff.iteritems():
            if value > 0:
                colors.append('g')
            else:
                colors.append('r')
                
        close_ax.plot(data_init_ready.index, data_init_ready.Close) #plot the data without shifting

        #shift one position the inv_sign only for plotting the signal in the day after is found, without shifting the
        #Close prices
        data_init_ready_shift = data_init_ready.copy()
        data_init_ready_shift['inv_sign'] = data_init_ready.inv_sign.shift(1)
        buy_pos = data_init_ready_shift.inv_sign == 1              
        buy_trade = data_init_ready_shift.loc[buy_pos]
        sell_pos = data_init_ready_shift.inv_sign == -1             
        sell_trade = data_init_ready_shift.loc[sell_pos]
        close_ax.scatter(sell_trade.index, sell_trade.Close.loc[sell_trade.index], marker='^', color='r', s=100)
        close_ax.scatter(buy_trade.index, buy_trade.Close.loc[buy_trade.index], marker='^', color='g', s=100)
        
        macd_ax.bar(x= data_init_ready.index, height= data_init_ready.macd_diff, width=width_bars, align='center', color=colors, edgecolor='black')

        acum_ax.plot(data_init_ready.index, data_init_ready.multiple_hold_acum)
        acum_ax.plot(data_init_ready.index, data_init_ready.macd_log_returns_acum)  
        acum_ax.legend(['multiple_hold_acum','macd_log_returns_acum'],fontsize=14)
        
    def execute_opt(self, start_opt=None, end_opt=None, interval_opt=None, ema_slow_opt=None, ema_fast_opt=None, ema_sign_opt=None, int_for_max=None, type_trend=None, trend_ref=None):
        '''
        REMARK: Introduced time must be in Tokyo time (UTC+9) but the calculations will be in UTC
        '''
        interval_opt = interval_opt
        macd_slow_opt = range(*ema_slow_opt)
        macd_fast_opt = range(*ema_fast_opt)
        macd_signal_opt = range(*ema_sign_opt)
        combinations = list(product(interval_opt, macd_slow_opt, macd_fast_opt, macd_signal_opt))
        
        results = []
        for comb in combinations:
            try:
                self.prepare_data(start=start_opt, end=end_opt, interval=comb[0])
                tuple_results = (comb[0], comb[1], comb[2], comb[3], *self.execute_backtest(start=self.start, ema_slow=comb[1], ema_fast=comb[2], ema_signal=comb[3]), trend_ref, start_opt, end_opt)
                results.append(tuple_results)
                print(f"processed {len(results)} out of a total {len(combinations)}")
            except (BinanceAPIException, ConnectionResetError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                    print('Something went wrong. Error occured at %s. Wait for 60s.' % (datetime.now().astimezone(timezone.utc)))
                    time.sleep(60)
                    api_key = "Q3Zsx6rO7uy0YntyWjb9CTGxbQAfENBxbPAkeOtksXm2AcLcu1y7IOj1fgPFtutO"
                    api_secret = "LeiOCoJdBuCtfgrt1WfsBweeyC2ZwuogPuDrkXFTioEGoaZYOGkju1GRM3yVqp7v"
                    client = Client(api_key, api_secret)
            except KeyboardInterrupt as e2:
                    print("error type is 'KeyboardInterrupt'. The data calculated so far has been stored in self.opt_results")
                    break
        
        mg = pd.DataFrame(data=results, columns = ['interval_opt', 'macd_slow_opt', 'macd_fast_opt', 'macd_signal_opt','multiple_hold', 'ann_log_mean_hold', 'ann_log_std_hold', 'sharpe_ratio_hold', 'multiple_macd_strategy', 'ann_log_mean_macd', 'ann_log_std_macd', 'sharpe_ratio_macd', 'multiple_macd_strategy_net', 'ann_log_mean_macd_net', 'ann_log_std_macd_net', 'sharpe_ratio_macd_net', 'trend_ref', 'start_opt', 'end_opt'])
        #Filtering only meaningfull combinations
        cond1 = mg.multiple_macd_strategy != 1 #not enough data to carry out a single crossover
        cond2 = mg.macd_slow_opt > mg.macd_fast_opt
        mg_filt = mg.loc[cond1&cond2].copy()
        self.opt_results = mg_filt.copy()
        self.opt_comb_num = len(combinations)
        
        #only show results for desired interval
        cond3 = mg_filt.interval_opt == int_for_max
        mg_desired_interval = mg_filt[cond3].copy()
        
        cond_max = mg_desired_interval.multiple_macd_strategy == mg_desired_interval.multiple_macd_strategy.max()
        multiple_macd_strategy_opt_max = mg_desired_interval[cond_max]
        
        cond_net_max = mg_desired_interval.multiple_macd_strategy_net == mg_desired_interval.multiple_macd_strategy_net.max()
        multiple_macd_strategy_net_opt_max = mg_desired_interval[cond_net_max]
        
        self.multiple_macd_strategy_max = multiple_macd_strategy_opt_max
        self.multiple_macd_strategy_net_max = multiple_macd_strategy_net_opt_max

        if os.path.exists(f"{type_trend}.csv"):
            df_imported = pd.read_csv(f"{type_trend}.csv")
            df_complete = pd.concat([df_imported, self.opt_results], axis = 0)
            df_complete.to_csv(f"{type_trend}.csv", mode='w', index=False, header=True)
        else:
            self.opt_results.to_csv(f"{type_trend}.csv", mode='w', index=False, header=True)
        
        

