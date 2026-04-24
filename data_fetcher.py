"""
Data fetcher for downloading historical OHLC data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import requests


class DataFetcher:
    """Fetch historical OHLC data from various sources"""
    
    @staticmethod
    def fetch_binance(symbol='BTC/USDT', timeframe='1m', days=30):
        """
        Fetch data from Binance
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1m', '5m', '1h')
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            exchange = ccxt.binance()
            
            # Timeframe to milliseconds
            timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
            
            # Calculate start time
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            all_candles = []
            
            # Fetch data in batches (Binance limit is 1000 per request)
            while since < int(datetime.now().timestamp() * 1000):
                candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                since = candles[-1][0] + timeframe_ms
            
            # Create DataFrame
            df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        
        except Exception as e:
            print(f"Error fetching data from Binance: {e}")
            return None
    
    @staticmethod
    def fetch_okx(symbol='BTC-USDT', timeframe='1m', days=30):
        """
        Fetch data from OKX
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            timeframe: Candle timeframe (e.g., '1m', '5m', '1h')
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            # OKX API endpoint
            url = "https://www.okx.com/api/v5/market/candles"
            
            # Convert timeframe
            bar_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '1h': '1H',
                '4h': '4H',
                '1d': '1D'
            }
            bar = bar_map.get(timeframe, '1m')
            
            # Timeframe to seconds
            timeframe_sec = {
                '1m': 60,
                '5m': 300,
                '15m': 900,
                '1h': 3600,
                '4h': 14400,
                '1d': 86400
            }.get(timeframe, 60)
            
            # Calculate start time
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            all_candles = []
            before = None
            
            # Fetch data in batches
            for _ in range(days * 24 * 60 // 100):  # Approximate number of batches
                params = {
                    'instId': symbol,
                    'bar': bar,
                    'limit': 100
                }
                
                if before:
                    params['before'] = before
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if data['code'] != '0' or not data['data']:
                    break
                
                candles = data['data']
                all_candles.extend(candles)
                before = candles[-1][0]  # Use last candle's timestamp as before
                
                if len(all_candles) >= days * 24 * 60:
                    break
            
            # Convert to DataFrame
            if all_candles:
                all_candles.reverse()  # Reverse to get chronological order
                df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vol_ccy', 'vol_ccy_quote', 'confirm'])
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Convert string values to float
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                return df
            
            return None
        
        except Exception as e:
            print(f"Error fetching data from OKX: {e}")
            return None
    
    @staticmethod
    def generate_sample_data(days=30, timeframe='1m'):
        """
        Generate sample OHLC data for testing
        
        Args:
            days: Number of days of data to generate
            timeframe: Candle timeframe
            
        Returns:
            DataFrame with OHLC data
        """
        # Generate timestamps
        minutes = days * 24 * 60
        timestamps = pd.date_range(end=datetime.now(), periods=minutes, freq='1min')
        
        # Generate random price data
        np.random.seed(42)
        base_price = 45000
        prices = []
        
        for i in range(minutes):
            # Random walk
            change = np.random.normal(0, 50)
            base_price += change
            prices.append(max(base_price, 1000))  # Ensure positive price
        
        # Create OHLC data
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p + np.random.uniform(0, 100) for p in prices],
            'low': [max(p - np.random.uniform(0, 100), 1000) for p in prices],
            'close': [p + np.random.uniform(-50, 50) for p in prices],
            'volume': np.random.uniform(10, 1000, minutes)
        })
        
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        df.set_index('timestamp', inplace=True)
        
        return df
