"""
Backtesting Engine for Ichimoku Strategy

Features:
- Load historical OHLC data
- Calculate all indicators
- Generate entry/exit signals
- Calculate P&L and statistics
- Generate backtest report
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategy.ichimoku_strategy import IchimokuStrategy
from risk_management.position_sizer import RiskManager


class Backtester:
    def __init__(self, 
                 initial_account_size=10000,
                 risk_per_trade=0.02,
                 strategy_params=None):
        """
        Initialize Backtester
        
        Args:
            initial_account_size: Initial account size in USDT
            risk_per_trade: Risk percentage per trade
            strategy_params: Strategy parameters dictionary
        """
        self.initial_account_size = initial_account_size
        self.strategy = IchimokuStrategy(ichimoku_params=strategy_params)
        self.risk_manager = RiskManager(initial_account_size, risk_per_trade)
        self.results = None
    
    def load_data(self, df):
        """
        Load and prepare data for backtesting
        
        Args:
            df: DataFrame with OHLC data (must have columns: open, high, low, close)
            
        Returns:
            DataFrame with indicators calculated
        """
        # Reset risk manager for new backtest
        self.risk_manager = RiskManager(self.initial_account_size, self.risk_manager.risk_per_trade)
        
        # Sort by timestamp
        df = df.sort_index().reset_index(drop=True)
        
        # Calculate indicators
        df = self.strategy.calculate_indicators(df)
        
        # Add signal columns
        df['buy_signal'] = df.apply(self.strategy.get_buy_signal, axis=1)
        df['sell_signal'] = df.apply(self.strategy.get_sell_signal, axis=1)
        
        return df
    
    def run(self, df):
        """
        Run backtest on the data
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with trade signals and results
        """
        # Load and prepare data
        df = self.load_data(df.copy())
        
        # Initialize columns for tracking
        df['position'] = 0  # 1 for long, -1 for short, 0 for flat
        df['trade_entry'] = 0
        df['trade_exit'] = 0
        df['entry_price'] = np.nan
        df['exit_price'] = np.nan
        df['pnl'] = np.nan
        
        # Process each candle
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Check if we have an open position
            if self.risk_manager.open_position is not None:
                pos = self.risk_manager.open_position
                
                # Check for exit conditions
                if pos.side == 'BUY':
                    # Exit on SL (low touches SL)
                    if row['low'] <= pos.sl_price:
                        exit_price = pos.sl_price
                        exit_reason = 'SL'
                    # Exit on TP (high touches TP)
                    elif row['high'] >= pos.tp_price:
                        exit_price = pos.tp_price
                        exit_reason = 'TP'
                    else:
                        exit_price = None
                        exit_reason = None
                else:  # SELL
                    # Exit on SL (high touches SL)
                    if row['high'] >= pos.sl_price:
                        exit_price = pos.sl_price
                        exit_reason = 'SL'
                    # Exit on TP (low touches TP)
                    elif row['low'] <= pos.tp_price:
                        exit_price = pos.tp_price
                        exit_reason = 'TP'
                    else:
                        exit_price = None
                        exit_reason = None
                
                # Close position if exit condition met
                if exit_price is not None:
                    trade_result = self.risk_manager.close_position(i, exit_price, exit_reason)
                    df.at[i, 'trade_exit'] = 1
                    df.at[i, 'exit_price'] = exit_price
                    df.at[i, 'pnl'] = trade_result['pnl']
                    df.at[i, 'position'] = 0
            
            # Check for entry signals only if no open position
            if self.risk_manager.open_position is None:
                if row['buy_signal']:
                    # Get entry levels
                    levels = self.strategy.get_entry_levels(row, 'BUY')
                    
                    # Open position
                    try:
                        pos = self.risk_manager.open_new_position(
                            i,
                            levels['entry_price'],
                            levels['sl_price'],
                            levels['tp_price'],
                            'BUY'
                        )
                        if pos is not None:
                            df.at[i, 'trade_entry'] = 1
                            df.at[i, 'entry_price'] = levels['entry_price']
                            df.at[i, 'position'] = 1
                    except Exception as e:
                        print(f"Error opening BUY position at index {i}: {e}")
                
                elif row['sell_signal']:
                    # Get entry levels
                    levels = self.strategy.get_entry_levels(row, 'SELL')
                    
                    # Open position
                    try:
                        pos = self.risk_manager.open_new_position(
                            i,
                            levels['entry_price'],
                            levels['sl_price'],
                            levels['tp_price'],
                            'SELL'
                        )
                        if pos is not None:
                            df.at[i, 'trade_entry'] = 1
                            df.at[i, 'entry_price'] = levels['entry_price']
                            df.at[i, 'position'] = -1
                    except Exception as e:
                        print(f"Error opening SELL position at index {i}: {e}")
        
        # Close any remaining open position at last candle
        if self.risk_manager.open_position is not None:
            pos = self.risk_manager.open_position
            last_close = df.iloc[-1]['close']
            trade_result = self.risk_manager.close_position(len(df) - 1, last_close, 'END_OF_DATA')
            df.at[len(df) - 1, 'trade_exit'] = 1
            df.at[len(df) - 1, 'exit_price'] = last_close
            df.at[len(df) - 1, 'pnl'] = trade_result['pnl']
        
        self.results = df
        return df
    
    def get_trades(self):
        """
        Get list of all completed trades
        
        Returns:
            List of trade dictionaries
        """
        return self.risk_manager.trade_history
    
    def get_stats(self):
        """
        Get backtest statistics
        
        Returns:
            Dictionary with account statistics
        """
        return self.risk_manager.get_account_stats()
    
    def print_report(self):
        """
        Print backtest report
        """
        stats = self.get_stats()
        trades = self.get_trades()
        
        print("\n" + "="*80)
        print("ICHIMOKU TRADING BOT - BACKTEST REPORT")
        print("="*80)
        
        print("\n[ACCOUNT STATISTICS]")
        print(f"Initial Account Size: ${stats.get('current_account_size') - stats.get('total_pnl', 0):,.2f}")
        print(f"Final Account Size: ${stats['current_account_size']:,.2f}")
        print(f"Total P&L: ${stats['total_pnl']:,.2f}")
        print(f"P&L %: {stats['total_pnl_percent']:.2f}%")
        print(f"Max Drawdown: ${stats['max_drawdown']:,.2f}")
        
        print("\n[TRADE STATISTICS]")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Winning Trades: {stats['winning_trades']}")
        print(f"Losing Trades: {stats['losing_trades']}")
        print(f"Win Rate: {stats['win_rate']:.2f}%")
        print(f"Profit Factor: {stats['profit_factor']:.2f}")
        
        print("\n[TRADES DETAIL]")
        print("-" * 120)
        print(f"{'#':<4} {'Type':<6} {'Entry':<12} {'Exit':<12} {'SL':<12} {'TP':<12} {'Size':<10} {'P&L':<12} {'P&L%':<8} {'Exit Reason':<12}")
        print("-" * 120)
        
        for i, trade in enumerate(trades, 1):
            print(f"{i:<4} {trade['side']:<6} ${trade['entry_price']:<11.2f} ${trade['exit_price']:<11.2f} ${trade['sl_price']:<11.2f} ${trade['tp_price']:<11.2f} {trade['position_size']:<10.4f} ${trade['pnl']:<11.2f} {trade['pnl_percent']:<7.2f}% {trade['exit_reason']:<12}")
        
        print("-" * 120)
        print("\n")
