"""
Ichimoku Candle 002 Trading Strategy (Buy & Sell)

Entry Conditions:
- BUY: EMA 20 close > Kumo Cloud upper line AND lower line
- SELL: EMA 20 close < Kumo Cloud upper line AND lower line

Exit Conditions:
- BUY: SL at Kumo Cloud lower line, TP = 3 * SL
- SELL: SL at Kumo Cloud upper line, TP = 3 * SL

Risk Management:
- Risk per trade: 2%
- No duplicate positions
"""

import pandas as pd
import numpy as np
from indicators.ichimoku import Ichimoku
from indicators.ema import EMA


class IchimokuStrategy:
    def __init__(self, 
                 ichimoku_params=None,
                 ema_period=20,
                 tp_multiplier=3):
        """
        Initialize Ichimoku Strategy
        
        Args:
            ichimoku_params: Dictionary with Ichimoku parameters
            ema_period: EMA period (default 20)
            tp_multiplier: Take profit multiplier (default 3)
        """
        if ichimoku_params is None:
            ichimoku_params = {
                'tenkan_period': 9,
                'kijun_period': 26,
                'senkou_b_period': 52,
                'displacement': 26
            }
        
        self.ichimoku = Ichimoku(**ichimoku_params)
        self.ema = EMA(period=ema_period)
        self.tp_multiplier = tp_multiplier
    
    def calculate_indicators(self, df):
        """
        Calculate all indicators
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with all indicators
        """
        # Calculate Ichimoku
        df = self.ichimoku.calculate(df)
        
        # Calculate EMA
        df = self.ema.calculate(df)
        
        return df
    
    def get_buy_signal(self, row):
        """
        Check for BUY signal
        
        Condition: EMA 20 close > Kumo Cloud upper AND lower lines
        
        Args:
            row: DataFrame row with indicators
            
        Returns:
            True if BUY signal, False otherwise
        """
        try:
            ema = row['ema']
            kumo_upper = row['kumo_upper']
            kumo_lower = row['kumo_lower']
            close = row['close']
            
            # Check if all values are valid (not NaN)
            if pd.isna(ema) or pd.isna(kumo_upper) or pd.isna(kumo_lower):
                return False
            
            # BUY: EMA close > both Kumo upper and lower lines
            return close > ema and close > kumo_upper and close > kumo_lower
        except:
            return False
    
    def get_sell_signal(self, row):
        """
        Check for SELL signal
        
        Condition: EMA 20 close < Kumo Cloud upper AND lower lines
        
        Args:
            row: DataFrame row with indicators
            
        Returns:
            True if SELL signal, False otherwise
        """
        try:
            ema = row['ema']
            kumo_upper = row['kumo_upper']
            kumo_lower = row['kumo_lower']
            close = row['close']
            
            # Check if all values are valid (not NaN)
            if pd.isna(ema) or pd.isna(kumo_upper) or pd.isna(kumo_lower):
                return False
            
            # SELL: EMA close < both Kumo upper and lower lines
            return close < ema and close < kumo_upper and close < kumo_lower
        except:
            return False
    
    def get_entry_levels(self, row, side):
        """
        Get entry levels for a trade
        
        Args:
            row: DataFrame row with indicators
            side: 'BUY' or 'SELL'
            
        Returns:
            Dictionary with entry_price, sl_price, tp_price
        """
        entry_price = row['close']
        
        if side == 'BUY':
            # SL at Kumo lower line
            sl_price = row['kumo_lower']
            # TP = 3 * SL distance
            sl_distance = entry_price - sl_price
            tp_price = entry_price + (sl_distance * self.tp_multiplier)
        else:  # SELL
            # SL at Kumo upper line
            sl_price = row['kumo_upper']
            # TP = 3 * SL distance
            sl_distance = sl_price - entry_price
            tp_price = entry_price - (sl_distance * self.tp_multiplier)
        
        return {
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price
        }
