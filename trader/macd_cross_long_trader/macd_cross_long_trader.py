#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
sys.path.append('/Users/jp/Desktop/Investment/trading_BOT/trader/macd_trader')
from macd_trader import Macd_trader


# In[ ]:


class Macd_cross_long_trader(Macd_trader):
    
    """Class to perform live testing using Binance testnet stream of data
    """
    def __init__(self, symbol=None, units='0.0006', interval=None, ema_slow=None, ema_fast=None, ema_signal=None, testnet=None, assigned_duration_minutes=None, emergency_price_chg_pct=None):
        super().__init__(symbol, units, interval, ema_slow, ema_fast, ema_signal, testnet, assigned_duration_minutes, emergency_price_chg_pct)

    def stablish_positions(self):
        
        ht_previous = self.data.macd_diff.iloc[-2]# this is the kandle before the latest (complete in recent data)
        ht_last = self.data.macd_diff.iloc[-1] #this is the last (incomplete 99% cases)
        
        #stablish neutral conditions
        if ((ht_previous > 0) and (ht_last < 0)):
            self.position = 0 #position adopted in the latest kandle that is incomplete 99% cases
        #stablish buy conditions
        elif ((ht_previous < 0) and (ht_last > 0)):
            self.position = 1 #position adopted in the latest kandle that is incomplete 99% cases
        else:  
            self.position = 'np' #in any other case do nothing and continue
        
        li = self.data.index == self.data.index[-1]
        self.data.loc[li, 'position'] = self.position
        
    def prepare_recent_data(self):
        super().prepare_recent_data()
        self.stablish_positions()

