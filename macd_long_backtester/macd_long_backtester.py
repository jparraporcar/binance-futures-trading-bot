#!/usr/bin/env python
# coding: utf-8

# In[103]:


import ta
import trendet
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.append('/Users/jp/Desktop/Investment/utils')
import utils as utils
import math
from string import ascii_uppercase
from itertools import product


# In[106]:


class Macd_long_backtester():
    
    '''
    Macd class for backtesting strategies
    How to use this class:
    1) Use 'prepare_data' method:
        INPUTS
        - start
        - end
        - interval
        - macd parameters
        
        COLUMNS CREATED
        - macd_diff
        - macd_macd
        - macd_signal
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
        self.symbol = symbol
        self.data_init = pd.DataFrame()
        self.trend_assigned = None
        self.interval = None
        #Read-only paramters below, only informative of the last data prepared
        self.start = None
        self.end = None
        self.ema_slow = None
        self.ema_fast = None
        self.ema_signal = None
        self.opt_results = None
    
    def __repr__(self):
        return f"Macd_long_backtester(symbol={self.symbol})"

    def prepare_data(self, start=None, end=None, interval=None):
        '''Prepare all the fields of data necessary for the study. The interval of dates to be studied is the one
        given when delclaring the class. To prepare another interval of dates, please create another class instance.
        :param start: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-01-29-20:00"
        :type start: str.
        :param end: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-02-29-20:00"
        :type end: str.
        :param interval: string among the followings: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        :type interval: str.
        :param ema_slow: integer representing the length of the ema for the slow part of the macd
        :type ema_slow: int.
        :param ema_fast: integer representing the length of the ema for the fast part of the macd
        :type ema_fast: int.
        :param ema_signal: integer representing the length of the ema for the macd signal
        :type ema_signal: int.
        '''

        self.start = start
        self.end = end
        self.interval = interval
        from_time = int(datetime.strptime(start, "%Y-%m-%d-%H:%M").timestamp()*1000)
        to_time = int(datetime.strptime(end, "%Y-%m-%d-%H:%M").timestamp()*1000)
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
    
    def get_trend_dates(self, type=None, trend_ref=None, do_plot=False):
        
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
        
        if (type == 'Up Trend'):
            date_init = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10))

        if (type == 'Down Trend'):
            date_init = self.data_init.loc[self.data_init['Down Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Down Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10)) 
                
        if (type == 'sideways'):
            #the letters are in both columns so it does not matter which column it is accesed
            date_init = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[0]
            date_end = self.data_init.loc[self.data_init['Up Trend'] == trend_ref].index[-1]
            if (do_plot == True):
                mask1 = (self.data_init.index >= date_init) 
                mask2 = (self.data_init.index <= date_end) 
                self.data_init.Close[mask1 & mask2].plot(figsize=(15,10))            
   
        date_init_int = int(date_init.timestamp()*1000)
        date_end_int = int(date_end.timestamp()*1000)
       
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
        
    def execute_backtest(self, ema_slow=None, ema_fast=None, ema_signal=None):
        '''
        REQUIREMENT: execute after "prepare_data" method
        '''
        #Assign the MACD parameters to the class to see which para,tershave been used last
        self.ema_slow = ema_slow
        self.ema_fast = ema_fast
        self.ema_signal = ema_signal 
        #obtaining MACD instance from python ta
        macd_diff = ta.trend.MACD(close=self.data_init.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd_diff()
        macd_macd = ta.trend.MACD(close=self.data_init.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd()
        macd_signal = ta.trend.MACD(close=self.data_init.Close, window_slow=ema_slow, window_fast=ema_fast, window_sign=ema_signal, fillna=False).macd_signal()
        #assigning the values of macd to ticker dataframe
        self.data_init['macd_diff'] = macd_diff
        self.data_init['macd_macd'] = macd_macd
        self.data_init['macd_signal'] = macd_signal        
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
                self.data_init_sub_sell = self.data_init.loc[index + timedelta(minutes=1):]
                for index_sub_sell, data_sub_sell in self.data_init_sub_sell.iterrows():
                    if (data_sub_sell.inv_sign == 0):
                        self.data_init.loc[index_sub_sell, 'position'] = 1
                    if (data_sub_sell.inv_sign != 0):
                        break
            if (data.inv_sign == 0):
                pass
            if(data.inv_sign == -1):
                self.data_init.loc[index, 'position'] = 0
                self.data_init_sub_buy = self.data_init.loc[index + timedelta(minutes=1):]
                for index_sub_buy, data_sub_buy in self.data_init_sub_buy.iterrows():
                    if (data_sub_buy.inv_sign == 0):
                        self.data_init.loc[index_sub_buy, 'position'] = 0
                    if (data_sub_buy.inv_sign != 0):
                        break
        #stablish the trading costs and the number of trades done
        self.data_init['trades'] = 0
        trading_cost = np.log(1 - 0.00075) + np.log(1 - 0.0001)
        trade_exec_cond = self.data_init.position.diff().fillna(0).abs() != 0
        self.data_init.loc[trade_exec_cond, 'trades'] = 1
        #calculate strategy returns
        self.data_init['macd_log_returns'] = self.data_init.log_returns_hold * self.data_init.position.shift(1)
        self.data_init['macd_log_returns_net'] = self.data_init.macd_log_returns + self.data_init.trades * trading_cost
        #calculating the function outputs
        multiple_hold = np.exp(self.data_init.log_returns_hold.sum())
        multiple_macd_strategy = np.exp(self.data_init.macd_log_returns.sum())
        multiple_macd_strategy_net = np.exp(self.data_init.macd_log_returns_net.sum())
        tuple_return = (multiple_hold, multiple_macd_strategy, multiple_macd_strategy_net)

        return tuple_return
    
    def execute_opt(self, start_opt=None, end_opt=None, interval_opt=None, ema_slow_opt=None, ema_fast_opt=None, ema_sign_opt=None, int_for_max=None):
       
        interval_opt = interval_opt
        macd_slow_opt = range(*ema_slow_opt)
        macd_fast_opt = range(*ema_fast_opt)
        macd_signal_opt = range(*ema_sign_opt)
        combinations = list(product(interval_opt, macd_slow_opt, macd_fast_opt, macd_signal_opt))
        
        results = []
        for comb in combinations:
            self.prepare_data(start=start_opt, end=end_opt, interval=comb[0])
            results.append(self.execute_backtest(comb[1], comb[2], comb[3]))

        combinations_df = pd.DataFrame(data=combinations, columns=['interval_opt', 'macd_slow_opt', 'macd_fast_opt', 'macd_signal_opt'])
        many_results_df = pd.DataFrame(data=results, columns = ['multiple_hold', 'multiple_macd_strategy', 'multiple_macd_strategy_net'])
        mg=pd.merge(combinations_df,many_results_df, how='inner', left_index=True, right_index=True)
        #Filtering only meaningfull combinations
        cond1 = mg.multiple_macd_strategy != 1 #not enough data to carry out a single crossover
        cond2 = mg.macd_slow_opt > mg.macd_fast_opt
        mg_filt = mg.loc[cond1&cond2].copy()
        self.opt_results = mg_filt
        
        #only show results for desired interval
        cond3 = mg_filt.interval_opt == int_for_max
        mg_desired_interval = mg_filt[cond3].copy()
        
        cond_max = mg_desired_interval.multiple_macd_strategy == mg_desired_interval.multiple_macd_strategy.max()
        multiple_macd_strategy_opt_max = mg_desired_interval[cond_max]
        
        cond_net_max = mg_desired_interval.multiple_macd_strategy_net == mg_desired_interval.multiple_macd_strategy_net.max()
        multiple_macd_strategy_net_opt_max = mg_desired_interval[cond_net_max]
        
        self.multiple_macd_strategy_max = multiple_macd_strategy_opt_max
        self.multiple_macd_strategy_net_max = multiple_macd_strategy_net_opt_max


# ## Results tested against the result coming from the file '2022Sep3th_BTC_MACD_long_only_CHECK_OK_Working' and it is the same result for the given paramaters: <br>
# 
# __1) macd_inst = Macd_long_backtester(symbol='BTCUSDT')__<br>
# 
# __2) macd_inst.prepare_data(interval='1d', start='2018-10-29-20:00', end='2022-08-29-20:00')__<br>
# 
# __3) macd_inst.assign_trends(window_size=60, plot=True)__<br>
# 
# __4) macd_inst.execute_backtest(ema_slow=24, ema_fast=12, ema_signal=9) = (3.2042562870505837, 4.8108773219256085, 4.41872336884791)__<br>
# 
# __And now results coming from the mentioned file: <br>
# '2022Sep3th_BTC_MACD_long_only_CHECK_OK_Working':__ <br>
# 
# __multiple_hold = np.exp(btcusdt.log_returns.sum()) <br>
# multiple_hold <br>
# 3.2042562870505837__
# 
# __multiple_macd_strategy = np.exp(btcusdt.macd_log_returns.sum()) <br>
# multiple_macd_strategy__ <br>
# __4.8108773219256085__ <br>
# 
# __multiple_macd_strategy_net = np.exp(btcusdt.macd_log_returns_net.sum()) <br>
# multiple_macd_strategy_net__ <br>
# __4.41872336884791__ <br>
# 
# 
# 
# 
# 