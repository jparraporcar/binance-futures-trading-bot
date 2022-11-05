#!/usr/bin/env python
# coding: utf-8

# In[34]:


import sys
sys.path.append('/Users/jp/Desktop/Investment/trading_BOT/trader/macd_trader')
from macd_trader import Macd_trader


# In[35]:


class Macd_peak_long_trader(Macd_trader):
    
    """Class to perform live testing using Binance testnet stream of data
    """
    def __init__(self, symbol=None, units='0.0006', interval=None, ema_slow=None, ema_fast=None, ema_signal=None, testnet=None, assigned_duration_minutes=None, emergency_price_chg_pct=None):
        super().__init__(symbol, units, interval, ema_slow, ema_fast, ema_signal, testnet, assigned_duration_minutes, emergency_price_chg_pct)
        
        self.positive_peak_found = False
        self.negative_peak_found = False

    def stablish_positions(self):
        #stablish neutral conditions
        cond1 = self.data.macd_diff.iloc[-3] > 0
        cond2 = self.data.macd_diff.iloc[-2] > 0
        cond3 = self.data.macd_diff.iloc[-1] > 0
        cond4 = self.data.macd_diff.iloc[-2] > self.data.macd_diff.iloc[-1]
        cond5 = self.data.macd_diff.iloc[-2] > self.data.macd_diff.iloc[-3]
        cond_all_neutral = cond1&cond2&cond3&cond4&cond5
        
        #stablish buy conditions
        cond6 = self.data.macd_diff.iloc[-3] < 0
        cond7 = self.data.macd_diff.iloc[-2] < 0
        cond8 = self.data.macd_diff.iloc[-1] < 0
        cond9 = self.data.macd_diff.iloc[-2] < self.data.macd_diff.iloc[-1]
        cond10 = self.data.macd_diff.iloc[-2] < self.data.macd_diff.iloc[-3]
        cond_all_buy = cond6&cond7&cond8&cond9&cond10        
        
        if ((cond_all_neutral == True) and (self.positive_peak_found == False)):
            self.position = 0 #position adopted in the latest kandle that is incomplete 99% cases
            self.negative_peak_found = False
            self.positive_peak_found = True
        elif ((cond_all_buy == True) and (self.negative_peak_found == False)):
            self.position = 1 #position adopted in the latest kandle that is incomplete 99% cases
            self.positive_peak_found = False
            self.negative_peak_found = True
        else:  
            self.position = 'np' #in any other case do nothing and continue
            
        li = self.data.index == self.data.index[-1]
        self.data.loc[li, 'position'] = self.position
        
    def prepare_recent_data(self):
        super().prepare_recent_data()
        self.stablish_positions()

