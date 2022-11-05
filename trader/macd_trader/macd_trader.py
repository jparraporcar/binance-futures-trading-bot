#!/usr/bin/env python
# coding: utf-8

# In[9]:


from binance.client import Client
from binance import ThreadedWebsocketManager
import binance as bn
import pandas as pd
import sys
from datetime import datetime, timedelta
import ta as ta
import numpy as np
import json
import sys
sys.path.append('/Users/jp/Desktop/Investment/utils')
import utils
import matplotlib.pyplot as plt
import smtplib
import time
import json


# In[8]:


class Macd_trader():
    """
    Class to perform live testing using Binance testnet stream of data
    """ 
    def __init__(self, symbol=None, units='0.0006', interval=None, ema_slow=None, ema_fast=None, ema_signal=None, testnet=None, assigned_duration_minutes=None, assigned_emergency_price_chg_pct=None):
        """
        :param symbol: ticker in Binance, i.e. "BTCUSDT"
        :type symbol: str.
        ----
        :param units: amount of base units, i.e. "BTC"
        :param type: float.
        ----
        :param interval: a string among the followings: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        :type interval: str.
        ----
        :param ema_slow: EMA slow for MACD calculation
        :type ema_slow: int.
        ----
        :param ema_fast: EMA fast for MACD calculation
        :type ema_fast: int.
        ----
        :param ema_signal: EMA signal for MACD calculation
        :type ema_signal: int.
        ----
        :param testnet: if True, testnet is used, otherwise REAL Binance account
        :type testnet: bool.
        ----
        :param assigned_duration_minutes: amount of minutes that the sesion is expected to last, if no problems appear.
        :type assigned_duration_minutes: int.
        ----
        :param: assigned_emergency_price_chg_pct: percentatge threshold (in absolute value) above which a sell order will be executed for safety purposes.
        In the case of a price increase the pct is taken as double of the value introduced (ratio 2 win : 1 lose)
        """
        self.units = units
        self.symbol = symbol
        self.interval = interval
        self.ema_slow = ema_slow
        self.ema_fast = ema_fast
        self.ema_signal = ema_signal 
        self.testnet = testnet 
        self.assigned_duration_minutes = assigned_duration_minutes
        self.assigned_emergency_price_chg_pct = assigned_emergency_price_chg_pct
        self.run_end_time_utc = None #time in UTC when the calculation finished
        self.run_end_delta = None #amount of time that has passed since the beginning of the calculation
        self.data = pd.DataFrame() #initialized dataframe to contain all OHLC data
        self.trades = 0 #counter of the number of trades
        self.trade_values = [] #all trading positions consecutive, long/short... or short/long...
        self.trade_values_time = [] #time at which each value in trade_values was appended
        self.position = None #initially no position is decided, it is pending to analysis recent data of macd to decide if it is long (1), neutral (0) or no position ('np')
        self.client = None #Binance client just if necessary
        self.trade_start_time_utc = None # time in utc to be defined when the stream of OHLC starts ( this time
        self.twm = None # Initialize ws client
        self.initial_balance_USDT = None #amount of USDT in account before a trade
        self.final_balance_USDT = None #amount of USDT in account after a trade
        self.initial_balance_BTC = None #amount of BTC in account before a trade
        self.final_balance_BTC = None #amount of BTC in account after a trade
        self.cum_profits = None #accumulated profits in the trading sesion
        self.close_pair = [] #two consecutive "close" prices to implement the safety returns threshold
        self.emergency_price_chg_flag = False #flag to activate the signal
        self.emergency_msg = None #message to be sent when emergency price signal activated
        self.pct_price_chg = None #percetatge of change in price monitored every second
        self.conn = None #smtp connection
        self.login_mail() #initialize smtp google account
        self.increase_counter = 0 #counter to monitor consecutive sharp increases in price per second
        self.decrease_counter = 0 #counter to monitor consecutive sharp decreases in price per second
        self.bot_name = "" #bot name to be defined in each child class
        
    def stream_candles(self, msg):
        self.event_time = pd.to_datetime(msg["E"], unit = "ms")
        start_time = pd.to_datetime(msg["k"]["t"], unit = "ms")
        first   = float(msg["k"]["o"])
        high    = float(msg["k"]["h"])
        low     = float(msg["k"]["l"])
        close   = float(msg["k"]["c"])
        volume  = float(msg["k"]["v"])
        complete=       msg["k"]["x"]
    
        # feed df (add new bar / update latest bar)
        self.data.loc[start_time, 'Open'] = first
        self.data.loc[start_time, 'High'] = high
        self.data.loc[start_time, 'Low'] = low
        self.data.loc[start_time, 'Close'] = close
        self.data.loc[start_time, 'Volume'] = volume
        self.data.loc[start_time, 'Complete'] = complete
        # add balance_ini column with the balance in the latest bar before executing order (after complete==True)
        self.data.loc[start_time, 'balance_ini_USDT'] = np.nan
        self.data.loc[start_time, 'balance_ini_BTC'] = np.nan
        # initialize quote_units
        self.data.loc[start_time, 'quote_units'] = np.nan
        #update MACD parameters with each ws retrieval
        macd_diff = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd_diff()
        macd_macd = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd()
        macd_signal = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd_signal()         
        self.data.loc[start_time, 'macd_diff'] = macd_diff.iloc[-1]
        self.data.loc[start_time, 'macd_macd'] = macd_macd.iloc[-1]
        self.data.loc[start_time, 'macd_signal'] = macd_signal.iloc[-1]
                
        print(".", end = "", flush = True) # just print something to get a feedback (everything OK)
        dt = datetime.utcnow() - self.trade_start_time_utc
        
        if ((dt) > timedelta(minutes=self.assigned_duration_minutes)):
            self.stop_ses()
            
        if (len(self.close_pair) == 0):
            self.close_pair.append(close)
        if (len(self.close_pair) == 1):
            self.close_pair.insert(0,close)
        if (len(self.close_pair) == 2):
            self.close_pair.pop()
            self.close_pair.insert(0,close)
            self.pct_price_chg = ((self.close_pair[1]/self.close_pair[0])-1)
            print(self.pct_price_chg)
            
            # condition for emergency price increase
            if (self.pct_price_chg > 2*self.assigned_emergency_price_chg_pct):
                self.emergency_price_chg_flag = True
                self.decrease_counter = 0
                self.increase_counter += 1
                self.emergency_msg = f"PRICE CHANGE - INCREASE - {self.increase_counter}"
                print(self.emergency_msg)
                
                if (self.increase_counter < 3):
                    pass
                elif (self.increase_counter == 3):
                    self.emergency_position_eval_increase()                               
                    self.emergency_price_chg_flag = False
                    self.increase_counter = 0
                    self.end_socket()
                    time.sleep(45)
                    self.init_socket()
                else:
                    pass
            # condition for emergency price decrease                    
            elif (self.pct_price_chg < -1*self.assigned_emergency_price_chg_pct):
                self.emergency_price_chg_flag = True
                self.increase_counter = 0
                self.decrease_counter += 1
                self.emergency_msg = f"PRICE CHANGE - DECREASE - {self.decrease_counter}"
                print(self.emergency_msg)                
            
                if (self.decrease_counter < 3):
                    pass
                elif (self.decrease_counter == 3):
                    self.emergency_position_eval_decrease()
                    self.emergency_price_chg_flag = False
                    self.decrease_counter = 0
                    self.end_socket()
                    time.sleep(45)
                    self.init_socket()
                else:
                    pass
            # condition for no emergency price change        
            else:
                pass
        
        # Every second that the execution arrives here, it means one of these two things:
        # 1) there has been no emergency price change
        # 2) there has been an emergency price change but it has been procesed
        if (complete == True):
            if (self.emergency_price_chg_flag==False): #continue the normal process if no emergency has been detected or if the flag has been set to false after processing an emergency
                self.stablish_positions()
                self.execute_trades()
            else: #if we enter into the completed kandle but we are in the middle of a emergency price: do nothing
                  # since it means that we are in the middle of assessing an emergency price change situation 
                pass
            
    def emergency_position_eval_increase(self):
                
            if (len(self.trade_values) == 0): #the price increase happens before any trade has been made -> buy
                self.position = 1
                self.execute_trades()
                return

            if (self.position == 0): #current position is neutral -> buy
                self.position = 1
                self.execute_trades()

            elif (self.position == 'np' and self.trade_values[-1] > 0): #current position is neutral -> buy  
                self.position = 1
                self.execute_trades()   

            elif (self.position == 1): #current position is long -> do nothing
                pass

            elif (self.position == 'np' and self.trade_values[-1] < 0): #current position is long -> do nothing
                pass

            else:
                pass
            
    def emergency_position_eval_decrease(self):
                
            if (len(self.trade_values) == 0): #the price decrease happens before any trade has been made -> mark as a 'np' and send to execute_trades() logic
                self.position = 'np'
                self.execute_trades()
                return

            if (self.position == 0): #current position is neutral -> do nothing
                pass

            elif (self.position == 'np' and self.trade_values[-1] > 0): #current position is neutral -> do nothing  
                pass  

            elif (self.position == 1): #current position is long -> sell
                self.position = 0
                self.execute_trades()

            elif (self.position == 'np' and self.trade_values[-1] < 0): #current position is long -> sell
                self.position = 0
                self.execute_trades()

            else:
                pass    
    
    def start_trading(self):
        self.trade_start_time_utc = datetime.utcnow()
        self.prepare_recent_data()
        self.initial_balance_USDT = round(float(self.client.get_asset_balance(asset='USDT')['free']),3)
        self.initial_balance_BTC = round(float(self.client.get_asset_balance(asset='BTC')['free']),3)
        self.init_socket()
        
    
    def init_socket(self):
        self.twm = ThreadedWebsocketManager()
        self.twm.start() 
        
        try:                  
            self.twm.start_kline_socket(callback = self.stream_candles, symbol = self.symbol, interval = self.interval)
        except (BinanceAPIException, ConnectionResetError, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            print(e)
            print('Something went wrong. Error occured at %s. The sesions will be automatically stopped after GOING NEUTRAL.' % (datetime.now().astimezone(timezone.utc)))
            self.stop_ses()
    
    def end_socket(self):
        self.twm.stop()
    
    def stop_ses(self, save_to_file=True):

        self.run_end_time_utc = datetime.utcnow()
        dt = self.run_end_time_utc - self.trade_start_time_utc
        self.run_end_delta = round(dt.seconds/60,0)
        print(f"trading sesion duration = {self.run_end_delta} minutes up to {self.assigned_duration_minutes}")
        
        if self.position == 0:
            print("STOP")

        if self.position == 1:
            order = self.client.create_order(symbol = self.symbol, side = "SELL", type = "MARKET", quantity = self.units)
            self.report_trade(order, "GOING NEUTRAL AND STOP") 
            self.position = 0
            
        if self.position == 'np':
            if (len(self.trade_values) == 0):
                print("STOP BEFORE PLACING ORDERS")            
            
            elif (self.trade_values[-1] < 0):
                self.position = 0 # latest neutral position
                li = self.data.index == self.data.index[-1]
                self.data.loc[li, 'position'] = self.position 
                order = self.client.create_order(symbol = self.symbol, side = "SELL", type = "MARKET", quantity = self.units)
                self.report_trade(order, "GOING NEUTRAL AND STOP") 
            else:
                print("STOP")

        self.twm.stop()
        
        trades_num_filter = self.data.position.dropna() != None
        self.trades = len(trades_num_filter)
        start_ses = datetime.strftime(self.trade_start_time_utc, "%Y-%m-%d-%H:%M")
        li = self.data.index == self.data.index[-1]
        self.data.loc[li, 'position'] = self.position
        self.final_balance_USDT = round(float(self.client.get_asset_balance(asset='USDT')['free']),3)
        self.final_balance_BTC = round(float(self.client.get_asset_balance(asset='BTC')['free']),3)
        
        if (save_to_file == True):
            self.save_to_files()

    def execute_trades(self):
        cond_last = self.data.index == self.data.index[-1]
        #execute trades depending on the positions stablished in define_strategy()
        if self.position == 1:
            self.data.loc[cond_last, 'balance_ini_USDT'] = round(float(self.client.get_asset_balance(asset='USDT')['free']),3)
            self.data.loc[cond_last, 'balance_ini_BTC'] = round(float(self.client.get_asset_balance(asset='BTC')['free']),3)                        
            order = self.client.create_order(symbol = self.symbol, side = "BUY", type = "MARKET", quantity = self.units)
            self.report_trade(order, "GOING LONG")

        if self.position == 0:
            self.data.loc[cond_last, 'balance_ini_USDT'] = round(float(self.client.get_asset_balance(asset='USDT')['free']),3)
            self.data.loc[cond_last, 'balance_ini_BTC'] = round(float(self.client.get_asset_balance(asset='BTC')['free']),3)                                    
            order = self.client.create_order(symbol = self.symbol, side = "SELL", type = "MARKET", quantity = self.units)
            self.report_trade(order, "GOING NEUTRAL")

        if self.position == 'np':
            pass

    def report_trade(self, order, going):
        last_index = self.data.index[-1]
        cond_last = self.data.index == self.data.index[-1]
        # extract data from order object
        side = order["side"]
        time = pd.to_datetime(order["transactTime"], unit = "ms")
        base_units = float(order["executedQty"])
        quote_units = float(order["cummulativeQuoteQty"])
        
        # calculate trading profits
        self.trades += 1
        
        last_t_str = datetime.strftime(self.data.index[-1], '%Y-%m-%d-%H:%M')
        
        if side == "BUY":
            self.trade_values.append(-quote_units)
            self.data.loc[cond_last, 'quote_units'] = -quote_units
        elif side == "SELL":
            self.trade_values.append(quote_units)
            self.data.loc[cond_last, 'quote_units'] = quote_units
        
        self.trade_values_time.append(last_t_str)
            
        if self.trades % 2 == 0:
            real_profit = round(np.sum(self.trade_values[-2:]), 3) 
            cum_profits = round(np.sum(self.trade_values), 3)
        else: 
            real_profit = 0
            cum_profits = round(np.sum(self.trade_values[:-1]), 3)
           
        self.cum_profits = cum_profits
        # print trade report
        print(2 * "\n" + 100* "-")
        msg1 = "{} | {}".format(time, going)
        print(msg1) 
        msg2 = "{} | Base_Units = {} | Quote_Units = {} | Price = {} ".format(time, base_units, quote_units, self.data.Close.iloc[-1])
        print(msg2)
        msg3 = "{} | Real profit = {} | Accumulate profit = {} ".format(time, real_profit, cum_profits)
        print(msg3)
        msg4 = ""
        if (self.emergency_price_chg_flag == True):
            msg4 = "price changed in 1s in pct: {}, which is more/less than the imposed pct: {} (imposed pct x2 if positive) ".format(round(self.pct_price_chg, 6), self.assigned_emergency_price_chg_pct) 
            print(msg4)
        print(100 * "-" + "\n")
        mail_msg = f"Subject: trade executed. Bot name: {self.bot_name}. \n\n {msg1} \n\n {msg2} \n\n {msg3} \n\n {msg4}"
        try:
            self.conn.sendmail('jpxcar6@gmail.com', 'jpxcar6@gmail.com', f"{mail_msg}")
        except smtplib.SMTPSenderRefused as e:
            print(e)
            self.login_mail()
            self.conn.sendmail('jpxcar6@gmail.com', 'jpxcar6@gmail.com', f"{mail_msg}")
    
    def prepare_recent_data(self):
        '''
        REMARK: Introduced time must be in Tokyo time (UTC+9) but the calculations will be in UTC
        Prepare all the fields of dat a necessary for the study. The interval of dates to be studied is the one
        given when delclaring the class. To prepare another interval of dates, please create another class instance.
        :param start: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-01-29-20:00"
        :type start: str.
        :param end: a string with the following format ""%Y-%m-%d-%H:%M" .i.e. "2022-02-29-20:00"
        :type end: str.
        :param interval: string among the followings: ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        :type interval: str.
        '''
        
        #Prepare pre-data to the present moment with non NaN for the trading period (macd paramters ready)
        current_time_obj = datetime.now()
        current_time = int(current_time_obj.timestamp()*1000)

#         from_time_obj = datetime.strptime(start, "%Y-%m-%d-%H:%M")
#       ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        ema_diff = self.ema_slow + self.ema_signal + 2
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
        from_time_obj = current_time_obj - td
        from_time = int((current_time_obj - td).timestamp()*1000)
        self.data = utils.get_history_v3(symbol=self.symbol, interval=self.interval, start=from_time, end=current_time, testnet=None)[0] #for historical data testnet is not used
        self.client = utils.get_history_v3(symbol=self.symbol, interval=self.interval, start=from_time, end=current_time, testnet=True)[1] # testnet is used to extract the client
        #obtaining MACD instance from python ta
        macd_diff = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd_diff()
        macd_macd = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd()
        macd_signal = ta.trend.MACD(close=self.data.Close, window_slow=self.ema_slow, window_fast=self.ema_fast, window_sign=self.ema_signal, fillna=False).macd_signal()
        #assigning the values of macd to ticker dataframe
        self.data['macd_diff'] = macd_diff
        self.data['macd_macd'] = macd_macd
        self.data['macd_signal'] = macd_signal
        #last candle retrieved from old data till the present moment will be incomplete 99.9% of the time
        self.data["Complete"] = [True for row in range(len(self.data)-1)] + [False]
        #decide position to be given to the latest recent data kandle (not completed in 99% of cases and that is 
        #going to be updated by the stream of data, so actually, position given to the latest kandle at this point
        #it is mots likely not to be used, but updated.
        self.stablish_positions()

    def stablish_positions(self):
        pass

    def open_orders(self):
        orders = self.client.get_open_orders(symbol=self.symbol)
        print(orders)
       
    def plot_results(self, start_plot=None, end_plot=None, width_bars=0.1):
        
        # from IPython.core.display import display, HTML
        # display(HTML("<style>.container { width:100% !important; }</style>"))
        colors=[]

        fig, (close_ax, macd_ax) = plt.subplots(nrows=2, ncols=1, figsize=(30,20), gridspec_kw={'height_ratios': [4,2]}, sharex=True)

        close_ax.grid(visible=True, which='major', axis='x', color='grey')
        macd_ax.grid(visible=True, which='major', axis='x', color='grey')
        close_ax.grid(visible=True, which='major', axis='y', color='grey')
        macd_ax.grid(visible=True, which='major', axis='y', color='grey')
        close_ax.grid(visible=True, which='minor', axis='x', color='grey')
        macd_ax.grid(visible=True, which='minor', axis='x', color='grey')

        close_ax.tick_params(labelrotation=45, labelsize = 'large')
        macd_ax.tick_params(labelrotation=45, labelsize = 'large')

        close_ax.margins(0)
        macd_ax.margins(0)
        
        close_ax.set_ylim(auto=True)
        
        data_ready = self.data.dropna(subset=['macd_diff', 'macd_macd', 'macd_signal']).copy()
        
        
        if (start_plot == None):
            start_plot = data_ready.index[0]
        if (end_plot == None):
            end_plot = data_ready.index[-1]  
            
        if ((start_plot != None) and (end_plot !=None)):
            cond_start = data_ready.index >= start_plot
            cond_end = data_ready.index <= end_plot
            data_ready = data_ready[cond_start&cond_end]
                
        for index, value in data_ready.macd_diff.iteritems():
            if value > 0:
                colors.append('g')
            else:
                colors.append('r')
                
        close_ax.plot(data_ready.index, data_ready.Close) #plot the data without shifting

        #shift one position the inv_sign only for plotting the signal in the day after is found, without shifting the
        #Close prices
        data_ready_shift = data_ready.copy()
        data_ready_shift['position'] = data_ready.position.shift(1)
        buy_pos = data_ready_shift.position == 1              
        buy_trade = data_ready_shift.loc[buy_pos]
        sell_pos = data_ready_shift.position == 0            
        sell_trade = data_ready_shift.loc[sell_pos]
        close_ax.scatter(sell_trade.index, sell_trade.Close.loc[sell_trade.index], marker='^', color='r', s=100)
        close_ax.scatter(buy_trade.index, buy_trade.Close.loc[buy_trade.index], marker='^', color='g', s=100)

        if ((self.data.Complete.iloc[-1] == False) and (self.data.position.iloc[-1] == 0)):
            close_ax.scatter(self.data.index[-1], self.data.Close.loc[self.data.index[-1]], marker='^', color='r', s=100)
        
        macd_ax.bar(x= data_ready.index, height= data_ready.macd_diff, width=width_bars, align='center', color=colors, edgecolor='black')
    
    def save_to_files(self):
        file_name = f"macd__symbol_{self.symbol}__interval_{self.interval}__eslow_{self.ema_slow}_efast_{self.ema_fast}_esign_{self.ema_signal}__duration_{self.run_end_delta}min_upto_{self.assigned_duration_minutes}min__profit_{self.cum_profits}dollar__tradesnum_{self.trades}" 
        outfile = open(file_name, 'wb')
        self.data.to_csv(outfile, index = True, header = True, sep = ',', encoding = 'utf-8', date_format ='%Y-%m-%d-%H:%M')
        outfile.close()
        results = {
            "units": self.units,
            "symbol": self.symbol,
            "interval": self.interval,
            "ema_slow": self.ema_slow,
            "ema_fast": self.ema_fast,
            "ema_signal": self.ema_signal,
            "testnet": self.testnet,
            "assigned_duration_minutes": self.assigned_duration_minutes,
            "assigned_emergency_price_chg_pct": self.assigned_emergency_price_chg_pct,
            "run_end_time_utc": self.run_end_time_utc.strftime("%Y-%m-%d-%H:%M:%S"),
            "run_end_delta": self.run_end_delta,
            "trades": self.trades,
            "trade_values": self.trade_values,
            "trade_values_time": self.trade_values_time,
            "trade_start_time_utc": self.trade_start_time_utc.strftime("%Y-%m-%d-%H:%M:%S"),
            "profit": self.cum_profits,
            "emergency_price_chg_flag": self.emergency_price_chg_flag,
            "emergency_msg": self.emergency_msg,
            "pct_price_chg": self.pct_price_chg,
            "bot_name": self.bot_name  
        }
        f = open(f"{file_name}.txt", "a")
        json.dump(results, f)
        f.close()
    
    def login_mail(self):
        self.conn = smtplib.SMTP('smtp.gmail.com', 587)   
        self.conn.ehlo()
        self.conn.starttls()
        self.conn.login('jpxcar6@gmail.com', 'iqdwckxxatmzbcom')
    
    def logout_mail(self):
        self.conn.quit()

