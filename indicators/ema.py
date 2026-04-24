"""
Exponential Moving Average (EMA) Indicator

EMA = (Close - EMA(previous)) * multiplier + EMA(previous)
where multiplier = 2 / (N + 1)
"""

import pandas as pd


class EMA:
    def __init__(self, period=20):
        """
        Initialize EMA indicator
        
        Args:
            period: EMA period (default 20)
        """
        self.period = period
    
    def calculate(self, df):
        """
        Calculate EMA for given DataFrame
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with EMA column added
        """
        df = df.copy()
        df['ema'] = df['close'].ewm(span=self.period, adjust=False).mean()
        return df
    
    @staticmethod
    def get_ema_value(close_prices, period):
        """
        Calculate EMA for a series of prices
        
        Args:
            close_prices: Series of close prices
            period: EMA period
            
        Returns:
            Series with EMA values
        """
        return close_prices.ewm(span=period, adjust=False).mean()
