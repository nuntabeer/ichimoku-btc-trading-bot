"""
Configuration & Settings for Ichimoku Trading Bot
"""

# Account Settings
INITIAL_ACCOUNT_SIZE = 10000  # USDT
RISK_PER_TRADE = 0.02  # 2%

# Strategy Settings
TIMEFRAME = '1m'  # 1 minute
SYMBOL = 'BTC/USDT'

# Ichimoku Settings
ICHIMOKU_TENKAN = 9
ICHIMOKU_KIJUN = 26
ICHIMOKU_SENKOU_B = 52
ICHIMOKU_DISPLACEMENT = 26

# EMA Settings
EMA_PERIOD = 20

# Backtesting Settings
BACKTEST_DAYS = 30

# TP/SL Settings
TP_MULTIPLIER = 3  # TP = 3 * SL
