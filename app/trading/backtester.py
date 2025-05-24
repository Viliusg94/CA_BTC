"""
Backtester implementation for evaluating trading strategies
"""
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from tqdm import tqdm
from datetime import datetime
from itertools import product
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from scipy import stats

from app.trading.trading_strategies import Strategy, Action
from app.trading.indicators import add_all_indicators

logger = logging.getLogger(__name__)

class Backtester:
    """Backtester for evaluating strategies on historical data"""
    
    def __init__(self, strategy: Strategy):
        """
        Initialize the backtester
        
        Args:
            strategy: Strategy to backtest
        """
        self.strategy = strategy
    
    def run_backtest(self, df: pd.DataFrame, verbose: bool = True) -> Dict[str, Any]:
        """
        Run backtest on historical data
        
        Args:
            df: DataFrame with OHLCV data
            verbose: Whether to show progress bar and logs
            
        Returns:
            Dictionary with backtest results
        """
        if verbose:
            logger.info(f"Running backtest for strategy: {self.strategy.name}")
        start_time = datetime.now()
        
        # Reset strategy state
        self.strategy.reset()
        
        # Ensure df has a datetime index
        if not isinstance(df.index, pd.DatetimeIndex) and 'time' in df.columns:
            df = df.set_index('time')
        
        # Ensure we have all required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not in dataframe")
        
        # Add all technical indicators
        df_with_indicators = add_all_indicators(df)
        
        # Calculate signals using the strategy
        df_signals = self.strategy.calculate_signals(df_with_indicators)
        
        # Track portfolio values
        prices = []
        portfolio_values = []
        positions = []
        balances = []  # Track cash balance separately
        
        # Iterate through data points
        iterator = tqdm(df_signals.iterrows(), total=len(df_signals), desc=f"Backtesting {self.strategy.name}") if verbose else df_signals.iterrows()
        
        for i, (timestamp, row) in enumerate(iterator):
            current_price = row['close']
            current_data = row.to_dict()
            
            # Check stop loss and take profit
            if self.strategy.position:
                sl_triggered = self.strategy.check_stop_loss(current_price, timestamp)
                tp_triggered = self.strategy.check_take_profit(current_price, timestamp)
                
                if sl_triggered or tp_triggered:
                    # Skip the normal decision process since we already executed a trade
                    self.strategy.update_portfolio_value(current_price)
                    prices.append(current_price)
                    portfolio_values.append(self.strategy.portfolio_value)
                    balances.append(self.strategy.balance)
                    positions.append(1 if self.strategy.position else 0)
                    continue
            
            # Get action from strategy
            action = self.strategy.decide_action(current_data)
            
            # Execute action
            if action == Action.BUY:
                self.strategy.execute_buy(timestamp, current_price)
            elif action == Action.SELL:
                self.strategy.execute_sell(timestamp, current_price)
            
            # Update portfolio value for this timestamp
            self.strategy.update_portfolio_value(current_price)
            prices.append(current_price)
            portfolio_values.append(self.strategy.portfolio_value)
            balances.append(self.strategy.balance)
            positions.append(1 if self.strategy.position else 0)
        
        # Get final metrics
        metrics = self.strategy.get_performance_metrics()
        
        # Calculate additional metrics
        additional_metrics = self._calculate_additional_metrics(portfolio_values, prices, positions, balances)
        metrics.update(additional_metrics)
        
        # Calculate backtest duration
        end_time = datetime.now()
        backtest_duration = (end_time - start_time).total_seconds()
        
        # Create summary
        initial_price = df['close'].iloc[0]
        final_price = df['close'].iloc[-1]
        buy_hold_return = (final_price - initial_price) / initial_price * 100
        
        summary = {
            'strategy_name': self.strategy.name,
            'initial_balance': self.strategy.initial_balance,
            'final_balance': self.strategy.balance,
            'portfolio_value': self.strategy.portfolio_value,
            'total_trades': metrics['total_trades'],
            'win_rate': metrics['win_rate'],
            'win_rate_percent': metrics['win_rate_percent'],
            'profit_factor': metrics['profit_factor'],
            'total_profit': metrics['total_profit'],
            'total_return_percent': metrics['total_return_percent'],
            'max_drawdown_percent': metrics['max_drawdown_pct'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'sortino_ratio': metrics.get('sortino_ratio', 0),
            'calmar_ratio': metrics.get('calmar_ratio', 0),
            'max_consecutive_wins': metrics.get('max_consecutive_wins', 0),
            'max_consecutive_losses': metrics.get('max_consecutive_losses', 0),
            'avg_profit_per_trade': metrics.get('avg_profit_per_trade', 0),
            'avg_loss_per_trade': metrics.get('avg_loss_per_trade', 0),
            'buy_hold_return': buy_hold_return,
            'outperformance': metrics['total_return_percent'] - buy_hold_return,
            'backtest_duration': backtest_duration,
            'prices': prices,
            'portfolio_values': portfolio_values,
            'positions': positions,
            'balances': balances,
            'trades': self.strategy.trades,
            'positions_history': self.strategy.positions_history
        }
        
        if verbose:
            logger.info(f"Backtest completed for {self.strategy.name}")
            logger.info(f"Final portfolio value: ${self.strategy.portfolio_value:.2f}")
            logger.info(f"Total return: {metrics['total_return_percent']:.2f}% vs. Buy & Hold: {buy_hold_return:.2f}%")
            logger.info(f"Win rate: {metrics['win_rate_percent']:.2f}% ({metrics['total_trades']} trades)")
        
        return summary
    
    def _calculate_additional_metrics(self, portfolio_values: List[float], prices: List[float], positions: List[int], balances: List[float]) -> Dict[str, float]:
        """
        Calculate additional trading performance metrics
        
        Args:
            portfolio_values: List of portfolio values
            prices: List of prices
            positions: List of position indicators (1 for in position, 0 for no position)
            balances: List of cash balances
            
        Returns:
            Dictionary with additional performance metrics
        """
        metrics = {}
        
        # Need at least two data points for calculations
        if len(portfolio_values) < 2 or len(self.strategy.trades) == 0:
            return metrics
        
        # Calculate daily returns
        returns = np.array([(portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1] for i in range(1, len(portfolio_values))])
        
        # Sortino Ratio (using only negative returns)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_std = np.std(negative_returns)
            mean_return = np.mean(returns)
            metrics['sortino_ratio'] = (mean_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        
        # Calmar Ratio (annualized return / max drawdown)
        if metrics.get('max_drawdown_pct', 0) > 0:
            annual_return = ((portfolio_values[-1] / portfolio_values[0]) ** (252 / len(portfolio_values)) - 1) * 100
            metrics['calmar_ratio'] = annual_return / metrics.get('max_drawdown_pct', 1)
            
        # Analyze trade sequences
        if hasattr(self.strategy, 'positions_history') and self.strategy.positions_history:
            # Calculate consecutive wins/losses
            profits = [pos['profit'] for pos in self.strategy.positions_history]
            is_profit = [p > 0 for p in profits]
            
            current_streak = 1
            max_win_streak = 0
            max_loss_streak = 0
            current_is_win = None
            
            for i in range(len(is_profit)):
                if i == 0:
                    current_is_win = is_profit[i]
                    continue
                
                if is_profit[i] == current_is_win:
                    current_streak += 1
                else:
                    # Streak ended
                    if current_is_win:
                        max_win_streak = max(max_win_streak, current_streak)
                    else:
                        max_loss_streak = max(max_loss_streak, current_streak)
                    
                    # Start new streak
                    current_streak = 1
                    current_is_win = is_profit[i]
            
            # Check the final streak
            if current_is_win:
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)
                
            metrics['max_consecutive_wins'] = max_win_streak
            metrics['max_consecutive_losses'] = max_loss_streak
            
            # Calculate average profit/loss per trade
            winning_trades = [pos['profit'] for pos in self.strategy.positions_history if pos['profit'] > 0]
            losing_trades = [pos['profit'] for pos in self.strategy.positions_history if pos['profit'] <= 0]
            
            metrics['avg_profit_per_trade'] = np.mean(winning_trades) if winning_trades else 0
            metrics['avg_loss_per_trade'] = np.mean(losing_trades) if losing_trades else 0
            
        return metrics
    
    def optimize_strategy_parameters(self, df, param_grid, metric='total_return_percent', 
                                   maximize=True, n_jobs=None, cv_folds=None):
        """
        Optimize strategy parameters using grid search
        
        Args:
            df: Historical data DataFrame
            param_grid: Dictionary of parameter ranges to search
            metric: Metric to optimize ('total_return_percent', 'sharpe_ratio', etc.)
            maximize: Whether to maximize (True) or minimize (False) the metric
            n_jobs: Number of parallel jobs (-1 for all cores)
            cv_folds: Number of cross-validation folds (None for no CV)
            
        Returns:
            tuple: (best_params, best_result, all_results)
        """
        print(f"Starting parameter optimization with {len(list(itertools.product(*param_grid.values())))} combinations...")
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        # Prepare data for cross-validation if specified
        if cv_folds:
            fold_size = len(df) // cv_folds
            cv_splits = []
            for i in range(cv_folds):
                start_idx = i * fold_size
                end_idx = (i + 1) * fold_size if i < cv_folds - 1 else len(df)
                train_data = df.iloc[:start_idx].append(df.iloc[end_idx:]) if start_idx > 0 else df.iloc[end_idx:]
                test_data = df.iloc[start_idx:end_idx]
                cv_splits.append((train_data, test_data))
        
        def evaluate_params(param_combo):
            """Evaluate a single parameter combination"""
            try:
                # Create parameter dictionary
                params = dict(zip(param_names, param_combo))
                
                # Create strategy with these parameters
                strategy_class = self.strategy.__class__
                test_strategy = strategy_class(
                    name=f"{self.strategy.name}_test",
                    **params
                )
                
                if cv_folds:
                    # Cross-validation evaluation
                    cv_scores = []
                    for train_data, test_data in cv_splits:
                        if len(test_data) < 10:  # Skip if test set too small
                            continue
                        test_backtester = Backtester(test_strategy)
                        cv_result = test_backtester.run_backtest(test_data)
                        cv_scores.append(cv_result[metric])
                    
                    if cv_scores:
                        score = np.mean(cv_scores)
                        score_std = np.std(cv_scores)
                    else:
                        score = float('-inf') if maximize else float('inf')
                        score_std = 0
                else:
                    # Single evaluation on full dataset
                    test_backtester = Backtester(test_strategy)
                    result = test_backtester.run_backtest(df)
                    score = result[metric]
                    score_std = 0
                
                return {
                    'params': params,
                    'score': score,
                    'score_std': score_std,
                    'param_combo': param_combo
                }
            except Exception as e:
                print(f"Error evaluating params {param_combo}: {str(e)}")
                return {
                    'params': dict(zip(param_names, param_combo)),
                    'score': float('-inf') if maximize else float('inf'),
                    'score_std': 0,
                    'param_combo': param_combo
                }
        
        # Parallel evaluation
        if n_jobs is None:
            n_jobs = min(4, mp.cpu_count() - 1)  # Conservative default
        
        if n_jobs == 1:
            # Sequential processing
            results = [evaluate_params(combo) for combo in param_combinations]
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                results = list(executor.map(evaluate_params, param_combinations))
        
        # Find best parameters
        if maximize:
            best_result = max(results, key=lambda x: x['score'])
        else:
            best_result = min(results, key=lambda x: x['score'])
        
        best_params = best_result['params']
        
        # Run full backtest with best parameters
        final_strategy = self.strategy.__class__(
            name=f"{self.strategy.name}_optimized",
            **best_params
        )
        final_backtester = Backtester(final_strategy)
        final_backtest_result = final_backtester.run_backtest(df)
        
        print(f"Optimization completed. Best {metric}: {best_result['score']:.4f}")
        print(f"Best parameters: {best_params}")
        
        return best_params, final_backtest_result, results
    
    def parameter_sensitivity_analysis(self, df, base_params, param_ranges, 
                                     metric='total_return_percent', steps=10):
        """
        Analyze sensitivity of strategy performance to parameter changes
        
        Args:
            df: Historical data DataFrame
            base_params: Base parameter set
            param_ranges: Dictionary of parameter ranges for sensitivity analysis
            metric: Metric to analyze
            steps: Number of steps to test for each parameter
            
        Returns:
            dict: Sensitivity analysis results
        """
        sensitivity_results = {}
        
        for param_name, (min_val, max_val) in param_ranges.items():
            print(f"Analyzing sensitivity for parameter: {param_name}")
            
            # Generate parameter values to test
            if isinstance(min_val, int) and isinstance(max_val, int):
                test_values = np.linspace(min_val, max_val, steps, dtype=int)
            else:
                test_values = np.linspace(min_val, max_val, steps)
            
            param_scores = []
            param_values = []
            
            for test_value in test_values:
                # Create test parameters
                test_params = base_params.copy()
                test_params[param_name] = test_value
                
                try:
                    # Create and test strategy
                    strategy_class = self.strategy.__class__
                    test_strategy = strategy_class(
                        name=f"{self.strategy.name}_sensitivity",
                        **test_params
                    )
                    
                    test_backtester = Backtester(test_strategy)
                    result = test_backtester.run_backtest(df)
                    
                    param_scores.append(result[metric])
                    param_values.append(test_value)
                    
                except Exception as e:
                    print(f"Error testing {param_name}={test_value}: {str(e)}")
                    param_scores.append(0)
                    param_values.append(test_value)
            
            # Calculate sensitivity metrics
            correlation = stats.pearsonr(param_values, param_scores)[0]
            sensitivity = (max(param_scores) - min(param_scores)) / (max_val - min_val)
            
            sensitivity_results[param_name] = {
                'param_values': param_values,
                'scores': param_scores,
                'correlation': correlation,
                'sensitivity': sensitivity,
                'optimal_value': param_values[np.argmax(param_scores)],
                'optimal_score': max(param_scores)
            }
        
        return sensitivity_results
    
    def plot_results(self, results: Dict[str, Any], buy_hold: bool = True, show_trades: bool = True) -> None:
        """
        Plot backtest results
        
        Args:
            results: Dictionary with backtest results
            buy_hold: Whether to plot buy & hold comparison
            show_trades: Whether to show trade markers
        """
        if not isinstance(results, dict) or 'portfolio_values' not in results or 'prices' not in results:
            logger.error("Invalid results for plotting")
            return

        # Extract data
        portfolio_values = results['portfolio_values']
        prices = results['prices']
        trades = results.get('trades', [])
        
        # Create figure and primary axis for portfolio value
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot portfolio value
        ax1.plot(portfolio_values, label='Portfolio Value', color='blue')
        ax1.set_xlabel('Bar')
        ax1.set_ylabel('Portfolio Value ($)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        
        # Create a secondary y-axis for asset price
        ax2 = ax1.twinx()
        ax2.plot(prices, label='Asset Price', color='gray', alpha=0.6)
        ax2.set_ylabel('Asset Price ($)', color='gray')
        ax2.tick_params(axis='y', labelcolor='gray')
        
        # Plot buy & hold for comparison
        if buy_hold:
            initial_investment = results['initial_balance']
            initial_price = prices[0]
            buy_hold_values = [initial_investment * (price / initial_price) for price in prices]
            ax1.plot(buy_hold_values, label='Buy & Hold', color='green', linestyle='--', alpha=0.7)
        
        # Show trade markers
        if show_trades and trades:
            buy_indices = []
            sell_indices = []
            
            for i, trade in enumerate(trades):
                if trade['action'] == 'BUY':
                    buy_indices.append(i)
                elif trade['action'] == 'SELL':
                    sell_indices.append(i)
            
            if buy_indices:
                ax2.scatter(buy_indices, [prices[i] for i in buy_indices], color='green', marker='^', s=100, label='Buy')
            
            if sell_indices:
                ax2.scatter(sell_indices, [prices[i] for i in sell_indices], color='red', marker='v', s=100, label='Sell')
        
        # Add title and legend
        plt.title(f"Backtest Results: {results['strategy_name']}", fontsize=14)
        
        # Combine legends from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        plt.show()
        
        # Plot additional charts
        self._plot_drawdown(results)
        self._plot_returns_distribution(results)
        
    def _plot_drawdown(self, results: Dict[str, Any]) -> None:
        """
        Plot drawdown chart
        
        Args:
            results: Dictionary with backtest results
        """
        portfolio_values = results['portfolio_values']
        
        # Calculate drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak * 100
        
        plt.figure(figsize=(12, 4))
        plt.plot(drawdown, color='red', alpha=0.8)
        plt.fill_between(range(len(drawdown)), drawdown, 0, color='red', alpha=0.1)
        plt.title('Portfolio Drawdown (%)', fontsize=14)
        plt.ylabel('Drawdown (%)')
        plt.xlabel('Bar')
        plt.tight_layout()
        plt.show()
        
    def _plot_returns_distribution(self, results: Dict[str, Any]) -> None:
        """
        Plot returns distribution
        
        Args:
            results: Dictionary with backtest results
        """
        portfolio_values = results['portfolio_values']
        
        # Calculate returns
        returns = np.diff(portfolio_values) / portfolio_values[:-1] * 100
        
        plt.figure(figsize=(12, 4))
        sns.histplot(returns, kde=True, bins=50, color='blue')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.8)
        plt.title('Daily Returns Distribution (%)', fontsize=14)
        plt.xlabel('Return (%)')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.show()
        
    def compare_strategies(self, strategies: List[Strategy], df: pd.DataFrame, 
                          plot: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple strategies on the same data
        
        Args:
            strategies: List of strategies to compare
            df: DataFrame with OHLCV data
            plot: Whether to plot the comparison
            
        Returns:
            Dictionary with results for each strategy
        """
        results = {}
        
        for strategy in tqdm(strategies, desc="Comparing Strategies"):
            backtester = Backtester(strategy)
            result = backtester.run_backtest(df, verbose=False)
            results[strategy.name] = result
        
        # Print comparison table
        comparison = []
        for name, result in results.items():
            comparison.append({
                'Strategy': name,
                'Total Return (%)': result['total_return_percent'],
                'Sharpe Ratio': result['sharpe_ratio'],
                'Max Drawdown (%)': result['max_drawdown_percent'],
                'Win Rate (%)': result['win_rate_percent'],
                'Profit Factor': result['profit_factor'],
                'Total Trades': result['total_trades']
            })
        
        comparison_df = pd.DataFrame(comparison).sort_values('Total Return (%)', ascending=False)
        print("Strategy Comparison:")
        print(comparison_df)
        
        # Plot comparison
        if plot:
            self._plot_strategy_comparison(results)
        
        return results
    
    def _plot_strategy_comparison(self, results: Dict[str, Dict[str, Any]]) -> None:
        """
        Plot comparison of multiple strategies
        
        Args:
            results: Dictionary with results for each strategy
        """
        # Prepare data for plotting
        portfolio_values = {}
        for name, result in results.items():
            # Normalize to start from 100% for fair comparison
            initial_value = result['portfolio_values'][0]
            normalized_values = [value / initial_value * 100 for value in result['portfolio_values']]
            portfolio_values[name] = normalized_values
        
        # Plot portfolio values
        plt.figure(figsize=(12, 6))
        
        for name, values in portfolio_values.items():
            plt.plot(values, label=name)
        
        # Calculate buy & hold based on the first strategy (assumes same data)
        first_result = list(results.values())[0]
        initial_price = first_result['prices'][0]
        final_price = first_result['prices'][-1]
        buy_hold_return = final_price / initial_price * 100
        plt.axhline(y=buy_hold_return, color='gray', linestyle='--', alpha=0.8, label='Buy & Hold')
        
        plt.title('Strategy Comparison (Normalized to 100%)', fontsize=14)
        plt.ylabel('Portfolio Value (%)')
        plt.xlabel('Bar')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        # Bar chart comparison of key metrics
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Total return
        returns = {name: result['total_return_percent'] for name, result in results.items()}
        axes[0, 0].bar(returns.keys(), returns.values())
        axes[0, 0].set_title('Total Return (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Sharpe ratio
        sharpe_ratios = {name: result['sharpe_ratio'] for name, result in results.items()}
        axes[0, 1].bar(sharpe_ratios.keys(), sharpe_ratios.values())
        axes[0, 1].set_title('Sharpe Ratio')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Max drawdown
        drawdowns = {name: result['max_drawdown_percent'] for name, result in results.items()}
        axes[1, 0].bar(drawdowns.keys(), drawdowns.values())
        axes[1, 0].set_title('Max Drawdown (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Win rate
        win_rates = {name: result['win_rate_percent'] for name, result in results.items()}
        axes[1, 1].bar(win_rates.keys(), win_rates.values())
        axes[1, 1].set_title('Win Rate (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def plot_optimization_results(self, optimization_results, param_grid, metric='total_return_percent'):
        """
        Visualize optimization results
        
        Args:
            optimization_results: Results from optimize_strategy_parameters
            param_grid: Original parameter grid
            metric: Metric that was optimized
        """
        results = optimization_results[2]  # All results
        
        # Convert results to DataFrame
        results_data = []
        for result in results:
            row = result['params'].copy()
            row[metric] = result['score']
            results_data.append(row)
        
        df_results = pd.DataFrame(results_data)
        
        # Determine grid layout
        param_names = list(param_grid.keys())
        n_params = len(param_names)
        
        if n_params == 1:
            # Single parameter plot
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            param_name = param_names[0]
            
            plt.scatter(df_results[param_name], df_results[metric], alpha=0.6)
            plt.xlabel(param_name)
            plt.ylabel(metric)
            plt.title(f'{metric} vs {param_name}')
            plt.grid(True, alpha=0.3)
            
        elif n_params == 2:
            # 2D heatmap
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            param1, param2 = param_names[0], param_names[1]
            pivot_table = df_results.pivot_table(
                values=metric, 
                index=param2, 
                columns=param1, 
                aggfunc='mean'
            )
            
            sns.heatmap(pivot_table, annot=True, fmt='.3f', cmap='viridis', ax=ax)
            plt.title(f'{metric} Heatmap: {param1} vs {param2}')
            
        else:
            # Multiple subplot grid for many parameters
            n_cols = min(3, n_params)
            n_rows = (n_params + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
            if n_rows == 1:
                axes = [axes] if n_cols == 1 else axes
            else:
                axes = axes.flatten()
            
            for i, param_name in enumerate(param_names):
                ax = axes[i] if n_params > 1 else axes
                
                # Group by parameter and show distribution
                param_groups = df_results.groupby(param_name)[metric]
                means = param_groups.mean()
                stds = param_groups.std()
                
                ax.errorbar(means.index, means.values, yerr=stds.values, 
                           marker='o', capsize=5, capthick=2)
                ax.set_xlabel(param_name)
                ax.set_ylabel(metric)
                ax.set_title(f'{metric} vs {param_name}')
                ax.grid(True, alpha=0.3)
            
            # Hide empty subplots
            for i in range(n_params, len(axes)):
                axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.show()
        
        # Summary statistics
        print(f"\nOptimization Results Summary:")
        print(f"Best {metric}: {df_results[metric].max():.4f}")
        print(f"Worst {metric}: {df_results[metric].min():.4f}")
        print(f"Mean {metric}: {df_results[metric].mean():.4f}")
        print(f"Std {metric}: {df_results[metric].std():.4f}")
    
    def plot_sensitivity_analysis(self, sensitivity_results, metric='total_return_percent'):
        """
        Visualize parameter sensitivity analysis results
        
        Args:
            sensitivity_results: Results from parameter_sensitivity_analysis
            metric: Metric that was analyzed
        """
        n_params = len(sensitivity_results)
        n_cols = min(3, n_params)
        n_rows = (n_params + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes
        else:
            axes = axes.flatten()
        
        for i, (param_name, results) in enumerate(sensitivity_results.items()):
            ax = axes[i] if n_params > 1 else axes[0]
            
            param_values = results['param_values']
            scores = results['scores']
            correlation = results['correlation']
            optimal_value = results['optimal_value']
            optimal_score = results['optimal_score']
            
            # Plot parameter vs score
            ax.plot(param_values, scores, 'b-', marker='o', markersize=4)
            ax.axvline(optimal_value, color='red', linestyle='--', alpha=0.7, 
                      label=f'Optimal: {optimal_value:.3f}')
            ax.axhline(optimal_score, color='red', linestyle='--', alpha=0.7)
            
            ax.set_xlabel(param_name)
            ax.set_ylabel(metric)
            ax.set_title(f'{param_name} Sensitivity\nCorr: {correlation:.3f}')
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        # Hide empty subplots
        for i in range(n_params, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.show()
        
        # Create sensitivity ranking
        sensitivity_ranking = []
        for param_name, results in sensitivity_results.items():
            sensitivity_ranking.append({
                'parameter': param_name,
                'sensitivity': abs(results['sensitivity']),
                'correlation': abs(results['correlation']),
                'optimal_value': results['optimal_value']
            })
        
        sensitivity_df = pd.DataFrame(sensitivity_ranking)
        sensitivity_df = sensitivity_df.sort_values('sensitivity', ascending=False)
        
        print(f"\nParameter Sensitivity Ranking:")
        print(sensitivity_df.to_string(index=False))
        
        # Plot sensitivity ranking
        plt.figure(figsize=(10, 6))
        bars = plt.bar(sensitivity_df['parameter'], sensitivity_df['sensitivity'])
        plt.xlabel('Parameter')
        plt.ylabel('Sensitivity Score')
        plt.title('Parameter Sensitivity Ranking')
        plt.xticks(rotation=45)
        
        # Add correlation as bar color
        colors = plt.cm.RdYlBu_r(sensitivity_df['correlation'] / sensitivity_df['correlation'].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        plt.colorbar(plt.cm.ScalarMappable(cmap='RdYlBu_r'), 
                    label='Absolute Correlation')
        plt.tight_layout()
        plt.show()
        
        return sensitivity_df
