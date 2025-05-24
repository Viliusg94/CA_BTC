"""
Trading strategy implementations - various specific trading strategies
for cryptocurrency trading
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from app.trading.trading_strategies import Strategy, Action, TradePosition
from app.trading.indicators import (
    simple_moving_average, exponential_moving_average,
    bollinger_bands, relative_strength_index,
    moving_average_convergence_divergence, stochastic_oscillator
)

logger = logging.getLogger(__name__)


class MovingAverageStrategy(Strategy):
    """Trading strategy based on Moving Average crossovers"""
    
    def __init__(self, name: str = "MA Crossover", initial_balance: float = 10000.0,
                 short_window: int = 10, long_window: int = 50, 
                 use_ema: bool = False, **kwargs):
        """
        Initialize the Moving Average Crossover strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            short_window: Short moving average window
            long_window: Long moving average window
            use_ema: Use exponential moving average instead of simple moving average
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        self.short_window = short_window
        self.long_window = long_window
        self.use_ema = use_ema
        
        # Ensure long window is actually longer than short window
        if self.short_window >= self.long_window:
            logger.warning(f"Short window ({short_window}) should be less than long window ({long_window})")
            self.short_window = min(self.short_window, self.long_window - 5)
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on Moving Average crossover
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # Calculate moving averages
        if self.use_ema:
            result_df['short_ma'] = exponential_moving_average(df, span=self.short_window)
            result_df['long_ma'] = exponential_moving_average(df, span=self.long_window)
        else:
            result_df['short_ma'] = simple_moving_average(df, window=self.short_window)
            result_df['long_ma'] = simple_moving_average(df, window=self.long_window)
        
        # Initialize signals column
        result_df['signal'] = 0
        
        # Generate signals: 1 for buy, -1 for sell
        # Buy signal: short MA crosses above long MA
        # Sell signal: short MA crosses below long MA
        result_df['short_gt_long'] = result_df['short_ma'] > result_df['long_ma']
        result_df['signal'] = result_df['short_gt_long'].astype(int).diff()
        
        # Convert signals to Action enum values
        result_df['action'] = Action.HOLD.value
        result_df.loc[result_df['signal'] == 1, 'action'] = Action.BUY.value
        result_df.loc[result_df['signal'] == -1, 'action'] = Action.SELL.value
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        return Action.HOLD


class RSIStrategy(Strategy):
    """Trading strategy based on Relative Strength Index (RSI)"""
    
    def __init__(self, name: str = "RSI", initial_balance: float = 10000.0,
                 window: int = 14, oversold: float = 30, overbought: float = 70, **kwargs):
        """
        Initialize the RSI strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            window: RSI calculation window
            oversold: Oversold threshold (buy signal when RSI < oversold)
            overbought: Overbought threshold (sell signal when RSI > overbought)
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        self.window = window
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on RSI values
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # Calculate RSI
        result_df['rsi'] = relative_strength_index(df, window=self.window)
        
        # Initialize signals
        result_df['signal'] = 0
        
        # Generate signals
        # Buy when RSI crosses below oversold level
        result_df['is_oversold'] = result_df['rsi'] < self.oversold
        result_df['buy_signal'] = (result_df['is_oversold'] != result_df['is_oversold'].shift(1)) & result_df['is_oversold']
        
        # Sell when RSI crosses above overbought level
        result_df['is_overbought'] = result_df['rsi'] > self.overbought
        result_df['sell_signal'] = (result_df['is_overbought'] != result_df['is_overbought'].shift(1)) & result_df['is_overbought']
        
        # Convert to action column
        result_df['action'] = Action.HOLD.value
        result_df.loc[result_df['buy_signal'], 'action'] = Action.BUY.value
        result_df.loc[result_df['sell_signal'], 'action'] = Action.SELL.value
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        # Alternative logic using RSI directly if action column is not available
        if 'rsi' in current_data:
            rsi_value = current_data['rsi']
            if rsi_value < self.oversold:
                return Action.BUY
            elif rsi_value > self.overbought:
                return Action.SELL
        
        return Action.HOLD


class BollingerBandsStrategy(Strategy):
    """Trading strategy based on Bollinger Bands"""
    
    def __init__(self, name: str = "Bollinger Bands", initial_balance: float = 10000.0,
                 window: int = 20, num_std: float = 2.0, **kwargs):
        """
        Initialize the Bollinger Bands strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            window: Bollinger Bands calculation window
            num_std: Number of standard deviations for bands
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        self.window = window
        self.num_std = num_std
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on Bollinger Bands breakouts
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # Calculate Bollinger Bands
        bb = bollinger_bands(df, window=self.window, num_std=self.num_std)
        result_df['bb_upper'] = bb['upper_band']
        result_df['bb_middle'] = bb['middle_band']
        result_df['bb_lower'] = bb['lower_band']
        
        # Calculate price distance from bands
        result_df['price_delta_upper'] = (result_df['close'] - result_df['bb_upper']) / result_df['bb_upper']
        result_df['price_delta_lower'] = (result_df['close'] - result_df['bb_lower']) / result_df['bb_lower']
        
        # Identify touch/breach of bands
        result_df['upper_touch'] = result_df['high'] >= result_df['bb_upper']
        result_df['lower_touch'] = result_df['low'] <= result_df['bb_lower']
        
        # Price crossing back inside the band after touching or breaching
        result_df['upper_cross_inside'] = (result_df['upper_touch'].shift(1) == True) & (result_df['close'] < result_df['bb_upper'])
        result_df['lower_cross_inside'] = (result_df['lower_touch'].shift(1) == True) & (result_df['close'] > result_df['bb_lower'])
        
        # Generate signals
        result_df['signal'] = 0
        
        # Sell signal: price crosses back inside the upper band (reversal of upward movement)
        result_df.loc[result_df['upper_cross_inside'], 'signal'] = -1
        
        # Buy signal: price crosses back inside the lower band (reversal of downward movement)
        result_df.loc[result_df['lower_cross_inside'], 'signal'] = 1
        
        # Convert to action column
        result_df['action'] = Action.HOLD.value
        result_df.loc[result_df['signal'] == 1, 'action'] = Action.BUY.value
        result_df.loc[result_df['signal'] == -1, 'action'] = Action.SELL.value
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        # Alternative logic using Bollinger Bands directly if action column is not available
        if all(k in current_data for k in ['close', 'bb_upper', 'bb_lower', 'bb_middle']):
            close = current_data['close']
            bb_upper = current_data['bb_upper']
            bb_lower = current_data['bb_lower']
            bb_middle = current_data['bb_middle']
            
            # Calculate volatility to adjust trade decisions
            volatility = (bb_upper - bb_lower) / bb_middle
            
            # Decision with volatility adjustment
            if close <= bb_lower * (1 + 0.02 * volatility):  # Near lower band
                return Action.BUY
            elif close >= bb_upper * (1 - 0.02 * volatility):  # Near upper band
                return Action.SELL
        
        return Action.HOLD


class MACDStrategy(Strategy):
    """Trading strategy based on Moving Average Convergence Divergence (MACD)"""
    
    def __init__(self, name: str = "MACD", initial_balance: float = 10000.0,
                 fast_period: int = 12, slow_period: int = 26, 
                 signal_period: int = 9, **kwargs):
        """
        Initialize the MACD strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            fast_period: Fast period for MACD calculation
            slow_period: Slow period for MACD calculation
            signal_period: Signal period for MACD calculation
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on MACD
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # Calculate MACD
        macd = moving_average_convergence_divergence(df, 
                                                    fast_period=self.fast_period, 
                                                    slow_period=self.slow_period, 
                                                    signal_period=self.signal_period)
        
        result_df['macd_line'] = macd['macd_line']
        result_df['signal_line'] = macd['signal_line']
        result_df['histogram'] = macd['histogram']
        
        # Initialize signals
        result_df['signal'] = 0
        
        # Generate signals for zero crossover of the MACD line
        result_df['macd_above_zero'] = result_df['macd_line'] > 0
        result_df['zero_cross_signal'] = result_df['macd_above_zero'].astype(int).diff()
        
        # Generate signals for MACD crossing with signal line
        result_df['macd_above_signal'] = result_df['macd_line'] > result_df['signal_line']
        result_df['signal_cross'] = result_df['macd_above_signal'].astype(int).diff()
        
        # Buy signal: MACD line crosses above signal line OR MACD crosses above zero
        buy_condition = (result_df['signal_cross'] == 1) | (result_df['zero_cross_signal'] == 1)
        result_df.loc[buy_condition, 'signal'] = 1
        
        # Sell signal: MACD line crosses below signal line OR MACD crosses below zero
        sell_condition = (result_df['signal_cross'] == -1) | (result_df['zero_cross_signal'] == -1)
        result_df.loc[sell_condition, 'signal'] = -1
        
        # Convert to action column
        result_df['action'] = Action.HOLD.value
        result_df.loc[result_df['signal'] == 1, 'action'] = Action.BUY.value
        result_df.loc[result_df['signal'] == -1, 'action'] = Action.SELL.value
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        # Alternative logic using MACD directly if action column is not available
        if all(k in current_data for k in ['macd_line', 'signal_line', 'histogram']):
            macd_line = current_data['macd_line'] 
            signal_line = current_data['signal_line']
            histogram = current_data['histogram']
            
            # MACD line crossing above signal line with positive momentum
            if macd_line > signal_line and histogram > 0 and histogram > current_data.get('histogram_prev', 0):
                return Action.BUY
                
            # MACD line crossing below signal line with negative momentum
            elif macd_line < signal_line and histogram < 0 and histogram < current_data.get('histogram_prev', 0):
                return Action.SELL
        
        return Action.HOLD


class MLModelStrategy(Strategy):
    """Trading strategy based on machine learning model predictions"""
    
    def __init__(self, name: str = "ML Model", initial_balance: float = 10000.0,
                 model=None, threshold: float = 0.005, **kwargs):
        """
        Initialize the ML Model strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            model: Pre-trained machine learning model
            threshold: Price change threshold for signal generation
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        self.model = model
        self.threshold = threshold
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on ML model predictions
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # If no model is provided, return dataframe without signals
        if self.model is None:
            logger.warning("No ML model provided for MLModelStrategy")
            result_df['action'] = Action.HOLD.value
            return result_df
            
        try:
            # Prepare data for prediction (this will depend on your model)
            # Here we're assuming the model takes the last n rows of data
            # and predicts the next price movement
            
            # Generate predictions
            predictions = []
            
            # For each data point, predict using a rolling window
            for i in range(len(df)):
                if i < self.model.sequence_length:
                    # Not enough data for prediction
                    predictions.append(np.nan)
                else:
                    # Extract sequence
                    sequence = df.iloc[i - self.model.sequence_length:i]
                    
                    # Preprocess (specific to your model)
                    X = sequence[self.model.feature_columns].values.reshape(1, self.model.sequence_length, -1)
                    
                    # Make prediction
                    pred = self.model.predict(X)[0][0]
                    predictions.append(pred)
            
            result_df['predicted_price'] = predictions
            result_df['predicted_return'] = (result_df['predicted_price'].shift(-1) - result_df['close']) / result_df['close']
            
            # Generate signals based on predicted returns
            result_df['signal'] = 0
            result_df.loc[result_df['predicted_return'] > self.threshold, 'signal'] = 1
            result_df.loc[result_df['predicted_return'] < -self.threshold, 'signal'] = -1
            
            # Convert to action column
            result_df['action'] = Action.HOLD.value
            result_df.loc[result_df['signal'] == 1, 'action'] = Action.BUY.value
            result_df.loc[result_df['signal'] == -1, 'action'] = Action.SELL.value
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            result_df['action'] = Action.HOLD.value
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        # Alternative logic using predicted return directly if available
        if 'predicted_return' in current_data:
            predicted_return = current_data['predicted_return']
            if predicted_return > self.threshold:
                return Action.BUY
            elif predicted_return < -self.threshold:
                return Action.SELL
        
        return Action.HOLD


class EnsembleStrategy(Strategy):
    """Trading strategy that combines multiple strategies"""
    
    def __init__(self, name: str = "Ensemble", initial_balance: float = 10000.0,
                 strategies: List[Strategy] = None, weights: List[float] = None, **kwargs):
        """
        Initialize the Ensemble strategy
        
        Args:
            name: Strategy name
            initial_balance: Initial balance in USD
            strategies: List of strategy instances to combine
            weights: List of weights for each strategy (must sum to 1)
            **kwargs: Additional arguments to pass to the base Strategy class
        """
        super().__init__(name=name, initial_balance=initial_balance, **kwargs)
        
        # Validate strategies
        if strategies is None or len(strategies) == 0:
            raise ValueError("At least one strategy must be provided")
        self.strategies = strategies
        
        # Validate weights
        if weights is None:
            # Equal weights if not specified
            self.weights = [1.0 / len(strategies)] * len(strategies)
        else:
            if len(weights) != len(strategies):
                raise ValueError("Number of weights must match number of strategies")
            if abs(sum(weights) - 1.0) > 1e-10:  # Allow small floating point errors
                raise ValueError("Weights must sum to 1.0")
            self.weights = weights
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals by combining signals from multiple strategies
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals column added
        """
        result_df = df.copy()
        
        # Get signals from each strategy
        signal_values = np.zeros(len(df))
        
        for i, strategy in enumerate(self.strategies):
            # Calculate signals for this strategy
            strategy_df = strategy.calculate_signals(df)
            
            # Extract signal column
            if 'signal' in strategy_df.columns:
                strategy_signals = strategy_df['signal'].values
            else:
                # Convert action to signal if signal column doesn't exist
                strategy_signals = np.zeros(len(df))
                strategy_signals[strategy_df['action'] == Action.BUY.value] = 1
                strategy_signals[strategy_df['action'] == Action.SELL.value] = -1
                
            # Apply weight
            signal_values += strategy_signals * self.weights[i]
        
        # Threshold weighted signal values
        result_df['signal'] = 0
        result_df.loc[signal_values > 0.25, 'signal'] = 1   # Strong buy signal
        result_df.loc[signal_values < -0.25, 'signal'] = -1  # Strong sell signal
        
        # Convert to action column
        result_df['action'] = Action.HOLD.value
        result_df.loc[result_df['signal'] == 1, 'action'] = Action.BUY.value
        result_df.loc[result_df['signal'] == -1, 'action'] = Action.SELL.value
        
        # Add individual strategy signals for reference
        for i, strategy in enumerate(self.strategies):
            col_name = f"strategy_{i+1}_signal"
            strategy_df = strategy.calculate_signals(df)
            if 'signal' in strategy_df.columns:
                result_df[col_name] = strategy_df['signal']
        
        return result_df
    
    def decide_action(self, current_data: Dict) -> Action:
        """
        Decide what action to take based on current data
        
        Args:
            current_data: Dictionary with current market data
            
        Returns:
            Action: HOLD, BUY, or SELL
        """
        if 'action' in current_data:
            action_value = current_data['action']
            if action_value == Action.BUY.value:
                return Action.BUY
            elif action_value == Action.SELL.value:
                return Action.SELL
        
        # If action is not available, query individual strategies
        votes = []
        for strategy in self.strategies:
            action = strategy.decide_action(current_data)
            if action == Action.BUY:
                votes.append(1)
            elif action == Action.SELL:
                votes.append(-1)
            else:
                votes.append(0)
        
        # Weighted average of votes
        weighted_vote = sum(v * w for v, w in zip(votes, self.weights))
        
        if weighted_vote > 0.25:
            return Action.BUY
        elif weighted_vote < -0.25:
            return Action.SELL
        
        return Action.HOLD


# Factory function to create strategies
def create_strategy(strategy_type: str, **kwargs) -> Strategy:
    """
    Factory function to create a strategy instance
    
    Args:
        strategy_type: Type of strategy to create
        **kwargs: Strategy parameters
        
    Returns:
        Strategy: Instance of the specified strategy
    """
    strategies = {
        'moving_average': MovingAverageStrategy,
        'rsi': RSIStrategy,
        'bollinger_bands': BollingerBandsStrategy,
        'macd': MACDStrategy,
        'ml_model': MLModelStrategy,
        'ensemble': EnsembleStrategy
    }
    
    if strategy_type.lower() not in strategies:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    strategy_class = strategies[strategy_type.lower()]
    return strategy_class(**kwargs)
