"""
Main entry point for Ichimoku Trading Bot

Usage:
    python main.py --backtest --days 30
"""

import argparse
import pandas as pd
from datetime import datetime
from backtester.backtest import Backtester
from data_fetcher import DataFetcher
import config


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Ichimoku Trading Bot')
    parser.add_argument('--backtest', action='store_true', help='Run backtest')
    parser.add_argument('--days', type=int, default=30, help='Number of days for backtest')
    parser.add_argument('--data-source', type=str, default='binance', help='Data source (binance, okx, sample)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("ICHIMOKU TRADING BOT - BACKTESTER")
    print("="*80)
    print(f"\nStarting backtest on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Fetch data
    print(f"\nFetching {args.days} days of {args.data_source.upper()} data...")
    
    if args.data_source.lower() == 'binance':
        df = DataFetcher.fetch_binance(
            symbol='BTC/USDT',
            timeframe=config.TIMEFRAME,
            days=args.days
        )
    elif args.data_source.lower() == 'okx':
        df = DataFetcher.fetch_okx(
            symbol='BTC-USDT',
            timeframe=config.TIMEFRAME,
            days=args.days
        )
    else:  # sample
        df = DataFetcher.generate_sample_data(
            days=args.days,
            timeframe=config.TIMEFRAME
        )
    
    if df is None or df.empty:
        print("ERROR: Could not fetch data. Using sample data instead...")
        df = DataFetcher.generate_sample_data(days=args.days)
    
    print(f"✓ Loaded {len(df)} candles")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    
    # Initialize backtester
    print("\nInitializing backtester...")
    backtester = Backtester(
        initial_account_size=config.INITIAL_ACCOUNT_SIZE,
        risk_per_trade=config.RISK_PER_TRADE
    )
    
    # Run backtest
    print("Running backtest...")
    results_df = backtester.run(df)
    print("✓ Backtest completed")
    
    # Print report
    backtester.print_report()
    
    # Save results to CSV
    results_df.to_csv('backtest_results.csv')
    print("\n✓ Results saved to backtest_results.csv")
    
    # Get trades
    trades = backtester.get_trades()
    if trades:
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv('backtest_trades.csv', index=False)
        print("✓ Trades saved to backtest_trades.csv")


if __name__ == '__main__':
    main()
