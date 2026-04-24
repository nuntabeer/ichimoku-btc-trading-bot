"""
Ichimoku Cloud Indicator

Components:
- Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
- Kijun-sen (Base Line): (26-period high + 26-period low) / 2
- Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, plotted 26 periods ahead
- Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
- Chikou Span (Lagging Span): Close price plotted 26 periods back

Kumo Cloud = area between Senkou Span A and B
"""

import pandas as pd
import numpy as np


class Ichimoku:
    def __init__(self, 
                 tenkan_period=9,
                 kijun_period=26,
                 senkou_b_period=52,
                 displacement=26):
        """
        Initialize Ichimoku indicator
        
        Args:
            tenkan_period: Period for Tenkan-sen (default 9)
            kijun_period: Period for Kijun-sen (default 26)
            senkou_b_period: Period for Senkou Span B (default 52)
            displacement: Displacement for Senkou Span (default 26)
        """
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement
    
    def calculate(self, df):
        """
        Calculate Ichimoku Cloud components
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with Ichimoku components
        """
        # Make a copy to avoid modifying original data
        df = df.copy()
        
        # Calculate Tenkan-sen (Conversion Line)
        tenkan_high = df['high'].rolling(window=self.tenkan_period).max()
        tenkan_low = df['low'].rolling(window=self.tenkan_period).min()
        df['tenkan_sen'] = (tenkan_high + tenkan_low) / 2
        
        # Calculate Kijun-sen (Base Line)
        kijun_high = df['high'].rolling(window=self.kijun_period).max()
        kijun_low = df['low'].rolling(window=self.kijun_period).min()
        df['kijun_sen'] = (kijun_high + kijun_low) / 2
        
        # Calculate Senkou Span A (Leading Span A)
        senkou_a = (df['tenkan_sen'] + df['kijun_sen']) / 2
        df['senkou_span_a'] = senkou_a.shift(self.displacement)
        
        # Calculate Senkou Span B (Leading Span B)
        senkou_b_high = df['high'].rolling(window=self.senkou_b_period).max()
        senkou_b_low = df['low'].rolling(window=self.senkou_b_period).min()
        senkou_b = (senkou_b_high + senkou_b_low) / 2
        df['senkou_span_b'] = senkou_b.shift(self.displacement)
        
        # Calculate Chikou Span (Lagging Span)
        df['chikou_span'] = df['close'].shift(-self.displacement)
        
        # Kumo Cloud Upper and Lower lines (current)
        df['kumo_upper'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
        df['kumo_lower'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)
        
        return df
    
    @staticmethod
    def is_price_above_cloud(close, kumo_upper, kumo_lower):
        """
        Check if price is above the Kumo cloud
        
        Args:
            close: Close price
            kumo_upper: Kumo upper line
            kumo_lower: Kumo lower line
            
        Returns:
            True if price is above cloud, False otherwise
        """
        if pd.isna(kumo_upper) or pd.isna(kumo_lower) or pd.isna(close):
            return False
        return close > kumo_upper and close > kumo_lower
    
    @staticmethod
    def is_price_below_cloud(close, kumo_upper, kumo_lower):
        """
        Check if price is below the Kumo cloud
        
        Args:
            close: Close price
            kumo_upper: Kumo upper line
            kumo_lower: Kumo lower line
            
        Returns:
            True if price is below cloud, False otherwise
        """
        if pd.isna(kumo_upper) or pd.isna(kumo_lower) or pd.isna(close):
            return False
        return close < kumo_upper and close < kumo_lower
