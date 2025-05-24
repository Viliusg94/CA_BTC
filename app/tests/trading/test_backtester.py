"""
Unit tests for the backtester module
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import warnings

# Add the project root to the path so we can import our modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.trading.backtester import Backtester
from app.trading.trading_strategies import Strategy, Action
from app.tests.trading.test_helpers import generate_test_data, validate_backtest_results

class TestStrategy(Strategy):
    """Simple test strategy for unit testing"""
    
    def __init__(self, name="Test Strategy", initial_balance=10000):
        super().__init__(name=name, initial_balance=initial_balance)
        self.custom_signals = []
    
    def calculate_signals(self, df):
        # Add a custom signal column for testing
        df = df.copy()
        df['signal'] = self.custom_signals
        return df
    
    def decide_action(self, current_data):
        if 'signal' not in current_data:
            return Action.HOLD
            
        signal = current_data['signal']
        if signal == 'buy' and not self.position:
            return Action.BUY
        elif signal == 'sell' and self.position:
            return Action.SELL
        else:
            return Action.HOLD


class BacktesterTests(unittest.TestCase):
    """Test cases for the Backtester class"""
    
    def setUp(self):
        """Set up test data"""
        # Create a simple dataframe with price data
        dates = pd.date_range(start='2023-01-01', periods=10)
        self.df = pd.DataFrame({
            'time': dates,
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
            'low': [95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
            'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        })
        self.df = self.df.set_index('time')
        
        # Create a test strategy with predefined signals
        self.strategy = TestStrategy()
    
    def test_basic_backtest(self):
        """Test basic backtest functionality"""
        # Setup signals: buy at index 2, sell at index 6
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, 'sell', None, None, None]
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Verify results
        self.assertEqual(results['total_trades'], 1)
        self.assertEqual(len(results['trades']), 2)  # One buy and one sell
        
        # Check if the strategy made a profit
        self.assertGreater(results['final_balance'], self.strategy.initial_balance)
    
    def test_backtest_with_stop_loss(self):
        """Test backtest with stop loss triggered"""
        # Setup signals: buy at index 2
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, None, None, None, None]
        
        # Set stop loss to trigger (5% below entry)
        self.strategy.stop_loss_pct = 0.05
        
        # Simulate price drop to trigger stop loss
        self.df.loc[self.df.index[4], 'close'] = 95  # 5% drop from entry at ~100
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Verify results
        self.assertEqual(results['total_trades'], 1)
        self.assertEqual(len(results['trades']), 2)  # One buy and one sell (stop loss)
        
        # Check if stop loss was triggered (balance should be less than initial)
        self.assertLess(results['final_balance'], self.strategy.initial_balance)
        
        # Verify the sell reason includes "stop_loss"
        self.assertIn('stop_loss', results['trades'][1].get('reason', '').lower())
    
    def test_backtest_with_take_profit(self):
        """Test backtest with take profit triggered"""
        # Setup signals: buy at index 2
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, None, None, None, None]
        
        # Set take profit to trigger (5% above entry)
        self.strategy.take_profit_pct = 0.05
        
        # Simulate price increase to trigger take profit
        self.df.loc[self.df.index[4], 'close'] = 108  # 8% increase from entry
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Verify results
        self.assertEqual(results['total_trades'], 1)
        self.assertEqual(len(results['trades']), 2)  # One buy and one sell (take profit)
        
        # Check if take profit was triggered (balance should be more than initial)
        self.assertGreater(results['final_balance'], self.strategy.initial_balance)
        
        # Verify the sell reason includes "take_profit"
        self.assertIn('take_profit', results['trades'][1].get('reason', '').lower())
    
    def test_backtest_with_missing_data(self):
        """Test backtest with missing data"""
        # Create dataframe with missing values
        df_missing = self.df.copy()
        df_missing.loc[df_missing.index[3], 'close'] = np.nan
        df_missing.loc[df_missing.index[5], 'high'] = np.nan
        df_missing.loc[df_missing.index[7], 'low'] = np.nan
        
        # Setup signals: buy at index 2, sell at index 8
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, None, None, 'sell', None]
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        
        # Run with warnings captured to check for missing data warnings
        with warnings.catch_warnings(record=True) as w:
            results = backtester.run_backtest(df_missing)
            self.assertTrue(any("missing data" in str(warning.message).lower() for warning in w))
        
        # Verify results - should still complete with missing data
        self.assertEqual(results['total_trades'], 1)
        self.assertEqual(len(results['trades']), 2)  # One buy and one sell
    
    def test_backtest_with_extreme_price_movement(self):
        """Test backtest with extreme price movements"""
        # Setup signals: buy at index 2, sell at index 8
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, None, None, 'sell', None]
        
        # Create dataframe with extreme price movement
        df_extreme = self.df.copy()
        # Add a 50% price spike
        df_extreme.loc[df_extreme.index[5], 'high'] = df_extreme.loc[df_extreme.index[4], 'close'] * 1.5
        df_extreme.loc[df_extreme.index[5], 'close'] = df_extreme.loc[df_extreme.index[4], 'close'] * 1.4
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(df_extreme)
        
        # Verify results
        self.assertEqual(results['total_trades'], 1)
        self.assertEqual(len(results['trades']), 2)  # One buy and one sell
        
        # Check if the trade profited from the price spike
        self.assertGreater(results['final_balance'], self.strategy.initial_balance)
    
    def test_multiple_trades(self):
        """Test backtest with multiple trades"""
        # Setup signals for multiple trades
        self.strategy.custom_signals = ['buy', None, 'sell', 'buy', None, 'sell', None, 'buy', 'sell', None]
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Verify results
        self.assertEqual(results['total_trades'], 3)
        self.assertEqual(len(results['trades']), 6)  # Three buys and three sells
    
    def test_no_trades(self):
        """Test backtest with no trades"""
        # Setup signals with no trades
        self.strategy.custom_signals = [None] * 10
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Verify results
        self.assertEqual(results['total_trades'], 0)
        self.assertEqual(len(results['trades']), 0)
        self.assertEqual(results['final_balance'], self.strategy.initial_balance)
    
    def test_edge_case_single_day(self):
        """Test backtest with single day of data"""
        # Create single-day dataframe
        df_single = pd.DataFrame({
            'time': [pd.Timestamp('2023-01-01')],
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [101],
            'volume': [1000]
        })
        df_single = df_single.set_index('time')
        
        # Setup signals: try to buy
        self.strategy.custom_signals = ['buy']
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(df_single)
        
        # Verify results - should not be able to complete a trade with single day
        self.assertEqual(results['total_trades'], 0)
    
    def test_parameter_optimization(self):
        """Test strategy parameter optimization"""
        # Create a strategy with configurable parameters
        class ParameterizedStrategy(Strategy):
            def __init__(self, name="Parameterized", initial_balance=10000, threshold=1.0):
                super().__init__(name=name, initial_balance=initial_balance)
                self.threshold = threshold
            
            def calculate_signals(self, df):
                df = df.copy()
                df['signal'] = np.where(df['close'] > df['close'].shift(1) * self.threshold, 'buy', 'sell')
                return df
                
            def decide_action(self, current_data):
                if current_data['signal'] == 'buy' and not self.position:
                    return Action.BUY
                elif current_data['signal'] == 'sell' and self.position:
                    return Action.SELL
                else:
                    return Action.HOLD
        
        # Create a longer dataframe for optimization
        dates = pd.date_range(start='2023-01-01', periods=100)
        df = pd.DataFrame({
            'time': dates,
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(100, 5, 100),
            'volume': np.random.normal(1000, 200, 100)
        })
        
        # Make sure prices follow a pattern
        for i in range(1, 100):
            df.loc[i, 'close'] = df.loc[i-1, 'close'] * (1 + np.random.normal(0, 0.02))
            df.loc[i, 'high'] = max(df.loc[i, 'close'] * 1.03, df.loc[i, 'close'])
            df.loc[i, 'low'] = min(df.loc[i, 'close'] * 0.97, df.loc[i, 'close'])
            df.loc[i, 'open'] = df.loc[i-1, 'close']
        
        # Set the time column as index
        df = df.set_index('time')
        
        # Create strategy and backtester
        strategy = ParameterizedStrategy()
        backtester = Backtester(strategy)
        
        # Define parameter grid
        param_grid = {'threshold': [0.99, 1.0, 1.01]}
        
        # Run optimization
        best_params, best_result = backtester.optimize_strategy_parameters(
            df, param_grid, metric='total_return_percent', maximize=True
        )
        
        # Verify that optimization returned results
        self.assertIsNotNone(best_params)
        self.assertIn('threshold', best_params)
        self.assertIsNotNone(best_result)
        self.assertIn('total_return_percent', best_result)
    
    def test_walk_forward_analysis(self):
        """Test walk-forward analysis functionality"""
        # Create a strategy with configurable parameters
        class SimpleStrategy(Strategy):
            def __init__(self, name="Simple", initial_balance=10000, window=3):
                super().__init__(name=name, initial_balance=initial_balance)
                self.window = window
            
            def calculate_signals(self, df):
                df = df.copy()
                # Simple moving average strategy: buy when price > MA, sell when price < MA
                df['ma'] = df['close'].rolling(window=self.window).mean()
                df['signal'] = np.where(df['close'] > df['ma'], 'buy', 'sell')
                return df
                
            def decide_action(self, current_data):
                if 'signal' not in current_data or pd.isna(current_data['signal']):
                    return Action.HOLD
                if current_data['signal'] == 'buy' and not self.position:
                    return Action.BUY
                elif current_data['signal'] == 'sell' and self.position:
                    return Action.SELL
                else:
                    return Action.HOLD
        
        # Create a dataframe with price trends
        dates = pd.date_range(start='2023-01-01', periods=50)
        df = pd.DataFrame({
            'time': dates,
            'open': np.linspace(100, 200, 50),
            'high': np.linspace(105, 210, 50),
            'low': np.linspace(95, 190, 50),
            'close': np.linspace(101, 205, 50),
            'volume': np.random.normal(1000, 200, 50)
        })
        
        # Add some noise to prices
        df['close'] = df['close'] + np.random.normal(0, 5, 50)
        df['high'] = df['close'] + np.random.normal(5, 2, 50)
        df['low'] = df['close'] - np.random.normal(5, 2, 50)
        df['open'] = df['close'] - np.random.normal(0, 2, 50)
        
        # Set the time column as index
        df = df.set_index('time')
        
        # Create strategy and backtester
        strategy = SimpleStrategy()
        backtester = Backtester(strategy)
        
        # Define parameter grid
        param_grid = {'window': [2, 3, 5]}
        
        # Run walk-forward analysis
        wfa_results = backtester.walk_forward_analysis(
            df, param_grid, window_size=20, step_size=10, metric='total_return_percent', maximize=True
        )
        
        # Verify results
        self.assertIsNotNone(wfa_results)
        self.assertIsInstance(wfa_results, list)
        self.assertGreater(len(wfa_results), 0)
        # Each result should have a parameters dict and results dict
        for params, result in wfa_results:
            self.assertIsInstance(params, dict)
            self.assertIn('window', params)
            self.assertIsInstance(result, dict)
            self.assertIn('total_return_percent', result)
    
    def test_result_validation(self):
        """Test validation of backtest results"""
        # Setup signals for a trade
        self.strategy.custom_signals = [None, None, 'buy', None, None, None, 'sell', None, None, None]
        
        # Create backtester and run
        backtester = Backtester(self.strategy)
        results = backtester.run_backtest(self.df)
        
        # Validate results using validation function
        is_valid, message = validate_backtest_results(results)
        self.assertTrue(is_valid, f"Validation failed: {message}")


if __name__ == '__main__':
    unittest.main()
