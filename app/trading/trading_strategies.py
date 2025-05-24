"""
Trading strategy foundation module - base classes and utilities
for cryptocurrency trading strategies
"""
import logging
import pandas as pd
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
from app.trading.model_signals import ModelSignalManager, TradingSignal, SignalType

logger = logging.getLogger(__name__)

class Action(Enum):
    """Possible trading actions"""
    HOLD = "HOLD"
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class TradePosition:
    """Represents an open trading position"""
    entry_price: float
    entry_time: pd.Timestamp
    amount: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class Strategy:
    """Base strategy class that all trading strategies should inherit from"""
    
    def __init__(self, name: str, initial_balance: float = 10000.0, fee_rate: float = 0.001, 
                 stop_loss: float = None, take_profit: float = None):
        """
        Initialize the strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            fee_rate: Trading fee as a decimal (e.g., 0.001 = 0.1%)
            stop_loss: Stop loss level as a decimal (e.g., 0.05 = 5%)
            take_profit: Take profit level as a decimal (e.g., 0.1 = 10%)
        """
        self.name = name
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.fee_rate = fee_rate
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
        self.position = None  # Current position
        self.positions_history = []  # History of positions
        self.trades = []  # History of trades
        
        # Performance metrics
        self.portfolio_value = initial_balance
        self.portfolio_values = []  # Track portfolio value over time
    
    def reset(self):
        """Reset the strategy to initial state"""
        self.balance = self.initial_balance
        self.position = None
        self.positions_history = []
        self.trades = []
        self.portfolio_value = self.initial_balance
        self.portfolio_values = []
        
    def calculate_position_value(self, current_price: float) -> float:
        """Calculate the value of the current position"""
        if not self.position:
            return 0.0
        return self.position.amount * current_price
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate total portfolio value (balance + position value)"""
        position_value = self.calculate_position_value(current_price)
        return self.balance + position_value
        
    def update_portfolio_value(self, current_price: float):
        """Update the portfolio value based on current price"""
        self.portfolio_value = self.calculate_portfolio_value(current_price)
        self.portfolio_values.append(self.portfolio_value)
    
    def execute_buy(self, timestamp, price: float, amount: float = None) -> bool:
        """
        Execute a buy order
        
        Args:
            timestamp: Time of the trade
            price: Current price
            amount: Amount to buy (in BTC) or None to use all available balance
            
        Returns:
            bool: True if trade was successful, False otherwise
        """
        # Don't buy if already in a position
        if self.position:
            return False
        
        # Calculate the amount to buy if not specified
        if amount is None:
            # Use all available balance accounting for fees
            amount = self.balance * (1 - self.fee_rate) / price
        
        # Calculate cost including fees
        cost = amount * price
        fee = cost * self.fee_rate
        total_cost = cost + fee
        
        # Check if we have enough balance
        if self.balance < total_cost:
            logger.warning(f"Not enough balance to buy. Required: {total_cost}, Available: {self.balance}")
            return False
        
        # Execute the trade
        self.balance -= total_cost
        
        # Create a position
        self.position = TradePosition(
            entry_price=price,
            entry_time=timestamp,
            amount=amount,
            stop_loss=price * (1 - self.stop_loss) if self.stop_loss else None,
            take_profit=price * (1 + self.take_profit) if self.take_profit else None
        )
        
        # Record the trade
        trade = {
            'timestamp': timestamp,
            'action': 'BUY',
            'price': price,
            'amount': amount,
            'fees': fee,
            'balance': self.balance,
            'profit': 0.0  # No profit on buy
        }
        self.trades.append(trade)
        logger.info(f"BUY: {amount} BTC at ${price} with fee ${fee}")
        
        return True
    
    def execute_sell(self, timestamp, price: float) -> bool:
        """
        Execute a sell order for the entire position
        
        Args:
            timestamp: Time of the trade
            price: Current price
            
        Returns:
            bool: True if trade was successful, False otherwise
        """
        # Must have a position to sell
        if not self.position:
            return False
        
        # Calculate value and fee
        amount = self.position.amount
        value = amount * price
        fee = value * self.fee_rate
        profit = value - (self.position.entry_price * amount) - fee
        
        # Execute the trade
        self.balance += value - fee
        
        # Store position history
        self.positions_history.append({
            'entry_time': self.position.entry_time,
            'exit_time': timestamp,
            'entry_price': self.position.entry_price,
            'exit_price': price,
            'amount': amount,
            'profit': profit,
            'profit_pct': profit / (self.position.entry_price * amount) * 100
        })
        
        # Record the trade
        trade = {
            'timestamp': timestamp,
            'action': 'SELL',
            'price': price,
            'amount': amount,
            'fees': fee,
            'balance': self.balance,
            'profit': profit
        }
        self.trades.append(trade)
        
        # Clear position
        self.position = None
        
        logger.info(f"SELL: {amount} BTC at ${price} with profit ${profit:.2f}")
        return True
    
    def check_stop_loss(self, current_price: float, timestamp) -> bool:
        """
        Check if stop loss has been triggered
        
        Args:
            current_price: Current price
            timestamp: Current timestamp
            
        Returns:
            bool: True if stop loss was triggered and executed, False otherwise
        """
        if not self.position or not self.position.stop_loss:
            return False
            
        if current_price <= self.position.stop_loss:
            logger.info(f"Stop loss triggered at ${current_price}")
            return self.execute_sell(timestamp, current_price)
            
        return False
    
    def check_take_profit(self, current_price: float, timestamp) -> bool:
        """
        Check if take profit has been triggered
        
        Args:
            current_price: Current price
            timestamp: Current timestamp
            
        Returns:
            bool: True if take profit was triggered and executed, False otherwise
        """
        if not self.position or not self.position.take_profit:
            return False
            
        if current_price >= self.position.take_profit:
            logger.info(f"Take profit triggered at ${current_price}")
            return self.execute_sell(timestamp, current_price)
            
        return False
        
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on the strategy
        Must be implemented by subclasses
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        raise NotImplementedError("Subclass must implement abstract method")
        
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        Must be implemented by subclasses
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        raise NotImplementedError("Subclass must implement abstract method")
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate and return performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.positions_history:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_profit': 0.0,
                'max_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Calculate metrics
        total_trades = len(self.positions_history)
        winning_trades = sum(1 for pos in self.positions_history if pos['profit'] > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(pos['profit'] for pos in self.positions_history)
        profit_factor = 0.0
        
        # Profit factor
        total_gains = sum(pos['profit'] for pos in self.positions_history if pos['profit'] > 0)
        total_losses = sum(abs(pos['profit']) for pos in self.positions_history if pos['profit'] < 0)
        if total_losses > 0:
            profit_factor = total_gains / total_losses
        
        # Calculate drawdown
        if not self.portfolio_values:
            max_drawdown_pct = 0.0
        else:
            peak = self.portfolio_values[0]
            max_drawdown = 0.0
            
            for value in self.portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            max_drawdown_pct = max_drawdown * 100
        
        # Calculate Sharpe ratio (assuming daily data)
        if len(self.portfolio_values) < 2:
            sharpe_ratio = 0.0
        else:
            returns = []
            for i in range(1, len(self.portfolio_values)):
                returns.append((self.portfolio_values[i] - self.portfolio_values[i-1]) / self.portfolio_values[i-1])
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'win_rate_percent': win_rate * 100,
            'profit_factor': profit_factor,
            'total_profit': total_profit,
            'total_return_percent': (total_profit / self.initial_balance) * 100,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': self.balance,
            'final_portfolio_value': self.portfolio_value
        }

class ModelDrivenStrategy(Strategy):
    """Strategy that uses ML model signals for trading decisions"""
    
    def __init__(self, name="ModelDriven", initial_balance=10000,
                 signal_manager: ModelSignalManager = None,
                 signal_threshold=0.6, confidence_threshold=0.5,
                 stop_loss_pct=0.02, take_profit_pct=0.04, position_size=1.0):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.signal_manager = signal_manager or ModelSignalManager()
        self.signal_threshold = signal_threshold
        self.confidence_threshold = confidence_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size = position_size
        
        # Track signals and performance
        self.signal_history = []
        self.last_signal = None
    
    def calculate_signals(self, df):
        """Calculate signals using model predictions"""
        df = df.copy()
        
        # Convert dataframe to historical data format
        historical_data = []
        for i, row in df.iterrows():
            historical_data.append({
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'timestamp': row.get('time', row.name)
            })
        
        # Generate signals for each row
        buy_signals = []
        sell_signals = []
        
        for i in range(len(df)):
            current_data = {
                'open': df.iloc[i]['open'],
                'high': df.iloc[i]['high'],
                'low': df.iloc[i]['low'],
                'close': df.iloc[i]['close'],
                'volume': df.iloc[i]['volume']
            }
            
            # Use historical data up to current point
            hist_data = historical_data[:i+1] if i > 0 else historical_data[:1]
            
            # Get consensus signal
            signal = self.signal_manager.get_consensus_signal(current_data, hist_data)
            
            # Store signal
            self.signal_history.append(signal)
            
            # Determine if signal meets thresholds
            meets_threshold = (signal.strength >= self.signal_threshold and 
                             signal.confidence >= self.confidence_threshold)
            
            buy_signals.append(signal.signal_type == SignalType.BUY and meets_threshold)
            sell_signals.append(signal.signal_type == SignalType.SELL and meets_threshold)
        
        df['model_buy_signal'] = buy_signals
        df['model_sell_signal'] = sell_signals
        
        return df
    
    def decide_action(self, current_data):
        """Determine action based on model signals"""
        if 'model_buy_signal' not in current_data or 'model_sell_signal' not in current_data:
            return Action.HOLD
        
        # Check buy signal
        if current_data['model_buy_signal'] and not self.position:
            return Action.BUY
        
        # Check sell signal
        elif current_data['model_sell_signal'] and self.position:
            return Action.SELL
        
        # Risk management: check stop loss and take profit
        if self.position and hasattr(self, 'entry_price'):
            current_price = current_data.get('close', current_data.get('price', 0))
            
            if self.position > 0:  # Long position
                # Stop loss
                if current_price <= self.entry_price * (1 - self.stop_loss_pct):
                    return Action.SELL
                # Take profit
                if current_price >= self.entry_price * (1 + self.take_profit_pct):
                    return Action.SELL
            
            elif self.position < 0:  # Short position
                # Stop loss
                if current_price >= self.entry_price * (1 + self.stop_loss_pct):
                    return Action.BUY
                # Take profit
                if current_price <= self.entry_price * (1 - self.take_profit_pct):
                    return Action.BUY
        
        return Action.HOLD

class HybridStrategy(Strategy):
    """Strategy that combines model signals with technical analysis"""
    
    def __init__(self, name="Hybrid", initial_balance=10000,
                 signal_manager: ModelSignalManager = None,
                 model_weight=0.7, ta_weight=0.3,
                 bb_length=20, bb_std=2.0, rsi_period=14,
                 stop_loss_pct=0.03, take_profit_pct=0.06, position_size=1.0):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.signal_manager = signal_manager or ModelSignalManager()
        self.model_weight = model_weight
        self.ta_weight = ta_weight
        
        # Technical analysis parameters
        self.bb_length = bb_length
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        
        # Risk management
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size = position_size
    
    def calculate_signals(self, df):
        """Calculate combined signals from models and technical analysis"""
        df = df.copy()
        
        # Add technical indicators
        from app.trading.indicators import add_bollinger_bands, add_rsi
        df = add_bollinger_bands(df, self.bb_length, self.bb_std)
        df = add_rsi(df, self.rsi_period)
        
        # Get model signals (same as ModelDrivenStrategy)
        historical_data = []
        for i, row in df.iterrows():
            historical_data.append({
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            })
        
        model_scores = []
        ta_scores = []
        
        for i in range(len(df)):
            # Model signal
            current_data = {
                'open': df.iloc[i]['open'],
                'high': df.iloc[i]['high'],
                'low': df.iloc[i]['low'],
                'close': df.iloc[i]['close'],
                'volume': df.iloc[i]['volume']
            }
            
            hist_data = historical_data[:i+1] if i > 0 else historical_data[:1]
            model_signal = self.signal_manager.get_consensus_signal(current_data, hist_data)
            
            # Convert model signal to score (-1 to 1)
            if model_signal.signal_type == SignalType.BUY:
                model_score = model_signal.strength * model_signal.confidence
            elif model_signal.signal_type == SignalType.SELL:
                model_score = -model_signal.strength * model_signal.confidence
            else:
                model_score = 0
            
            # Technical analysis score
            ta_score = 0
            
            # Bollinger Bands signal
            bb_upper_col = f'bb_upper_{self.bb_length}_{self.bb_std}'
            bb_lower_col = f'bb_lower_{self.bb_length}_{self.bb_std}'
            
            if bb_upper_col in df.columns and bb_lower_col in df.columns:
                if df.iloc[i]['close'] < df.iloc[i][bb_lower_col]:
                    ta_score += 0.5  # Oversold
                elif df.iloc[i]['close'] > df.iloc[i][bb_upper_col]:
                    ta_score -= 0.5  # Overbought
            
            # RSI signal
            rsi_col = f'rsi_{self.rsi_period}'
            if rsi_col in df.columns:
                rsi_value = df.iloc[i][rsi_col]
                if rsi_value < 30:
                    ta_score += 0.5  # Oversold
                elif rsi_value > 70:
                    ta_score -= 0.5  # Overbought
            
            model_scores.append(model_score)
            ta_scores.append(ta_score)
        
        # Combine scores
        combined_scores = []
        for model_score, ta_score in zip(model_scores, ta_scores):
            combined_score = (model_score * self.model_weight + 
                            ta_score * self.ta_weight)
            combined_scores.append(combined_score)
        
        # Generate buy/sell signals
        df['hybrid_buy_signal'] = [score > 0.3 for score in combined_scores]
        df['hybrid_sell_signal'] = [score < -0.3 for score in combined_scores]
        df['hybrid_score'] = combined_scores
        
        return df
    
    def decide_action(self, current_data):
        """Determine action based on hybrid signals"""
        if 'hybrid_buy_signal' not in current_data or 'hybrid_sell_signal' not in current_data:
            return Action.HOLD
        
        # Check signals
        if current_data['hybrid_buy_signal'] and not self.position:
            return Action.BUY
        elif current_data['hybrid_sell_signal'] and self.position:
            return Action.SELL
        
        # Risk management (same as ModelDrivenStrategy)
        if self.position and hasattr(self, 'entry_price'):
            current_price = current_data.get('close', current_data.get('price', 0))
            
            if self.position > 0:  # Long position
                if current_price <= self.entry_price * (1 - self.stop_loss_pct):
                    return Action.SELL
                if current_price >= self.entry_price * (1 + self.take_profit_pct):
                    return Action.SELL
            elif self.position < 0:  # Short position
                if current_price >= self.entry_price * (1 + self.stop_loss_pct):
                    return Action.BUY
                if current_price <= self.entry_price * (1 - self.take_profit_pct):
                    return Action.BUY
        
        return Action.HOLD
