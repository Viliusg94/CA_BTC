"""
Visualization tools for trading strategies and backtesting results
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any, Union
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_equity_curve(results: Dict[str, Any], buy_hold: bool = True, 
                     show_drawdown: bool = True, figsize: Tuple[int, int] = (14, 8)) -> plt.Figure:
    """
    Plot the equity curve from backtest results
    
    Args:
        results: Dictionary with backtest results
        buy_hold: Whether to include buy & hold comparison
        show_drawdown: Whether to include drawdown subplot
        figsize: Figure size
        
    Returns:
        Figure object
    """
    portfolio_values = results['portfolio_values']
    dates = results.get('dates', range(len(portfolio_values)))
    prices = results['prices']
    
    # Create figure
    if show_drawdown:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    else:
        fig, ax1 = plt.subplots(figsize=figsize)
    
    # Plot equity curve
    ax1.plot(dates, portfolio_values, label='Strategy', linewidth=2, color='blue')
    ax1.set_ylabel('Portfolio Value', fontsize=12)
    ax1.set_title(f"Equity Curve: {results['strategy_name']}", fontsize=14, fontweight='bold')
    
    # Add price on secondary y-axis
    ax1_twin = ax1.twinx()
    ax1_twin.plot(dates, prices, label='Asset Price', color='gray', alpha=0.5)
    ax1_twin.set_ylabel('Asset Price', fontsize=12, color='gray')
    
    # Add buy & hold line
    if buy_hold:
        initial_value = portfolio_values[0]
        initial_price = prices[0]
        buy_hold_values = [initial_value * (price / initial_price) for price in prices]
        ax1.plot(dates, buy_hold_values, label='Buy & Hold', linestyle='--', color='green', alpha=0.7)
    
    # Add trade markers
    trades = results.get('trades', [])
    
    if trades:
        buy_dates = []
        sell_dates = []
        buy_prices = []
        sell_prices = []
        
        trade_index = 0
        for i, date in enumerate(dates):
            if trade_index < len(trades):
                trade = trades[trade_index]
                if hasattr(trade, 'get'):  # Check if it's a dictionary
                    trade_date = trade.get('timestamp')
                    
                    if trade_date == date:
                        if trade.get('action') == 'BUY':
                            buy_dates.append(date)
                            buy_prices.append(prices[i])
                        elif trade.get('action') == 'SELL':
                            sell_dates.append(date)
                            sell_prices.append(prices[i])
                        
                        trade_index += 1
        
        if buy_dates:
            ax1_twin.scatter(buy_dates, buy_prices, marker='^', color='green', s=100, label='Buy', zorder=5)
        
        if sell_dates:
            ax1_twin.scatter(sell_dates, sell_prices, marker='v', color='red', s=100, label='Sell', zorder=5)
    
    # Add drawdown subplot
    if show_drawdown:
        # Calculate drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak * 100
        
        ax2.fill_between(dates, drawdown, 0, color='red', alpha=0.3, label='Drawdown')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.set_ylim(max(drawdown) * 1.1, 0)  # Reverse y-axis for drawdown
        ax2.grid(True, alpha=0.3)
    
    # Add legend for both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Format the plot
    ax1.grid(True, alpha=0.3)
    
    # Format dates if dates are datetime objects
    if hasattr(dates[0], 'strftime'):
        fig.autofmt_xdate()
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
    plt.tight_layout()
    return fig

def plot_returns_distribution(results: Dict[str, Any], figsize: Tuple[int, int] = (14, 6)) -> plt.Figure:
    """
    Plot the distribution of returns
    
    Args:
        results: Dictionary with backtest results
        figsize: Figure size
        
    Returns:
        Figure object
    """
    portfolio_values = results['portfolio_values']
    
    # Calculate daily returns
    returns = np.diff(portfolio_values) / portfolio_values[:-1] * 100
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot distribution
    sns.histplot(returns, kde=True, bins=50, ax=ax, color='blue')
    ax.axvline(x=0, color='red', linestyle='--', alpha=0.8)
    
    # Calculate stats
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    skew = np.mean(((returns - mean_return) / std_return) ** 3) if std_return > 0 else 0
    kurtosis = np.mean(((returns - mean_return) / std_return) ** 4) - 3 if std_return > 0 else 0
    
    # Add stats text box
    stats_text = f"Mean: {mean_return:.2f}%\nStd Dev: {std_return:.2f}%\nSkew: {skew:.2f}\nKurtosis: {kurtosis:.2f}"
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, fontsize=12,
           verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_title('Returns Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Daily Return (%)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_underwater_curve(results: Dict[str, Any], figsize: Tuple[int, int] = (14, 6)) -> plt.Figure:
    """
    Plot underwater curve (drawdown over time)
    
    Args:
        results: Dictionary with backtest results
        figsize: Figure size
        
    Returns:
        Figure object
    """
    portfolio_values = results['portfolio_values']
    dates = results.get('dates', range(len(portfolio_values)))
    
    # Calculate drawdown
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (peak - portfolio_values) / peak * 100
    
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
    ax.plot(dates, drawdown, color='red', alpha=0.8)
    
    # Stats
    max_dd = np.max(drawdown)
    max_dd_idx = np.argmax(drawdown)
    recovery_idx = np.argmax(portfolio_values[max_dd_idx:]) + max_dd_idx if max_dd_idx < len(portfolio_values) - 1 else max_dd_idx
    if recovery_idx == max_dd_idx:
        recovery_time = "Not recovered"
    else:
        recovery_time = f"{recovery_idx - max_dd_idx} bars"
    
    # Add stats text box
    stats_text = f"Max Drawdown: {max_dd:.2f}%\nRecovery Time: {recovery_time}"
    ax.text(0.95, 0.05, stats_text, transform=ax.transAxes, fontsize=12,
           verticalalignment='bottom', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_title('Underwater Curve (Drawdown)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Drawdown (%)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format dates if dates are datetime objects
    if hasattr(dates[0], 'strftime'):
        fig.autofmt_xdate()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
    plt.tight_layout()
    return fig

def plot_monthly_returns_heatmap(results: Dict[str, Any], figsize: Tuple[int, int] = (14, 8)) -> plt.Figure:
    """
    Plot monthly returns heatmap
    
    Args:
        results: Dictionary with backtest results
        figsize: Figure size
        
    Returns:
        Figure object
    """
    portfolio_values = results['portfolio_values']
    dates = results.get('dates')
    
    # Need datetime dates for this analysis
    if not dates or not hasattr(dates[0], 'month'):
        print("Monthly heatmap requires datetime dates")
        return None
    
    # Calculate daily returns
    daily_returns = np.diff(portfolio_values) / portfolio_values[:-1] * 100
    
    # Create dataframe with dates and returns
    returns_df = pd.DataFrame({
        'date': dates[1:],
        'return': daily_returns
    })
    
    # Add month and year columns
    returns_df['year'] = returns_df['date'].dt.year
    returns_df['month'] = returns_df['date'].dt.month
    
    # Calculate monthly returns
    monthly_returns = returns_df.groupby(['year', 'month'])['return'].sum().unstack()
    
    # Replace month numbers with names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_returns.columns = [month_names[i-1] for i in monthly_returns.columns]
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use a diverging colormap with white at zero
    cmap = sns.diverging_palette(10, 240, as_cmap=True)
    
    # Plot heatmap
    sns.heatmap(monthly_returns, annot=True, fmt=".1f", cmap=cmap, center=0,
               linewidths=.5, ax=ax, cbar_kws={"label": "Return (%)"})
    
    ax.set_title('Monthly Returns (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Year', fontsize=12)
    
    plt.tight_layout()
    return fig

def create_interactive_equity_chart(results: Dict[str, Any], buy_hold: bool = True) -> go.Figure:
    """
    Create an interactive equity curve chart using Plotly
    
    Args:
        results: Dictionary with backtest results
        buy_hold: Whether to include buy & hold comparison
        
    Returns:
        Plotly figure object
    """
    portfolio_values = results['portfolio_values']
    dates = results.get('dates', [pd.Timestamp('2022-01-01') + pd.Timedelta(days=i) for i in range(len(portfolio_values))])
    prices = results['prices']
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add equity line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=portfolio_values,
            name="Portfolio Value",
            line=dict(color="blue", width=2)
        ),
        secondary_y=False
    )
    
    # Add price line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            name="Asset Price",
            line=dict(color="gray", width=1, dash="dot")
        ),
        secondary_y=True
    )
    
    # Add buy & hold line
    if buy_hold:
        initial_value = portfolio_values[0]
        initial_price = prices[0]
        buy_hold_values = [initial_value * (price / initial_price) for price in prices]
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=buy_hold_values,
                name="Buy & Hold",
                line=dict(color="green", width=1, dash="dash")
            ),
            secondary_y=False
        )
    
    # Add trade markers
    trades = results.get('trades', [])
    
    if trades:
        buy_dates = []
        sell_dates = []
        buy_prices = []
        sell_prices = []
        
        trade_index = 0
        for i, date in enumerate(dates):
            if trade_index < len(trades):
                trade = trades[trade_index]
                if hasattr(trade, 'get'):  # Check if it's a dictionary
                    trade_date = trade.get('timestamp')
                    
                    if trade_date == date:
                        if trade.get('action') == 'BUY':
                            buy_dates.append(date)
                            buy_prices.append(prices[i])
                        elif trade.get('action') == 'SELL':
                            sell_dates.append(date)
                            sell_prices.append(prices[i])
                        
                        trade_index += 1
        
        if buy_dates:
            fig.add_trace(
                go.Scatter(
                    x=buy_dates,
                    y=buy_prices,
                    mode='markers',
                    marker=dict(
                        symbol="triangle-up",
                        color="green",
                        size=12
                    ),
                    name="Buy"
                ),
                secondary_y=True
            )
        
        if sell_dates:
            fig.add_trace(
                go.Scatter(
                    x=sell_dates,
                    y=sell_prices,
                    mode='markers',
                    marker=dict(
                        symbol="triangle-down",
                        color="red",
                        size=12
                    ),
                    name="Sell"
                ),
                secondary_y=True
            )
    
    # Set titles
    fig.update_layout(
        title_text=f"Strategy Performance: {results['strategy_name']}",
        xaxis_title="Date",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified"
    )
    
    fig.update_yaxes(title_text="Portfolio Value", secondary_y=False)
    fig.update_yaxes(title_text="Asset Price", secondary_y=True)
    
    # Add a range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            type="date",
            rangeslider=dict(visible=True),
        )
    )
    
    return fig

def plot_strategy_comparison(results_dict: Dict[str, Dict[str, Any]], 
                            metrics: List[str] = ['total_return_percent', 'sharpe_ratio', 'max_drawdown_percent'],
                            figsize: Tuple[int, int] = (16, 10)) -> plt.Figure:
    """
    Compare multiple strategies using bar charts
    
    Args:
        results_dict: Dictionary with results for each strategy
        metrics: List of metrics to compare
        figsize: Figure size
        
    Returns:
        Figure object
    """
    # Get strategy names
    strategies = list(results_dict.keys())
    
    # Create figure
    fig, axs = plt.subplots(1, len(metrics), figsize=figsize)
    
    # Set titles for each metric
    metric_titles = {
        'total_return_percent': 'Total Return (%)',
        'sharpe_ratio': 'Sharpe Ratio',
        'max_drawdown_percent': 'Max Drawdown (%)',
        'win_rate_percent': 'Win Rate (%)',
        'profit_factor': 'Profit Factor',
        'total_trades': 'Total Trades'
    }
    
    # Plot each metric
    for i, metric in enumerate(metrics):
        values = [results_dict[strat].get(metric, 0) for strat in strategies]
        
        # Sort by metric value (highest to lowest, except for drawdown which is lowest to highest)
        if metric == 'max_drawdown_percent':
            # For drawdown, lower is better
            sorted_indices = np.argsort(values)
        else:
            # For other metrics, higher is better
            sorted_indices = np.argsort(values)[::-1]
            
        sorted_strategies = [strategies[idx] for idx in sorted_indices]
        sorted_values = [values[idx] for idx in sorted_indices]
        
        # Create color map based on performance
        if metric == 'max_drawdown_percent':
            # For drawdown, green is low values
            colors = plt.cm.RdYlGn_r(np.linspace(0, 1, len(values)))
        else:
            # For other metrics, green is high values
            colors = plt.cm.RdYlGn(np.linspace(0, 1, len(values)))
            
        # Rank colors by sorted indices
        colors = colors[sorted_indices]
        
        # Plot bar chart
        axs[i].bar(sorted_strategies, sorted_values, color=colors)
        
        # Add values on top of bars
        for j, v in enumerate(sorted_values):
            axs[i].text(j, v * 1.01, f"{v:.2f}", ha='center', fontsize=10)
        
        # Set title and grid
        axs[i].set_title(metric_titles.get(metric, metric), fontsize=14)
        axs[i].set_ylabel(metric_titles.get(metric, metric))
        axs[i].grid(axis='y', alpha=0.3)
        
        # Rotate x-axis labels if there are more than 3 strategies
        if len(strategies) > 3:
            axs[i].set_xticklabels(sorted_strategies, rotation=45, ha='right')
    
    plt.tight_layout()
    return fig

def plot_trades_analysis(results: Dict[str, Any], figsize: Tuple[int, int] = (16, 10)) -> plt.Figure:
    """
    Analyze trade statistics and performance
    
    Args:
        results: Dictionary with backtest results
        figsize: Figure size
        
    Returns:
        Figure object
    """
    positions_history = results.get('positions_history', [])
    
    if not positions_history:
        print("No trade history available for analysis")
        return None
    
    # Create dataframe for analysis
    trades_df = pd.DataFrame(positions_history)
    
    # Calculate holding time
    if 'entry_time' in trades_df.columns and 'exit_time' in trades_df.columns:
        trades_df['holding_time'] = (trades_df['exit_time'] - trades_df['entry_time']).dt.total_seconds() / 3600  # hours
    
    # Create figure
    fig, axs = plt.subplots(2, 2, figsize=figsize)
    
    # 1. Profit distribution
    sns.histplot(trades_df['profit'], kde=True, bins=30, color='blue', ax=axs[0, 0])
    axs[0, 0].axvline(x=0, color='red', linestyle='--', alpha=0.8)
    axs[0, 0].set_title('Profit Distribution', fontsize=14)
    axs[0, 0].set_xlabel('Profit/Loss ($)')
    
    # 2. Cumulative profit
    trades_df['cumulative_profit'] = trades_df['profit'].cumsum()
    axs[0, 1].plot(trades_df.index, trades_df['cumulative_profit'], color='green')
    axs[0, 1].set_title('Cumulative Profit', fontsize=14)
    axs[0, 1].set_xlabel('Trade #')
    axs[0, 1].set_ylabel('Cumulative Profit ($)')
    axs[0, 1].grid(alpha=0.3)
    
    # 3. Win/loss ratio by month if dates are available
    if 'exit_time' in trades_df.columns:
        trades_df['month'] = trades_df['exit_time'].dt.strftime('%Y-%m')
        monthly_stats = trades_df.groupby('month').agg({
            'profit': ['sum', 'count', lambda x: (x > 0).sum()],
            'profit_pct': ['mean', 'std']
        })
        monthly_stats.columns = ['total_profit', 'num_trades', 'num_wins', 'avg_return', 'std_return']
        monthly_stats['win_rate'] = monthly_stats['num_wins'] / monthly_stats['num_trades'] * 100
        
        ax = axs[1, 0]
        ax.bar(monthly_stats.index, monthly_stats['total_profit'], color='blue')
        ax2 = ax.twinx()
        ax2.plot(monthly_stats.index, monthly_stats['win_rate'], color='green', marker='o')
        
        ax.set_title('Monthly Performance', fontsize=14)
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Profit ($)', color='blue')
        ax2.set_ylabel('Win Rate (%)', color='green')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(alpha=0.3)
        
    # 4. Profit vs. holding time scatter plot (if available)
    if 'holding_time' in trades_df.columns:
        axs[1, 1].scatter(trades_df['holding_time'], trades_df['profit'], alpha=0.7,
                        c=trades_df['profit'] > 0, cmap='RdYlGn')
        axs[1, 1].set_title('Profit vs. Holding Time', fontsize=14)
        axs[1, 1].set_xlabel('Holding Time (hours)')
        axs[1, 1].set_ylabel('Profit ($)')
        axs[1, 1].grid(alpha=0.3)
    else:
        # Alternative: Profit percentage distribution
        if 'profit_pct' in trades_df.columns:
            sns.histplot(trades_df['profit_pct'], kde=True, bins=30, color='purple', ax=axs[1, 1])
            axs[1, 1].axvline(x=0, color='red', linestyle='--', alpha=0.8)
            axs[1, 1].set_title('Profit Percentage Distribution', fontsize=14)
            axs[1, 1].set_xlabel('Profit/Loss (%)')
    
    plt.tight_layout()
    return fig
