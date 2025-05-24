"""
Helper functions for testing the backtester
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_data(days=30, base_price=100, volatility=0.02, trend=0.001):
    """
    Generate synthetic price data for testing
    
    Args:
        days (int): Number of days to generate
        base_price (float): Starting price
        volatility (float): Daily volatility as a decimal
        trend (float): Daily trend as a decimal (positive=uptrend, negative=downtrend)
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    # Generate dates
    dates = pd.date_range(start='2023-01-01', periods=days)
    
    # Initialize price at base_price
    prices = [base_price]
    
    # Generate subsequent prices with random walk
    for i in range(1, days):
        # Random component (daily volatility)
        random_change = np.random.normal(0, volatility)
        # Trend component
        trend_change = trend
        # New price
        new_price = prices[-1] * (1 + random_change + trend_change)
        prices.append(max(new_price, 0.1))  # Ensure price is positive
    
    # Generate OHLCV data
    df = pd.DataFrame({
        'time': dates,
        'close': prices
    })
    
    # Generate open, high, low
    for i in range(len(df)):
        if i == 0:
            df.loc[df.index[i], 'open'] = prices[i] * (1 - volatility/2)
        else:
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close']
        
        # Random high and low around close
        high_offset = abs(np.random.normal(0, volatility))
        low_offset = abs(np.random.normal(0, volatility))
        df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * (1 + high_offset)
        df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * (1 - low_offset)
    
    # Generate volume (correlated with price changes)
    base_volume = 1000
    volumes = []
    for i in range(len(df)):
        if i == 0:
            price_change = 0
        else:
            price_change = abs((df.loc[df.index[i], 'close'] - df.loc[df.index[i-1], 'close']) / df.loc[df.index[i-1], 'close'])
        
        # Higher volume on bigger price changes
        volume_multiplier = 1 + 5 * price_change
        # Add randomness
        volume = base_volume * volume_multiplier * np.random.uniform(0.8, 1.2)
        volumes.append(volume)
    
    df['volume'] = volumes
    
    # Set time as index
    df = df.set_index('time')
    
    return df

def generate_specific_scenario(scenario_type, days=30, base_price=100):
    """
    Generate specific test scenarios
    
    Args:
        scenario_type (str): Type of scenario ('uptrend', 'downtrend', 'sideways', 
                             'volatile', 'crash', 'rally', 'missing_data')
        days (int): Number of days
        base_price (float): Starting price
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    if scenario_type == 'uptrend':
        return generate_test_data(days, base_price, volatility=0.01, trend=0.01)
    
    elif scenario_type == 'downtrend':
        return generate_test_data(days, base_price, volatility=0.01, trend=-0.01)
    
    elif scenario_type == 'sideways':
        return generate_test_data(days, base_price, volatility=0.01, trend=0)
    
    elif scenario_type == 'volatile':
        return generate_test_data(days, base_price, volatility=0.05, trend=0)
    
    elif scenario_type == 'crash':
        # Normal data for the first half, then crash
        df = generate_test_data(days, base_price, volatility=0.01, trend=0.005)
        crash_start = days // 2
        crash_end = min(crash_start + 5, days)
        # 30% drop over 5 days
        for i in range(crash_start, crash_end):
            df.loc[df.index[i], 'close'] = df.loc[df.index[crash_start-1], 'close'] * (1 - 0.06 * (i - crash_start + 1))
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close']
            df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 1.02
            df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 0.98
        
        # Recovery period
        for i in range(crash_end, days):
            recovery_factor = 1 + 0.02 * (i - crash_end + 1)
            df.loc[df.index[i], 'close'] = min(
                df.loc[df.index[crash_end-1], 'close'] * recovery_factor, 
                df.loc[df.index[crash_start-1], 'close']  # Cap recovery at pre-crash level
            )
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close']
            df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 1.02
            df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 0.98
        
        return df
    
    elif scenario_type == 'rally':
        # Normal data for the first half, then rally
        df = generate_test_data(days, base_price, volatility=0.01, trend=-0.002)
        rally_start = days // 2
        rally_end = min(rally_start + 5, days)
        # 30% rise over 5 days
        for i in range(rally_start, rally_end):
            df.loc[df.index[i], 'close'] = df.loc[df.index[rally_start-1], 'close'] * (1 + 0.06 * (i - rally_start + 1))
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close']
            df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 1.02
            df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 0.98
        
        # Consolidation period
        for i in range(rally_end, days):
            consolidation_factor = 1 - 0.01 * (i - rally_end + 1)
            df.loc[df.index[i], 'close'] = max(
                df.loc[df.index[rally_end-1], 'close'] * consolidation_factor, 
                df.loc[df.index[rally_start-1], 'close'] * 1.15  # Floor consolidation at 15% above pre-rally
            )
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close']
            df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 1.02
            df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'open'], df.loc[df.index[i], 'close']) * 0.98
        
        return df
    
    elif scenario_type == 'missing_data':
        df = generate_test_data(days, base_price, volatility=0.02, trend=0.001)
        
        # Randomly remove some data points
        missing_indices = np.random.choice(range(days), size=days//10, replace=False)
        for idx in missing_indices:
            columns_to_nullify = np.random.choice(['open', 'high', 'low', 'close'], 
                                                size=np.random.randint(1, 4), 
                                                replace=False)
            for col in columns_to_nullify:
                df.loc[df.index[idx], col] = np.nan
        
        return df
    
    else:
        # Default case
        return generate_test_data(days, base_price, volatility=0.02, trend=0.001)

def validate_backtest_results(results):
    """
    Validate backtest results for consistency and correctness
    
    Args:
        results (dict): Backtest results dictionary
        
    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
    # Check if essential keys exist
    essential_keys = ['strategy_name', 'initial_balance', 'final_balance', 'total_trades', 'trades']
    for key in essential_keys:
        if key not in results:
            return False, f"Missing essential key: {key}"
    
    # Check if final balance is consistent with trades
    expected_final_balance = results['initial_balance']
    
    # Calculate P&L from trades
    trade_profit_loss = 0
    buy_trades = []
    sell_trades = []
    
    for trade in results['trades']:
        if trade['action'] == 'BUY':
            buy_trades.append(trade)
        elif trade['action'] == 'SELL':
            sell_trades.append(trade)
            
            # Match this sell with the most recent unmatched buy
            if buy_trades:
                buy_trade = buy_trades.pop(0)  # Get the oldest buy trade
                
                # Calculate profit/loss for this trade pair
                quantity = trade['quantity'] if 'quantity' in trade else buy_trade.get('quantity', 0)
                buy_price = buy_trade['price'] if 'price' in buy_trade else 0
                sell_price = trade['price'] if 'price' in trade else 0
                
                trade_profit_loss += quantity * (sell_price - buy_price)
                
                # Subtract commission if applicable
                if 'commission' in buy_trade:
                    trade_profit_loss -= buy_trade['commission']
                if 'commission' in trade:
                    trade_profit_loss -= trade['commission']
    
    # Check if there are unmatched buy trades (open positions)
    if buy_trades:
        return False, f"Found {len(buy_trades)} unmatched buy trades - positions not closed"
    
    # Calculate expected final balance
    expected_final_balance += trade_profit_loss
    
    # Allow small floating point differences (< $1)
    if abs(expected_final_balance - results['final_balance']) > 1:
        return False, f"Final balance inconsistent: expected ≈{expected_final_balance:.2f}, got {results['final_balance']:.2f}"
    
    # Check if total trades is consistent with trades list
    if results['total_trades'] != len(results['trades']) // 2:  # Each trade is a buy+sell pair
        return False, f"Total trades inconsistent: {results['total_trades']} reported, but {len(results['trades']) // 2} found"
    
    # Check if metrics are calculated correctly
    if 'win_rate_percent' in results:
        # Count winning trades
        winning_trades = 0
        trade_pairs = len(results['trades']) // 2
        
        for i in range(trade_pairs):
            buy_idx = i * 2
            sell_idx = buy_idx + 1
            
            if buy_idx < len(results['trades']) and sell_idx < len(results['trades']):
                buy_trade = results['trades'][buy_idx]
                sell_trade = results['trades'][sell_idx]
                
                if 'price' in buy_trade and 'price' in sell_trade:
                    if sell_trade['price'] > buy_trade['price']:
                        winning_trades += 1
        
        # Calculate expected win rate
        expected_win_rate = (winning_trades / trade_pairs * 100) if trade_pairs > 0 else 0
        
        # Allow small differences (< 0.5%)
        if abs(expected_win_rate - results['win_rate_percent']) > 0.5:
            return False, f"Win rate inconsistent: expected ≈{expected_win_rate:.2f}%, got {results['win_rate_percent']:.2f}%"
    
    # Validation passed
    return True, "Backtest results validated successfully"
