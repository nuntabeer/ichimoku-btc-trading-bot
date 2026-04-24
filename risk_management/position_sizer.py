"""
Position Sizing & Risk Management

Rules:
- Risk per trade: 2%
- No duplicate positions
- Position size based on risk amount
"""

from dataclasses import dataclass
import pandas as pd


@dataclass
class Position:
    """Position details"""
    entry_index: int
    entry_price: float
    sl_price: float
    tp_price: float
    position_size: float
    side: str  # 'BUY' or 'SELL'
    risk_amount: float
    potential_reward: float


class RiskManager:
    """
    Risk Management & Position Sizing
    
    Rules:
    - Risk per trade: 2%
    - No duplicate positions
    - Position size based on risk amount
    """
    
    def __init__(self, account_size: float, risk_per_trade: float = 0.02):
        """
        Initialize Risk Manager
        
        Args:
            account_size: Total account size in USDT
            risk_per_trade: Risk percentage per trade (0.02 = 2%)
        """
        self.initial_account_size = account_size
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
        self.open_position = None
        self.trade_history = []
    
    def calculate_position_size(self, 
                                entry_price: float, 
                                sl_price: float, 
                                side: str) -> float:
        """
        Calculate position size based on 2% risk rule
        
        Formula:
        Risk Amount = Account Size * Risk Percentage
        Risk in Price = |Entry - SL|
        Position Size = Risk Amount / Risk in Price
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            side: 'BUY' or 'SELL'
            
        Returns:
            Position size in contract (quantity)
        """
        # Calculate risk amount in USDT
        risk_amount = self.account_size * self.risk_per_trade
        
        # Calculate risk in price
        price_risk = abs(entry_price - sl_price)
        
        if price_risk <= 0:
            return 0
        
        # Position size = risk amount / price risk
        position_size = risk_amount / price_risk
        
        return round(position_size, 4)
    
    def can_open_position(self) -> bool:
        """
        Check if we can open a new position
        
        Rules:
        - No duplicate positions (max 1 open position)
        
        Returns:
            True if we can open position, False otherwise
        """
        return self.open_position is None
    
    def open_new_position(self, 
                          index: int,
                          entry_price: float, 
                          sl_price: float, 
                          tp_price: float, 
                          side: str) -> Position:
        """
        Open a new position
        
        Args:
            index: Candle index
            entry_price: Entry price
            sl_price: Stop loss price
            tp_price: Take profit price
            side: 'BUY' or 'SELL'
            
        Returns:
            Position object
        """
        if not self.can_open_position():
            raise Exception("Cannot open position - one already open")
        
        position_size = self.calculate_position_size(entry_price, sl_price, side)
        
        if position_size <= 0:
            return None
        
        if side == 'BUY':
            risk_amount = (entry_price - sl_price) * position_size
            reward_amount = (tp_price - entry_price) * position_size
        else:  # SELL
            risk_amount = (sl_price - entry_price) * position_size
            reward_amount = (entry_price - tp_price) * position_size
        
        position = Position(
            entry_index=index,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            position_size=position_size,
            side=side,
            risk_amount=risk_amount,
            potential_reward=reward_amount
        )
        
        self.open_position = position
        return position
    
    def close_position(self, exit_index: int, exit_price: float, exit_reason: str = 'MANUAL') -> dict:
        """
        Close the current position
        
        Args:
            exit_index: Candle index at exit
            exit_price: Price at which position is closed
            exit_reason: Reason for closing (TP, SL, MANUAL)
            
        Returns:
            Dictionary with P&L information
        """
        if self.open_position is None:
            raise Exception("No open position to close")
        
        pos = self.open_position
        
        if pos.side == 'BUY':
            pnl = (exit_price - pos.entry_price) * pos.position_size
            pnl_percent = ((exit_price - pos.entry_price) / pos.entry_price) * 100
        else:  # SELL
            pnl = (pos.entry_price - exit_price) * pos.position_size
            pnl_percent = ((pos.entry_price - exit_price) / pos.entry_price) * 100
        
        # Update account size
        self.account_size += pnl
        
        trade_result = {
            'entry_index': pos.entry_index,
            'exit_index': exit_index,
            'side': pos.side,
            'entry_price': round(pos.entry_price, 2),
            'exit_price': round(exit_price, 2),
            'sl_price': round(pos.sl_price, 2),
            'tp_price': round(pos.tp_price, 2),
            'position_size': round(pos.position_size, 4),
            'pnl': round(pnl, 2),
            'pnl_percent': round(pnl_percent, 2),
            'risk_amount': round(pos.risk_amount, 2),
            'potential_reward': round(pos.potential_reward, 2),
            'exit_reason': exit_reason,
            'account_size_after': round(self.account_size, 2)
        }
        
        self.trade_history.append(trade_result)
        self.open_position = None
        
        return trade_result
    
    def get_account_stats(self) -> dict:
        """
        Get account statistics
        
        Returns:
            Dictionary with account stats
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'current_account_size': self.account_size,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        total_pnl_percent = (total_pnl / self.initial_account_size) * 100
        
        # Calculate profit factor
        gross_profit = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calculate max drawdown
        cumulative_pnl = []
        running_total = 0
        for trade in self.trade_history:
            running_total += trade['pnl']
            cumulative_pnl.append(running_total)
        
        max_drawdown = 0
        peak = 0
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = peak - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2),
            'current_account_size': round(self.account_size, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2)
        }
