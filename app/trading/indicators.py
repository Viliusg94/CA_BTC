"""
Technical indicators for trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def simple_moving_average(df: pd.DataFrame, column: str = 'close', window: int = 20) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA)
    
    Args:
        df: DataFrame with price data
        column: Column to use for calculation
        window: Window size for the moving average
        
    Returns:
        Series with SMA values
    """
    return df[column].rolling(window=window).mean()


def exponential_moving_average(df: pd.DataFrame, column: str = 'close', span: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        df: DataFrame with price data
        column: Column to use for calculation
        span: Span for the EMA
        
    Returns:
        Series with EMA values
    """
    return df[column].ewm(span=span, adjust=False).mean()


def bollinger_bands(df: pd.DataFrame, column: str = 'close', window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
    """
    Calculate Bollinger Bands
    
    Args:
        df: DataFrame with price data
        column: Column to use for calculation
        window: Window size for moving average
        num_std: Number of standard deviations for bands
        
    Returns:
        Dictionary with upper_band, middle_band, and lower_band
    """
    middle_band = df[column].rolling(window=window).mean()
    std_dev = df[column].rolling(window=window).std()
    
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    
    return {
        'middle_band': middle_band,
        'upper_band': upper_band,
        'lower_band': lower_band
    }


def relative_strength_index(df: pd.DataFrame, column: str = 'close', window: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        df: DataFrame with price data
        column: Column to use for calculation
        window: Window size for RSI calculation
        
    Returns:
        Series with RSI values
    """
    # Calculate price changes
    delta = df[column].diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and average loss
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def moving_average_convergence_divergence(df: pd.DataFrame, column: str = 'close', 
                                         fast_period: int = 12, slow_period: int = 26, 
                                         signal_period: int = 9) -> Dict[str, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD)
    
    Args:
        df: DataFrame with price data
        column: Column to use for calculation
        fast_period: Period for fast EMA
        slow_period: Period for slow EMA
        signal_period: Period for signal line
        
    Returns:
        Dictionary with macd_line, signal_line, and histogram
    """
    # Calculate fast and slow EMAs
    fast_ema = df[column].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df[column].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return {
        'macd_line': macd_line,
        'signal_line': signal_line,
        'histogram': histogram
    }


def average_true_range(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data
        window: Window size for ATR calculation
        
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate true range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR
    atr = tr.rolling(window=window).mean()
    
    return atr


def stochastic_oscillator(df: pd.DataFrame, window: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> Dict[str, pd.Series]:
    """
    Calculate Stochastic Oscillator
    
    Args:
        df: DataFrame with OHLC data
        window: Window size for calculation
        k_smooth: Smoothing for %K line
        d_smooth: Smoothing for %D line
        
    Returns:
        Dictionary with k_line and d_line
    """
    # Calculate %K
    low_min = df['low'].rolling(window=window).min()
    high_max = df['high'].rolling(window=window).max()
    
    k_raw = 100 * ((df['close'] - low_min) / (high_max - low_min))
    k_line = k_raw.rolling(window=k_smooth).mean()
    
    # Calculate %D
    d_line = k_line.rolling(window=d_smooth).mean()
    
    return {
        'k_line': k_line,
        'd_line': d_line
    }


def on_balance_volume(df: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV)
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Series with OBV values
    """
    # Get price change direction
    price_change = df['close'].diff()
    
    # Initialize OBV
    obv = pd.Series(0, index=df.index)
    
    # Calculate OBV
    obv.iloc[1:] = (
        (price_change.iloc[1:] > 0) * df['volume'].iloc[1:] -
        (price_change.iloc[1:] < 0) * df['volume'].iloc[1:] +
        (price_change.iloc[1:] == 0) * 0
    ).cumsum()
    
    return obv


def ichimoku_cloud(df: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26, 
                 senkou_span_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
    """
    Calculate Ichimoku Cloud
    
    Args:
        df: DataFrame with OHLC data
        tenkan_period: Period for Tenkan-sen (Conversion Line)
        kijun_period: Period for Kijun-sen (Base Line)
        senkou_span_b_period: Period for Senkou Span B (Leading Span B)
        displacement: Displacement for cloud
        
    Returns:
        Dictionary with tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, and chikou_span
    """
    # Calculate Tenkan-sen (Conversion Line)
    tenkan_high = df['high'].rolling(window=tenkan_period).max()
    tenkan_low = df['low'].rolling(window=tenkan_period).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    
    # Calculate Kijun-sen (Base Line)
    kijun_high = df['high'].rolling(window=kijun_period).max()
    kijun_low = df['low'].rolling(window=kijun_period).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    
    # Calculate Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # Calculate Senkou Span B (Leading Span B)
    senkou_b_high = df['high'].rolling(window=senkou_span_b_period).max()
    senkou_b_low = df['low'].rolling(window=senkou_span_b_period).min()
    senkou_span_b = ((senkou_b_high + senkou_b_low) / 2).shift(displacement)
    
    # Calculate Chikou Span (Lagging Span)
    chikou_span = df['close'].shift(-displacement)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


def fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci Retracement Levels
    
    Args:
        high: Highest price in the trend
        low: Lowest price in the trend
        
    Returns:
        Dictionary with retracement levels
    """
    diff = high - low
    
    return {
        '0.0': low,
        '0.236': low + 0.236 * diff,
        '0.382': low + 0.382 * diff,
        '0.5': low + 0.5 * diff,
        '0.618': low + 0.618 * diff,
        '0.786': low + 0.786 * diff,
        '1.0': high
    }


def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Classic Pivot Points
    
    Args:
        high: Previous period's high
        low: Previous period's low
        close: Previous period's close
        
    Returns:
        Dictionary with pivot point levels
    """
    pivot = (high + low + close) / 3
    
    return {
        'pivot': pivot,
        'r1': 2 * pivot - low,
        'r2': pivot + (high - low),
        'r3': pivot + 2 * (high - low),
        's1': 2 * pivot - high,
        's2': pivot - (high - low),
        's3': pivot - 2 * (high - low)
    }


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all indicators to DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicators added
    """
    result = df.copy()
    
    # Add Simple Moving Averages
    result['sma_10'] = simple_moving_average(df, window=10)
    result['sma_20'] = simple_moving_average(df, window=20)
    result['sma_50'] = simple_moving_average(df, window=50)
    result['sma_200'] = simple_moving_average(df, window=200)
    
    # Add Exponential Moving Averages
    result['ema_10'] = exponential_moving_average(df, span=10)
    result['ema_20'] = exponential_moving_average(df, span=20)
    result['ema_50'] = exponential_moving_average(df, span=50)
    result['ema_200'] = exponential_moving_average(df, span=200)
    
    # Add Bollinger Bands
    bb = bollinger_bands(df)
    result['bb_middle'] = bb['middle_band']
    result['bb_upper'] = bb['upper_band']
    result['bb_lower'] = bb['lower_band']
    
    # Add RSI
    result['rsi'] = relative_strength_index(df)
    
    # Add MACD
    macd = moving_average_convergence_divergence(df)
    result['macd'] = macd['macd_line']
    result['macd_signal'] = macd['signal_line']
    result['macd_hist'] = macd['histogram']
    
    # Add ATR
    result['atr'] = average_true_range(df)
    
    # Add Stochastic
    stoch = stochastic_oscillator(df)
    result['stoch_k'] = stoch['k_line']
    result['stoch_d'] = stoch['d_line']
    
    # Add OBV
    result['obv'] = on_balance_volume(df)
    
    # Add Ichimoku Cloud
    ichimoku = ichimoku_cloud(df)
    result['ichimoku_tenkan'] = ichimoku['tenkan_sen']
    result['ichimoku_kijun'] = ichimoku['kijun_sen']
    result['ichimoku_a'] = ichimoku['senkou_span_a']
    result['ichimoku_b'] = ichimoku['senkou_span_b']
    result['ichimoku_chikou'] = ichimoku['chikou_span']
    
    return result
