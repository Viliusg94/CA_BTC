from flask import Blueprint, render_template, request, jsonify, session
from app.trading.binance_api import get_candlestick_data
import logging

# Inicializuojame logger
logger = logging.getLogger(__name__)

# Inicializuojame trading maršrutus
trading = Blueprint('trading', __name__, url_prefix='/trading')

@trading.route('/')
def index():
    """
    Prekybos pradinis puslapis
    """
    return render_template('trading/index.html')

@trading.route('/candlestick')
def candlestick():
    """
    Žvakių grafiko puslapis
    """
    return render_template('trading/candlestick.html')

@trading.route('/charts')
def charts():
    """
    Grafikų analizės puslapis
    """
    return render_template('trading/charts.html')

@trading.route('/simulate')
def simulate():
    """
    Prekybos simuliacijos puslapis
    """
    return render_template('trading/simulate.html')

# API endpoint žvakių grafiko duomenims
@trading.route('/api/candlestick_data')
def candlestick_data_api():
    """API endpoint žvakių grafiko duomenims"""
    timeframe = request.args.get('timeframe', '1m')
    interval = request.args.get('interval', '1d')
    
    try:
        data = get_candlestick_data(timeframe, interval)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Klaida gaunant žvakių duomenis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trading.route('/activate_strategy', methods=['POST'])
def activate_strategy():
    """Activate a trading strategy by type"""
    try:
        data = request.form or request.json
        
        # Get strategy type
        strategy_type = data.get('strategy_type')
        if not strategy_type:
            return jsonify({'success': False, 'error': 'No strategy type specified'}), 400
            
        # Check if strategy exists
        if strategy_type not in STRATEGY_REGISTRY:
            return jsonify({'success': False, 'error': f'Unknown strategy type: {strategy_type}'}), 400
            
        # Get strategy configuration
        config = data.get('config', {})
        strategy_params = {
            'name': config.get('name', f"{strategy_type} Strategy"),
            'initial_balance': float(config.get('initial_balance', 10000)),
            'fee_rate': float(config.get('fee_rate', 0.001))
        }
        
        # Add strategy-specific parameters
        if strategy_type == 'moving_average':
            strategy_params.update({
                'short_period': int(config.get('ma_short_period', 10)),
                'long_period': int(config.get('ma_long_period', 30))
            })
        elif strategy_type == 'prediction_based':
            strategy_params.update({
                'threshold_percent': float(config.get('prediction_threshold', 1.0)),
                'max_holding_days': int(config.get('prediction_max_days', 3))
            })
        elif strategy_type == 'ensemble':
            # Ensemble strategy combines multiple strategies
            ma_strategy = MovingAverageStrategy(
                name='MA Sub-strategy',
                initial_balance=float(config.get('initial_balance', 10000)),
                fee_rate=float(config.get('fee_rate', 0.001)),
                short_period=int(config.get('ma_short_period', 10)),
                long_period=int(config.get('ma_long_period', 30))
            )
            
            pred_strategy = PredictionBasedStrategy(
                name='Prediction Sub-strategy',
                initial_balance=float(config.get('initial_balance', 10000)),
                fee_rate=float(config.get('fee_rate', 0.001)),
                threshold_percent=float(config.get('prediction_threshold', 1.0)),
                max_holding_days=int(config.get('prediction_max_days', 3))
            )
            
            # Set up combined strategy
            strategy_params['strategies'] = [ma_strategy, pred_strategy]
            strategy_params['weights'] = [
                float(config.get('ma_weight', 0.5)),
                float(config.get('prediction_weight', 0.5))
            ]
        
        # Create the strategy
        strategy_class = STRATEGY_REGISTRY[strategy_type]
        strategy = strategy_class(**strategy_params)
        
        # Set as active strategy
        global active_strategy, active_config
        active_strategy = strategy
        active_config = config
        
        # Store in database if available
        try:
            from app.models import db, TradingStrategy
            
            # Store in database
            db_strategy = TradingStrategy(
                name=strategy.name,
                strategy_type=strategy_type,
                config=json.dumps(config),
                is_active=True
            )
            
            # Deactivate other strategies
            TradingStrategy.query.update({'is_active': False})
            
            # Save new strategy
            db.session.add(db_strategy)
            db.session.commit()
            
            logger.info(f"Strategy {strategy_type} activated and saved to database")
            
            return jsonify({
                'success': True,
                'message': 'Strategy activated successfully',
                'strategy_id': db_strategy.id
            })
            
        except Exception as e:
            logger.error(f"Error saving strategy to database: {e}")
            # Continue with in-memory activation
        
        return jsonify({
            'success': True,
            'message': 'Strategy activated in memory only (database unavailable)',
            'strategy_type': strategy_type,
            'config': config
        })
    except Exception as e:
        logger.error(f"Error activating strategy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@trading.route('/strategies')
def list_strategies():
    """List all available trading strategies"""
    try:
        strategies = []
        
        # Add built-in strategies
        for strategy_id, strategy_class in STRATEGY_REGISTRY.items():
            strategies.append({
                'id': strategy_id,
                'name': strategy_id.replace('_', ' ').title(),
                'description': strategy_class.__doc__ or 'No description available'
            })
        
        # Check if database is available and add custom strategies
        try:
            from app.models import TradingStrategy
            custom_strategies = TradingStrategy.query.all()
            for strat in custom_strategies:
                strategies.append({
                    'id': f"custom_{strat.id}",
                    'name': strat.name,
                    'description': 'Custom strategy',
                    'is_custom': True,
                    'is_active': strat.is_active,
                    'created_at': strat.created_at.isoformat() if hasattr(strat, 'created_at') else None
                })
        except Exception as e:
            logger.error(f"Error loading strategies from database: {e}")
        
        return jsonify({
            'success': True,
            'strategies': strategies
        })
        
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trading.route('/execute', methods=['POST'])
def execute_trade():
    """Manually execute a trade with the active strategy"""
    try:
        # Get request data
        data = request.form or request.json
        action = data.get('action')
        
        # Validate action
        if action not in ['buy', 'sell']:
            return jsonify({'success': False, 'error': 'Invalid action (must be buy or sell)'}), 400
            
        # Check if we have an active strategy
        global active_strategy
        if active_strategy is None:
            return jsonify({'success': False, 'error': 'No active trading strategy'}), 400
            
        # Get current price
        current_price = get_real_bitcoin_price()
        if current_price is None:
            return jsonify({'success': False, 'error': 'Could not get current price'}), 500
            
        # Execute the trade
        action_enum = Action.BUY if action == 'buy' else Action.SELL
        percentage = float(data.get('percentage', 1.0))
        
        trade = active_strategy.execute_trade(
            action=action_enum,
            timestamp=datetime.now(),
            price=current_price,
            percentage=percentage
        )
        
        if trade is None:
            return jsonify({
                'success': False,
                'error': f"Could not execute {action} trade. Check balances and try again."
            }), 400
            
        # Return the result
        return jsonify({
            'success': True,
            'trade': trade.to_dict(),
            'balance_usd': active_strategy.balance_usd,
            'balance_btc': active_strategy.balance_btc,
            'message': f"{action.title()} trade executed successfully"
        })
            
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@trading.route('/status')
def trading_status():
    """Get current trading status including portfolio value and performance metrics"""
    try:
        # Check if we have an active strategy
        global active_strategy
        if active_strategy is None:
            return jsonify({
                'success': False,
                'error': 'No active trading strategy',
                'status': 'inactive'
            }), 400
            
        # Get current Bitcoin price
        current_price = get_real_bitcoin_price()
        if current_price is None:
            return jsonify({
                'success': False,
                'error': 'Could not get current Bitcoin price',
                'status': 'error'
            }), 500
            
        # Calculate portfolio value
        portfolio_usd = active_strategy.balance_usd
        portfolio_btc = active_strategy.balance_btc
        portfolio_btc_value = portfolio_btc * current_price
        total_value = portfolio_usd + portfolio_btc_value
        
        # Get trade history
        trades = active_strategy.trade_history
        
        # Calculate basic performance metrics
        trade_count = len(trades)
        profitable_trades = sum(1 for trade in trades if trade.profit > 0)
        profit_percentage = (profitable_trades / trade_count * 100) if trade_count > 0 else 0
        
        # Calculate total profit
        total_profit = sum(trade.profit for trade in trades) if trades else 0
        
        # Get current positions
        current_positions = []
        if portfolio_btc > 0:
            current_positions.append({
                'asset': 'BTC',
                'amount': portfolio_btc,
                'value_usd': portfolio_btc_value,
                'avg_entry_price': active_strategy.get_average_entry_price() if hasattr(active_strategy, 'get_average_entry_price') else None,
                'unrealized_profit': portfolio_btc_value - (active_strategy.get_position_cost() if hasattr(active_strategy, 'get_position_cost') else 0)
            })
        
        # Get recent signals
        recent_signals = active_strategy.recent_signals[-10:] if hasattr(active_strategy, 'recent_signals') else []
        
        # Get strategy config
        global active_config
        
        # Return the result
        return jsonify({
            'success': True,
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'strategy': {
                'name': active_strategy.name,
                'type': active_strategy.__class__.__name__,
                'config': active_config
            },
            'market': {
                'current_price': current_price
            },
            'portfolio': {
                'total_value_usd': total_value,
                'balance_usd': portfolio_usd,
                'balance_btc': portfolio_btc,
                'btc_value_usd': portfolio_btc_value
            },
            'positions': current_positions,
            'performance': {
                'trade_count': trade_count,
                'profitable_trades': profitable_trades,
                'profit_percentage': profit_percentage,
                'total_profit': total_profit
            },
            'recent_signals': [{
                'timestamp': signal.timestamp.isoformat() if isinstance(signal.timestamp, datetime) else signal.timestamp,
                'action': signal.action.name if hasattr(signal.action, 'name') else signal.action,
                'price': signal.price,
                'confidence': signal.confidence if hasattr(signal, 'confidence') else None
            } for signal in recent_signals],
            'recent_trades': [{
                'timestamp': trade.timestamp.isoformat() if isinstance(trade.timestamp, datetime) else trade.timestamp,
                'action': trade.action.name if hasattr(trade.action, 'name') else trade.action,
                'price': trade.price,
                'amount': trade.amount,
                'profit': trade.profit
            } for trade in trades[-5:]] if trades else []
        })
            
    except Exception as e:
        logger.error(f"Error getting trading status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@trading.route('/history')
def trade_history():
    """Get trading history with filtering and pagination"""
    try:
        # Check if we have an active strategy
        global active_strategy
        if active_strategy is None:
            return jsonify({
                'success': False, 
                'error': 'No active trading strategy',
                'trades': []
            }), 400
            
        # Get query parameters for filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action = request.args.get('action')  # 'buy' or 'sell'
        
        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get all trades from the active strategy
        all_trades = active_strategy.trade_history
        
        # Apply filters
        filtered_trades = all_trades
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            filtered_trades = [t for t in filtered_trades if t.timestamp >= start_dt]
            
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            filtered_trades = [t for t in filtered_trades if t.timestamp <= end_dt]
            
        if action:
            action_enum = None
            if action.lower() == 'buy':
                action_enum = Action.BUY
            elif action.lower() == 'sell':
                action_enum = Action.SELL
                
            if action_enum:
                filtered_trades = [t for t in filtered_trades if t.action == action_enum]
        
        # Calculate total count for pagination
        total_count = len(filtered_trades)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_trades = filtered_trades[start_idx:end_idx]
        
        # Calculate performance metrics
        total_profit = sum(t.profit for t in filtered_trades)
        winning_trades = sum(1 for t in filtered_trades if t.profit > 0)
        losing_trades = sum(1 for t in filtered_trades if t.profit < 0)
        win_rate = winning_trades / total_count if total_count > 0 else 0
        
        # Calculate average profit and loss
        profits = [t.profit for t in filtered_trades if t.profit > 0]
        losses = [t.profit for t in filtered_trades if t.profit < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = abs(sum(profits) / sum(losses)) if sum(losses) else float('inf')
        
        # Prepare serialized trades for response
        trades_data = [t.to_dict() for t in paginated_trades]
        
        # Return paginated results with metadata
        return jsonify({
            'success': True,
            'trades': trades_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'metrics': {
                'total_trades': total_count,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving trade history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_real_bitcoin_price():
    """Get current Bitcoin price from CoinGecko API"""
    try:
        from app.utils.bitcoin_api import get_real_bitcoin_price as api_get_price
        return api_get_price()
    except ImportError:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data["bitcoin"]["usd"]
        except Exception as e:
            logger.error(f"Error getting Bitcoin price: {e}")
            return None

@trading.route('/optimize', methods=['POST'])
def optimize_strategy():
    """Optimize trading strategy parameters using grid search"""
    try:
        # Get request data
        data = request.form or request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        # Get strategy type and optimization parameters
        strategy_type = data.get('strategy_type')
        optimization_method = data.get('optimization_method', 'grid_search')
        param_grid = data.get('param_grid', {})
        metric = data.get('optimization_metric', 'profit')
        test_data_days = int(data.get('test_data_days', 30))
        max_combinations = int(data.get('max_combinations', 50))
        
        # Validate inputs
        if not strategy_type:
            return jsonify({'success': False, 'error': 'No strategy type specified'}), 400
            
        if strategy_type not in STRATEGY_REGISTRY:
            return jsonify({'success': False, 'error': f'Unknown strategy type: {strategy_type}'}), 400
            
        if not param_grid:
            return jsonify({'success': False, 'error': 'No parameter grid provided'}), 400
        
        logger.info(f"Starting optimization for {strategy_type} strategy using {optimization_method}")
        logger.info(f"Parameter grid: {param_grid}")
        
        # Get historical data for backtesting
        historical_data = get_historical_klines(days=test_data_days)
        if not historical_data or len(historical_data) < 100:
            return jsonify({
                'success': False, 
                'error': 'Insufficient historical data for optimization'
            }), 400
            
        # Perform grid search
        results = []
        
        # Create parameter combinations
        param_combinations = []
        if optimization_method == 'grid_search':
            param_combinations = create_parameter_grid(param_grid)
            # Limit the number of combinations to prevent excessive computation
            if len(param_combinations) > max_combinations:
                logger.warning(f"Too many parameter combinations ({len(param_combinations)}), limiting to {max_combinations}")
                import random
                random.shuffle(param_combinations)
                param_combinations = param_combinations[:max_combinations]
        elif optimization_method == 'random_search':
            param_combinations = create_random_search(param_grid, n_iter=max_combinations)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported optimization method: {optimization_method}'
            }), 400
        
        logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        # Evaluate each combination
        for params in param_combinations:
            try:
                # Create strategy with the current parameters
                strategy_params = {
                    'name': f"{strategy_type} test strategy",
                    'initial_balance': float(data.get('initial_balance', 10000)),
                    'fee_rate': float(data.get('fee_rate', 0.001)),
                    **params
                }
                
                # Create the strategy
                strategy_class = STRATEGY_REGISTRY[strategy_type]
                strategy = strategy_class(**strategy_params)
                
                # Backtest the strategy
                backtest_result = backtest_strategy(strategy, historical_data)
                
                # Add result with parameters
                result = {
                    'parameters': params,
                    'profit': backtest_result['final_balance'] - strategy.initial_balance,
                    'profit_percent': (backtest_result['final_balance'] / strategy.initial_balance - 1) * 100,
                    'win_rate': backtest_result.get('win_rate', 0),
                    'trades': backtest_result.get('total_trades', 0),
                    'max_drawdown': backtest_result.get('max_drawdown', 0)
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error evaluating parameter combination {params}: {e}")
                continue
        
        # Sort results based on the chosen metric
        if metric == 'profit':
            results.sort(key=lambda x: x['profit'], reverse=True)
        elif metric == 'win_rate':
            results.sort(key=lambda x: x['win_rate'], reverse=True)
        elif metric == 'max_drawdown':
            results.sort(key=lambda x: x['max_drawdown'])
        
        # Get best parameters
        best_result = results[0] if results else None
        
        # Create performance visualizations
        visualizations = create_optimization_visualizations(results, param_grid)
        
        return jsonify({
            'success': True,
            'message': f'Strategy optimization completed with {len(results)} evaluations',
            'best_parameters': best_result['parameters'] if best_result else None,
            'best_performance': {
                'profit': best_result['profit'] if best_result else None,
                'profit_percent': best_result['profit_percent'] if best_result else None,
                'win_rate': best_result['win_rate'] if best_result else None,
                'trades': best_result['trades'] if best_result else None,
                'max_drawdown': best_result['max_drawdown'] if best_result else None,
            } if best_result else None,
            'all_results': results[:10],  # Return only top 10 to avoid huge responses
            'total_combinations_tested': len(results),
            'visualizations': visualizations
        })
        
    except Exception as e:
        logger.error(f"Error in strategy optimization: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

def create_parameter_grid(param_grid):
    """Create all combinations of parameters for grid search"""
    import itertools
    
    # Extract all parameter combinations
    param_names = sorted(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    
    # Generate combinations
    combinations = []
    for values in itertools.product(*param_values):
        combination = {name: value for name, value in zip(param_names, values)}
        combinations.append(combination)
    
    return combinations

def create_random_search(param_grid, n_iter=10):
    """Create random combinations of parameters for random search"""
    import random
    
    combinations = []
    param_names = sorted(param_grid.keys())
    
    for _ in range(n_iter):
        combination = {}
        for name in param_names:
            values = param_grid[name]
            combination[name] = random.choice(values)
        combinations.append(combination)
    
    return combinations

def backtest_strategy(strategy, historical_data):
    """Backtest a strategy on historical data"""
    from app.trading.backtester import Backtester
    
    try:
        backtester = Backtester(strategy)
        result = backtester.run_backtest(historical_data)
        return result
    except ImportError:
        # If backtester module not available, do a simple backtest
        return simple_backtest(strategy, historical_data)

def simple_backtest(strategy, historical_data):
    """Simple backtest implementation if full backtester not available"""
    from datetime import datetime
    
    # Reset strategy
    strategy.reset()
    
    # Track metrics
    winning_trades = 0
    total_trades = 0
    portfolio_values = []
    max_portfolio_value = strategy.initial_balance
    
    # Process each data point
    for i in range(len(historical_data)):
        data_point = historical_data.iloc[i]
        
        # Create signal from data point
        signal = strategy.generate_signal(
            timestamp=data_point.time,
            open_price=float(data_point.open),
            high_price=float(data_point.high),
            low_price=float(data_point.low),
            close_price=float(data_point.close),
            volume=float(data_point.volume)
        )
        
        # Execute trade based on signal
        if signal and signal.action != Action.HOLD:
            trade = strategy.execute_trade(
                action=signal.action,
                timestamp=data_point.time,
                price=float(data_point.close),
            )
            
            if trade:
                total_trades += 1
                if trade.profit > 0:
                    winning_trades += 1
        
        # Track portfolio value
        portfolio_value = strategy.balance_usd + strategy.balance_btc * float(data_point.close)
        portfolio_values.append(portfolio_value)
        
        # Update max portfolio value for drawdown calculation
        max_portfolio_value = max(max_portfolio_value, portfolio_value)
    
    # Calculate win rate
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Calculate max drawdown
    max_drawdown = 0
    for value in portfolio_values:
        drawdown = (max_portfolio_value - value) / max_portfolio_value * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    # Return backtest results
    return {
        'final_balance': strategy.balance_usd + strategy.balance_btc * historical_data.iloc[-1].close,
        'initial_balance': strategy.initial_balance,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'max_drawdown': max_drawdown
    }

def create_optimization_visualizations(results, param_grid):
    """Create visualizations of optimization results"""
    if not results:
        return None
        
    # Extract parameter names
    param_names = sorted(param_grid.keys())
    if len(param_names) < 1:
        return None
        
    # Create visualizations for each parameter
    visualizations = {}
    
    for param in param_names:
        # Group results by this parameter
        param_values = sorted(set(result['parameters'][param] for result in results))
        
        # Calculate average profit for each parameter value
        profits = []
        for value in param_values:
            matching_results = [r for r in results if r['parameters'][param] == value]
            avg_profit = sum(r['profit'] for r in matching_results) / len(matching_results)
            profits.append(avg_profit)
        
        # Create data points for line chart
        visualizations[param] = {
            'type': 'line',
            'data': {
                'labels': [str(v) for v in param_values],
                'datasets': [{
                    'label': f'Profit by {param}',
                    'data': profits,
                    'fill': False,
                    'borderColor': 'rgb(75, 192, 192)',
                    'tension': 0.1
                }]
            }
        }
        
    # If we have exactly 2 parameters, create a heat map
    if len(param_names) == 2:
        param1, param2 = param_names
        param1_values = sorted(set(result['parameters'][param1] for result in results))
        param2_values = sorted(set(result['parameters'][param2] for result in results))
        
        # Create 2D array for heatmap
        heatmap_data = []
        for val1 in param1_values:
            row = []
            for val2 in param2_values:
                matching_results = [r for r in results 
                                  if r['parameters'][param1] == val1 
                                  and r['parameters'][param2] == val2]
                avg_profit = sum(r['profit'] for r in matching_results) / len(matching_results) if matching_results else 0
                row.append(avg_profit)
            heatmap_data.append(row)
        
        visualizations['heatmap'] = {
            'type': 'heatmap',
            'data': {
                'labels': {
                    'x': [str(v) for v in param2_values],
                    'y': [str(v) for v in param1_values]
                },
                'values': heatmap_data
            },
            'params': {
                'x': param2,
                'y': param1
            }
        }
    
    return visualizations

@trading.route('/backtest', methods=['POST'])
def run_backtest():
    """Run a backtest of a trading strategy on historical data"""
    try:
        # Get request data
        data = request.form or request.json
        
        # Validate required fields
        required_fields = ['strategy_type', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
                
        strategy_type = data['strategy_type']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # Parse parameters if provided
        initial_balance = float(data.get('initial_balance', 10000))
        strategy_params = data.get('parameters', {})
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False, 
                'error': 'Invalid date format. Please use YYYY-MM-DD'
            }), 400
            
        # Ensure end date is not in the future
        if end_date > datetime.now():
            end_date = datetime.now()
            
        # Get historical data for the specified period
        historical_data = get_historical_klines(start_date=start_date, end_date=end_date)
        
        if not historical_data or len(historical_data) < 10:
            return jsonify({
                'success': False, 
                'error': 'Insufficient historical data for the specified period'
            }), 400
        
        # Create the strategy instance
        if strategy_type not in STRATEGY_REGISTRY:
            return jsonify({
                'success': False, 
                'error': f'Unknown strategy type: {strategy_type}'
            }), 400
        
        strategy_class = STRATEGY_REGISTRY[strategy_type]
        
        try:
            strategy = strategy_class(
                name=f"{strategy_type} backtest",
                initial_balance=initial_balance,
                **strategy_params
            )
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return jsonify({
                'success': False, 
                'error': f'Error creating strategy: {str(e)}'
            }), 400
            
        # Run the backtest
        try:
            backtester = Backtester(strategy)
            backtest_result = backtester.run_backtest(historical_data)
            
            # Return response with backtest results
            return jsonify({
                'success': True,
                'backtest_result': backtest_result,
                'strategy_type': strategy_type,
                'parameters': strategy_params,
                'data_points': len(historical_data),
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
            })
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return jsonify({
                'success': False, 
                'error': f'Error running backtest: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing backtest request: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@trading.route('/compare_strategies', methods=['POST'])
def compare_strategies():
    """Compare multiple trading strategies or configurations on the same data"""
    try:
        # Get request data
        data = request.form or request.json
        
        # Validate required fields
        required_fields = ['start_date', 'end_date', 'strategies']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
                
        start_date = data['start_date']
        end_date = data['end_date']
        strategies_configs = data['strategies']  # List of strategy configs
        
        if not isinstance(strategies_configs, list) or len(strategies_configs) < 1:
            return jsonify({
                'success': False, 
                'error': 'Strategies must be a list with at least one strategy configuration'
            }), 400
            
        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False, 
                'error': 'Invalid date format. Please use YYYY-MM-DD'
            }), 400
            
        # Ensure end date is not in the future
        if end_date > datetime.now():
            end_date = datetime.now()
            
        # Get historical data once for all strategies
        historical_data = get_historical_klines(start_date=start_date, end_date=end_date)
        
        if not historical_data or len(historical_data) < 10:
            return jsonify({
                'success': False, 
                'error': 'Insufficient historical data for the specified period'
            }), 400
            
        # Run backtests for each strategy
        results = []
        
        for idx, strategy_config in enumerate(strategies_configs):
            strategy_type = strategy_config.get('type')
            strategy_name = strategy_config.get('name', f"Strategy {idx+1}")
            strategy_params = strategy_config.get('parameters', {})
            initial_balance = float(strategy_config.get('initial_balance', 10000))
            
            if not strategy_type or strategy_type not in STRATEGY_REGISTRY:
                results.append({
                    'success': False,
                    'strategy_name': strategy_name,
                    'error': f'Unknown strategy type: {strategy_type}'
                })
                continue
                
            try:
                # Create strategy instance
                strategy_class = STRATEGY_REGISTRY[strategy_type]
                strategy = strategy_class(
                    name=strategy_name,
                    initial_balance=initial_balance,
                    **strategy_params
                )
                
                # Run backtest
                backtester = Backtester(strategy)
                backtest_result = backtester.run_backtest(historical_data)
                
                # Add result
                results.append({
                    'success': True,
                    'strategy_name': strategy_name,
                    'strategy_type': strategy_type,
                    'parameters': strategy_params,
                    'backtest_result': backtest_result
                })
                
            except Exception as e:
                logger.error(f"Error backtesting strategy {strategy_name}: {e}")
                results.append({
                    'success': False,
                    'strategy_name': strategy_name,
                    'error': str(e)
                })
        
        # Return combined results
        return jsonify({
            'success': True,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'data_points': len(historical_data),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

def get_historical_klines(start_date=None, end_date=None, symbol="BTCUSDT", interval="15m"):
    """Get historical kline data from Binance API"""
    import requests
    import pandas as pd
    
    try:
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
            
        # Convert to milliseconds timestamp
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        # Determine appropriate interval based on date range
        days_diff = (end_date - start_date).days
        if days_diff > 30:
            interval = "1d"  # Daily for longer ranges
        elif days_diff > 7:
            interval = "4h"  # 4-hour for medium ranges
        
        url = "https://api.binance.com/api/v3/klines"
        all_klines = []
        current_start = start_ts
        
        while current_start < end_ts:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_ts,
                'limit': 1000  # Max limit per request
            }
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get klines: {response.status_code}")
                break
                
            klines = response.json()
            
            if not klines:
                break
                
            all_klines.extend(klines)
            
            # Update start for next batch
            current_start = klines[-1][0] + 1
        
        if not all_klines:
            logger.warning("No kline data retrieved")
            return None
            
        # Convert to DataFrame
        columns = ['time', 'open', 'high', 'low', 'close', 'volume', 
                  'close_time', 'quote_asset_volume', 'number_of_trades',
                  'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
                  
        df = pd.DataFrame(all_klines, columns=columns)
        
        # Convert data types
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_columns] = df[numeric_columns].astype(float)
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching historical klines: {e}")
        return None

@trading.route('/api/models/available')
def get_available_models():
    """Get available models for trading"""
    try:
        from app.models import ModelHistory
        
        # Get all models with their performance metrics
        models = ModelHistory.query.all()
        
        available_models = []
        for model in models:
            available_models.append({
                'id': model.id,
                'type': model.model_type,
                'r2': model.r2,
                'mae': model.mae,
                'rmse': model.rmse,
                'is_active': model.is_active,
                'timestamp': model.timestamp.isoformat() if model.timestamp else None,
                'epochs': model.epochs,
                'performance_summary': f"R²: {model.r2:.3f}, MAE: {model.mae:.2f}" if model.r2 and model.mae else "No metrics available"
            })
        
        # Sort by R² score (best first)
        available_models.sort(key=lambda x: x['r2'] or 0, reverse=True)
        
        return jsonify({
            'success': True,
            'models': available_models,
            'count': len(available_models)
        })
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trading.route('/api/trading/set-model', methods=['POST'])
def set_trading_model():
    """Set the model to use for trading signals"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        model_type = data.get('model_type')
        
        if not model_id or not model_type:
            return jsonify({
                'success': False,
                'error': 'Model ID and type are required'
            }), 400
        
        # Store the selected model in session or a trading configuration
        session['trading_model_id'] = model_id
        session['trading_model_type'] = model_type
        
        # Validate that the model exists
        from app.models import ModelHistory
        model = ModelHistory.query.get(model_id)
        
        if not model:
            return jsonify({
                'success': False,
                'error': 'Selected model not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': f'{model_type.upper()} model set for trading',
            'model': {
                'id': model.id,
                'type': model.model_type,
                'accuracy': model.r2,
                'mae': model.mae
            }
        })
        
    except Exception as e:
        logger.error(f"Error setting trading model: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trading.route('/api/trading/signals')
def get_trading_signals():
    """Get current trading signals based on selected model and strategy"""
    try:
        strategy = request.args.get('strategy', 'bollinger_macd')
        model_id = request.args.get('model_id') or session.get('trading_model_id')
        risk_level = request.args.get('risk_level', 'moderate')
        
        signals = []
        metrics = {}
        
        if model_id:
            # Get model predictions
            from app.models import ModelHistory
            model = ModelHistory.query.get(model_id)
            
            if model:
                # Generate signals based on model predictions
                signals = generate_model_based_signals(model, strategy, risk_level)
                metrics = {
                    'model_accuracy': model.r2,
                    'avgConfidence': calculate_signal_confidence(signals),
                    'last_update': datetime.now().isoformat()
                }
        
        # If no model signals, fall back to technical analysis
        if not signals:
            signals = generate_technical_signals(strategy, risk_level)
            metrics = {
                'avgConfidence': 0.5,  # Lower confidence for technical signals
                'last_update': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'signals': signals,
            'metrics': metrics,
            'strategy': strategy,
            'model_id': model_id
        })
        
    except Exception as e:
        logger.error(f"Error getting trading signals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_model_based_signals(model, strategy, risk_level):
    """Generate trading signals based on ML model predictions"""
    try:
        # Get recent price data
        from app.utils.bitcoin_api import get_bitcoin_price_history
        price_data = get_bitcoin_price_history(days=7)
        
        if not price_data or not price_data.get('prices'):
            return []
        
        current_price = price_data['prices'][-1]
        
        # Simple signal generation based on model type and accuracy
        confidence = model.r2 if model.r2 else 0.5
        
        # Determine signal based on model performance and strategy
        if model.model_type.lower() in ['lstm', 'gru', 'transformer']:
            # Time series models - look for trend
            recent_prices = price_data['prices'][-5:]
            if len(recent_prices) >= 2:
                trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if trend > 0.02:  # 2% upward trend
                    action = 'BUY'
                elif trend < -0.02:  # 2% downward trend
                    action = 'SELL'
                else:
                    action = 'HOLD'
            else:
                action = 'HOLD'
        else:
            # Other models - use different logic
            action = 'HOLD'
        
        # Adjust confidence based on risk level
        risk_multiplier = {'conservative': 0.8, 'moderate': 1.0, 'aggressive': 1.2}
        adjusted_confidence = min(1.0, confidence * risk_multiplier.get(risk_level, 1.0))
        
        return [{
            'action': action,
            'price': current_price,
            'confidence': adjusted_confidence,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'model_type': model.model_type,
            'strategy': strategy
        }]
        
    except Exception as e:
        logger.error(f"Error generating model-based signals: {str(e)}")
        return []

def generate_technical_signals(strategy, risk_level):
    """Generate signals based on technical analysis"""
    try:
        from app.utils.bitcoin_api import get_bitcoin_price_history
        price_data = get_bitcoin_price_history(days=7)
        
        if not price_data or not price_data.get('prices'):
            return []
        
        current_price = price_data['prices'][-1]
        
        # Simple moving average crossover
        if len(price_data['prices']) >= 5:
            short_ma = sum(price_data['prices'][-3:]) / 3
            long_ma = sum(price_data['prices'][-5:]) / 5
            
            if short_ma > long_ma:
                action = 'BUY'
            elif short_ma < long_ma:
                action = 'SELL'
            else:
                action = 'HOLD'
        else:
            action = 'HOLD'
        
        return [{
            'action': action,
            'price': current_price,
            'confidence': 0.5,  # Lower confidence for technical signals
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'strategy': strategy
        }]
        
    except Exception as e:
        logger.error(f"Error generating technical signals: {str(e)}")
        return []

def calculate_signal_confidence(signals):
    """Calculate average confidence of signals"""
    if not signals:
        return 0
    
    total_confidence = sum(signal.get('confidence', 0) for signal in signals)
    return total_confidence / len(signals)

@trading.route('/api/trading/chart-data')
def get_chart_data():
    """Get chart data with trading signals"""
    try:
        from app.utils.bitcoin_api import get_bitcoin_price_history
        price_data = get_bitcoin_price_history(days=1)  # Last 24 hours
        
        if not price_data:
            return jsonify({
                'success': False,
                'error': 'No price data available'
            })
        
        # Generate sample trading signals for visualization
        buy_signals = []
        sell_signals = []
        
        # Add some sample signals (you can replace with real signal logic)
        prices = price_data.get('prices', [])
        dates = price_data.get('dates', [])
        
        for i in range(0, len(prices), 6):  # Every 6th data point
            if i < len(prices) and i < len(dates):
                if i % 12 == 0:  # Buy signal
                    buy_signals.append({
                        'x': dates[i],
                        'y': prices[i]
                    })
                elif i % 12 == 6:  # Sell signal
                    sell_signals.append({
                        'x': dates[i],
                        'y': prices[i]
                    })
        
        return jsonify({
            'success': True,
            'data': {
                'timestamps': dates,
                'prices': prices,
                'buySignals': buy_signals,
                'sellSignals': sell_signals
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trading.route('/api/trading/backtest', methods=['POST'])
def run_trading_backtest():
    """Run a backtest with selected model and strategy"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        strategy = data.get('strategy', 'bollinger_macd')
        risk_level = data.get('risk_level', 'moderate')
        position_size = float(data.get('position_size', 25)) / 100
        
        if not model_id:
            return jsonify({
                'success': False,
                'error': 'Model ID is required'
            }), 400
        
        # Get the model
        from app.models import ModelHistory
        model = ModelHistory.query.get(model_id)
        
        if not model:
            return jsonify({
                'success': False,
                'error': 'Model not found'
            }), 404
        
        # Run backtest simulation
        results = simulate_backtest(model, strategy, risk_level, position_size)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def simulate_backtest(model, strategy, risk_level, position_size):
    """Simulate a trading backtest"""
    try:
        # Get historical data for backtesting
        from app.utils.bitcoin_api import get_bitcoin_price_history
        price_data = get_bitcoin_price_history(days=30)
        
        if not price_data or not price_data.get('prices'):
            raise ValueError("No price data available for backtesting")
        
        prices = price_data['prices']
        
        # Simple backtest simulation
        initial_balance = 10000
        balance = initial_balance
        btc_held = 0
        trades = []
        wins = 0
        losses = 0
        
        # Risk parameters based on risk level
        risk_params = {
            'conservative': {'stop_loss': 0.02, 'take_profit': 0.03},
            'moderate': {'stop_loss': 0.03, 'take_profit': 0.05},
            'aggressive': {'stop_loss': 0.05, 'take_profit': 0.08}
        }
        
        stop_loss = risk_params[risk_level]['stop_loss']
        take_profit = risk_params[risk_level]['take_profit']
        
        # Simulate trading based on simple moving average strategy
        for i in range(5, len(prices)):
            current_price = prices[i]
            
            # Simple signal: buy when short MA > long MA
            short_ma = sum(prices[i-3:i]) / 3
            long_ma = sum(prices[i-5:i]) / 5
            
            # Apply model confidence as a filter
            model_confidence = model.r2 if model.r2 else 0.5
            signal_threshold = 0.3 + (0.4 * model_confidence)  # Higher confidence = lower threshold
            
            if btc_held == 0 and short_ma > long_ma * (1 + signal_threshold * 0.01):
                # Buy signal
                btc_to_buy = (balance * position_size) / current_price
                btc_held = btc_to_buy
                balance -= btc_to_buy * current_price
                
                trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'amount': btc_to_buy,
                    'timestamp': i
                })
                
            elif btc_held > 0:
                # Check for sell conditions
                entry_price = trades[-1]['price'] if trades else current_price
                price_change = (current_price - entry_price) / entry_price
                
                should_sell = False
                
                if price_change >= take_profit:
                    # Take profit
                    should_sell = True
                    wins += 1
                elif price_change <= -stop_loss:
                    # Stop loss
                    should_sell = True
                    losses += 1
                elif short_ma < long_ma * (1 - signal_threshold * 0.01):
                    # Sell signal
                    should_sell = True
                    if price_change > 0:
                        wins += 1
                    else:
                        losses += 1
                
                if should_sell:
                    balance += btc_held * current_price
                    
                    trades.append({
                        'type': 'SELL',
                        'price': current_price,
                        'amount': btc_held,
                        'timestamp': i
                    })
                    
                    btc_held = 0
        
        # If we still hold BTC at the end, sell it
        if btc_held > 0:
            balance += btc_held * prices[-1]
            if prices[-1] > trades[-1]['price']:
                wins += 1
            else:
                losses += 1
        
        # Calculate results
        total_return = ((balance - initial_balance) / initial_balance) * 100
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate max drawdown (simplified)
        max_drawdown = 0
        peak = initial_balance
        for trade in trades:
            if trade['type'] == 'SELL':
                current_value = balance
                if current_value > peak:
                    peak = current_value
                drawdown = ((peak - current_value) / peak) * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': losses,
            'final_balance': balance,
            'summary': f"Strategy returned {total_return:.2f}% over 30 days with {win_rate:.1f}% win rate using {model.model_type.upper()} model."
        }
        
    except Exception as e:
        logger.error(f"Error in backtest simulation: {str(e)}")
        return {
            'total_return': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'summary': f"Backtest failed: {str(e)}"
        }